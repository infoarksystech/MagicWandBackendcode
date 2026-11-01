from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.db.database import get_db
from app.models.models import OTPStore, User
from app.services.users import AddressService, UserService
from sqlalchemy.orm import Session
from app.schemas.users import AddressCreate, AddressResponse, AddressUpdate, ChangePasswordRequest, ResetPasswordRequest, UserCreate, UserOut, UsersOut, UserOutDelete, UserUpdate, VerifyOTPRequest
from app.core.security import check_admin_role, get_current_user, get_password_hash, verify_password
from app.schemas.users import ForgotPasswordRequest, ForgotPasswordResponse
from app.utils.email import send_otp_email
import random


router = APIRouter(tags=["Users"], prefix="/users")


# Get All Users
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=UsersOut,
    dependencies=[Depends(check_admin_role)])
def get_all_users(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query("", description="Search based username"),
    role: str = Query("user", enum=["user", "admin"])
):
    return UserService.get_all_users(db, page, limit, search, role)


# Get User By ID
@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserOut,
    dependencies=[Depends(check_admin_role)])
def get_user(user_id: int, db: Session = Depends(get_db)):
    return UserService.get_user(db, user_id)


# Create New User
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=UserOut,
    dependencies=[Depends(check_admin_role)])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return UserService.create_user(db, user)


# Update Existing User
@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserOut,
    dependencies=[Depends(check_admin_role)])
def update_user(user_id: int, updated_user: UserUpdate, db: Session = Depends(get_db)):
    return UserService.update_user(db, user_id, updated_user)


# Delete User By ID
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserOutDelete,
    dependencies=[Depends(check_admin_role)])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return UserService.delete_user(db, user_id)


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):

    user = UserService.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )

    # Generate a 4-digit OTP
    otp = str(random.randint(1000, 9999))  # Generates a 4-digit OTP

    # Save OTP in the database (or cache like Redis)
    UserService.store_otp(db, user.id, otp)

    # Send OTP to user's email
    send_otp_email(user.email, otp)

    return {"status": "success", "otp": otp}  # OTP should not be returned in production


@router.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    
    user = UserService.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = db.query(OTPStore).filter(OTPStore.user_id == user.id).first()

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP not found")

    if stored_otp.otp != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.utcnow() > stored_otp.expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")

    return {"status": "success", "message": "OTP verified successfully"}

@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = UserService.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stored_otp = db.query(OTPStore).filter(
        OTPStore.user_id == user.id,
        OTPStore.otp == request.otp
    ).first()

    if not stored_otp:
        raise HTTPException(status_code=400, detail="OTP not found")

    if datetime.utcnow() > stored_otp.expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Hash the new password and update
    hashed_password = get_password_hash(request.new_password)
    user.password = hashed_password
    db.commit()

    # Delete OTP after successful password reset
    db.delete(stored_otp)
    db.commit()

    return {"status": "success", "message": "Password reset successfully"}

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # current_user is a dictionary from the token payload
):
    # Get the User object using the user ID from the token
    user = db.query(User).filter(User.id == current_user["id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify the old password
    if not verify_password(request.old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect",
        )

    # Check if new password and confirm password match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match",
        )

    # Hash the new password and update the user record
    user.password = get_password_hash(request.new_password)
    db.commit()

    return {"status": "success", "message": "Password changed successfully"}


@router.post("/add-address")
def add_address(
    address: AddressCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Add a new address for the logged-in user.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_address = AddressService.add_address(db, user_id, address)
    return {"status": "success", "address": new_address}

@router.put("/update-address/{address_id}", response_model=AddressResponse)
def update_address(
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update an existing address. Only the owner can update.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    updated_address = AddressService.update_address(db, user_id, address_id, address)
    if not updated_address:
        raise HTTPException(status_code=404, detail="Address not found or unauthorized")

    return updated_address


@router.post("/get-addresses", response_model=List[AddressResponse])
def get_addresses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # Ensure it allows all users
):
    """
    Get all addresses for the logged-in user.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    addresses = AddressService.get_addresses_by_user(db, user_id)
    return addresses



@router.delete("/delete-address/{address_id}")
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a specific address by its ID for the logged-in user.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")

    success = AddressService.delete_address(db, user_id, address_id)
    if not success:
        raise HTTPException(status_code=404, detail="Address not found or unauthorized")

    return {"status": "success", "message": "Address deleted successfully"}


@router.get("/admin/get-addresses/{user_id}", response_model=List[AddressResponse], dependencies=[Depends(check_admin_role)])
def get_user_addresses_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Admin: Get all addresses of a specific user by user_id.
    """
    addresses = AddressService.get_addresses_by_user(db, user_id)
    if not addresses:
        raise HTTPException(status_code=404, detail="No addresses found for this user")
    return addresses

@router.put(
    "/admin/update-address/{user_id}/{address_id}",
    response_model=AddressResponse,
    dependencies=[Depends(check_admin_role)],
)
def admin_update_user_address(
    user_id: int,
    address_id: int,
    address: AddressUpdate,
    db: Session = Depends(get_db),
):
    """
    Admin: Update a specific address of a user by user_id and address_id.
    """
    updated_address = AddressService.update_address(db, user_id, address_id, address)

    if not updated_address:
        raise HTTPException(
            status_code=404,
            detail="Address not found or user not authorized",
        )

    return updated_address

