from pydantic import BaseModel , EmailStr, constr
from typing import List
from datetime import datetime
from app.schemas.carts import CartBase
from typing import Optional

class BaseConfig:
    from_attributes = True


class UserBase(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone:str
    full_name: str
    password: str
    role: str
    is_active: bool
    created_at: datetime
    carts: List[CartBase]

    class Config(BaseConfig):
        pass


class UserCreate(BaseModel):
    full_name: str
    username: str
    phone:str
    email: str
    password: str

    class Config(BaseConfig):
        pass


class UserUpdate(UserCreate):
    pass


class UserOut(BaseModel):
    message: str
    data: UserBase

    class Config(BaseConfig):
        pass


class UsersOut(BaseModel):
    message: str
    data: List[UserBase]

    class Config(BaseConfig):
        pass


class UserOutDelete(BaseModel):
    message: str
    data: UserBase

    class Config(BaseConfig):
        pass

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    status: str
    otp: str  # Remove this in production

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: constr(min_length=6) # type: ignore
    confirm_password: constr(min_length=6)  # type: ignore

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str      

class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    address_type: str
    address_name: str
    
class AddressUpdate(BaseModel):
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    address_type: str
    address_name: str

class AddressResponse(BaseModel):
    id: int
    user_id: int
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    address_type: str
    address_name: str
    address_type: str
    address_name: Optional[str] = None
    class Config:
        from_attributes = True             

class AddressOut(BaseModel):
    id: int
    user_id: int
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    address_type: str
    address_name: Optional[str] = None