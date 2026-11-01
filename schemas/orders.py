from pydantic import BaseModel
from typing import List
from datetime import datetime

# ✅ Order Item Request (For Order Creation)
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    subtotal: float  # ✅ Send subtotal directly

# ✅ Order Creation Request (No Cart, Uses Direct Product Details)
class OrderCreate(BaseModel):
    project_id: int
    gallery_id: int
    total_amount: float
    payment_status: str  # ✅ Accept payment status (pending, paid, etc.)
    order_items: List[OrderItemCreate]

# ✅ Order Item Response (Without Variants)
class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True

        
class OrderResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    gallery_id: int
    total_amount: float
    payment_status: str
    created_at: datetime
    order_items: List[OrderItemResponse]

    class Config:
        from_attributes = True
