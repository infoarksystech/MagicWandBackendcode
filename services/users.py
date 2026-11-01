from sqlalchemy.orm import Session
from app.models.models import Address, User
from app.schemas.users import UserCreate, UserUpdate
from app.utils.responses import ResponseHandler
from app.core.security import get_password_hash
from app.models.models import User, OTPStore
from datetime import datetime, timedelta



class UserService:
    @staticmethod
    def get_all_users(db: Session, page: int, limit: int, search: str = "", role: str = "user"):
        users = db.query(User).order_by(User.id.asc()).filter(
            User.username.contains(search), User.role == role).limit(limit).offset((page - 1) * limit).all()
        return {"message": f"Page {page} with {limit} users", "data": users}

    @staticmethod
    def get_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            ResponseHandler.not_found_error("User", user_id)
        return ResponseHandler.get_single_success(user.username, user_id, user)

    @staticmethod
    def create_user(db: Session, user: UserCreate):
        hashed_password = get_password_hash(user.password)
        user.password = hashed_password
        db_user = User(id=None, **user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return ResponseHandler.create_success(db_user.username, db_user.id, db_user)

    @staticmethod
    def update_user(db: Session, user_id: int, updated_user: UserUpdate):
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            ResponseHandler.not_found_error("User", user_id)

        updated_data = updated_user.model_dump()

        # Check if password is provided, if not, remove it from the update data
        if "password" in updated_data and not updated_data["password"]:
            del updated_data["password"]

        for key, value in updated_data.items():
            setattr(db_user, key, value)

        db.commit()
        db.refresh(db_user)
        return ResponseHandler.update_success(db_user.username, db_user.id, db_user)

    @staticmethod
    def delete_user(db: Session, user_id: int):
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            ResponseHandler.not_found_error("User", user_id)
        db.delete(db_user)
        db.commit()
        return ResponseHandler.delete_success(db_user.username, db_user.id, db_user)


    @staticmethod
    def get_user_by_email(db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def store_otp(db: Session, user_id: int, otp: str):
        """
        Store OTP in the database for verification with expiry.
        """
        expires_at = datetime.utcnow() + timedelta(minutes=20)  # OTP expires in 10 minutes

        # Check if OTP already exists for user
        existing_otp = db.query(OTPStore).filter(OTPStore.user_id == user_id).first()
        if existing_otp:
            existing_otp.otp = otp
            existing_otp.expires_at = expires_at
        else:
            db_otp = OTPStore(user_id=user_id, otp=otp, expires_at=expires_at)
            db.add(db_otp)

        db.commit()

class AddressService:
    @staticmethod
    def add_address(db: Session, user_id: int, address_data):
        new_address = Address(
            user_id=user_id,
            street=address_data.street,
            city=address_data.city,
            state=address_data.state,
            country=address_data.country,
            postal_code=address_data.postal_code,
            address_type=address_data.address_type,
            address_name=address_data.address_name
        )
        db.add(new_address)
        db.commit()
        db.refresh(new_address)
        return new_address
    

    @staticmethod
    def update_address(db: Session, user_id: int, address_id: int, address_data):
        address = db.query(Address).filter(
            Address.id == address_id, Address.user_id == user_id
        ).first()
        if not address:
            return None  # Ensures users can only update their own addresses

        # Update fields
        address.street = address_data.street
        address.city = address_data.city
        address.state = address_data.state
        address.country = address_data.country
        address.postal_code = address_data.postal_code
        address.address_type=address_data.address_type,
        address.address_name=address_data.address_name

        db.commit()
        db.refresh(address)
        return address

    @staticmethod
    def get_addresses_by_user(db: Session, user_id: int):
        return db.query(Address).filter(Address.user_id == user_id).all()


    @staticmethod
    def delete_address(db: Session, user_id: int, address_id: int):
        address = db.query(Address).filter(
            Address.id == address_id, Address.user_id == user_id
        ).first()
        if not address:
            return None  # Ensures users can only delete their own addresses

        db.delete(address)
        db.commit()
        return True   