from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.orders import OrderService
from app.schemas.orders import OrderCreate, OrderResponse
from app.db.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])

# ✅ Create Order Without Cart
@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create an order directly using product details (without cart).
    """
    return OrderService.create_order(user_data, db, order_data)

# ✅ Get Order by ID
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve order details.
    """
    return OrderService.get_order(user_data, db, order_id)

# ✅ Get All Orders
@router.get("/", response_model=List[OrderResponse])
def get_all_orders(
    user_data: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetch all orders for the current user.
    """
    return OrderService.get_all_orders(user_data, db)
