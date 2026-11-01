from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.products import ProductBase, CategoryBase


# ✅ Product Model for Cart (Fix: Make category optional instead of excluding it)
class ProductBaseCart(ProductBase):
    category: Optional[CategoryBase] = None  # ✅ Fix: Allows missing category

    model_config = ConfigDict(from_attributes=True)  # ✅ Ensure ORM compatibility


# ✅ Cart Item (Supports Variants)
class CartItemBase(BaseModel):
    id: int
    product_id: int
    quantity: int
    subtotal: float
    product: ProductBaseCart  # ✅ Product details
    

    model_config = ConfigDict(from_attributes=True)  # ✅ ORM Mode Fix


# ✅ Cart Base Model
class CartBase(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    total_amount: float
    cart_items: List[CartItemBase]  # ✅ Fix: Ensure this is properly serialized

    model_config = ConfigDict(from_attributes=True)  # ✅ Ensure SQLAlchemy compatibility


# ✅ Response Model for Getting a Cart
class CartOut(BaseModel):
    message: str
    data: CartBase

    model_config = ConfigDict(from_attributes=True)  # ✅ Fix serialization issue


# ✅ List Response for Multiple Carts
class CartsOutList(BaseModel):
    message: str
    data: List[CartBase]

    model_config = ConfigDict(from_attributes=True)  # ✅ Fix serialization issue


class CartsUserOutList(BaseModel):
    message: str
    data: List[CartBase]

    model_config = ConfigDict(from_attributes=True)  # ✅ Fix serialization issue


# ✅ Delete Cart Response
class CartOutDelete(BaseModel):
    message: str
    data: CartBase

    model_config = ConfigDict(from_attributes=True)  # ✅ Fix serialization issue


# ✅ Creating a Cart Item (Includes Variants)
class CartItemCreate(BaseModel):
    product_id: int
    quantity: int


# ✅ Creating a Cart
class CartCreate(BaseModel):
    cart_items: List[CartItemCreate]

    model_config = ConfigDict(from_attributes=True)  # ✅ Fix serialization issue


# ✅ Updating Cart (Reuses CartCreate Structure)
class CartUpdate(CartCreate):
    pass
