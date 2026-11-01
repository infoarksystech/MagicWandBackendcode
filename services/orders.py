from sqlalchemy.orm import Session
from app.models.models import Order, OrderItem
from app.schemas.orders import OrderCreate, OrderItemResponse, OrderResponse
from app.utils.responses import ResponseHandler

class OrderService:
    # ✅ Create Order (Without Cart)
    @staticmethod
    def create_order(user_data: dict, db: Session, order_data: OrderCreate):
        user_id = user_data["id"]

        # ✅ Create Order
        order = Order(
            user_id=user_id,
            project_id=order_data.project_id,
            gallery_id=order_data.gallery_id,
            total_amount=order_data.total_amount,
            payment_status=order_data.payment_status,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # ✅ Create Order Items
        order_items = []
        for item in order_data.order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                subtotal=item.subtotal
            )
            order_items.append(order_item)

        db.add_all(order_items)
        db.commit()

        # ✅ Convert to Pydantic model before returning
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            project_id=order.project_id,
            gallery_id=order.gallery_id,
            total_amount=order.total_amount,
            payment_status=order.payment_status,
            created_at=order.created_at,
            order_items=[
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    subtotal=item.subtotal
                ) for item in order_items
            ]
        )

    # ✅ Get Order by ID
    @staticmethod
    def get_order(user_data: dict, db: Session, order_id: int):
        user_id = user_data["id"]
        
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order:
            return ResponseHandler.not_found_error("Order", order_id)

        # ✅ Convert SQLAlchemy Model to Pydantic Model
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            project_id=order.project_id,
            gallery_id=order.gallery_id,
            total_amount=order.total_amount,
            payment_status=order.payment_status,
            created_at=order.created_at,
            order_items=[
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    subtotal=item.subtotal
                ) for item in order.order_items
            ]
        )

    # ✅ Get All Orders for a User
    @staticmethod
    def get_all_orders(user_data: dict, db: Session):
        user_id = user_data["id"]
        orders = db.query(Order).filter(Order.user_id == user_id).all()

        return [
            OrderResponse(
                id=order.id,
                user_id=order.user_id,
                project_id=order.project_id,
                gallery_id=order.gallery_id,  # ✅ Add this line
                total_amount=order.total_amount,
                payment_status=order.payment_status,
                created_at=order.created_at,
                order_items=[
                    OrderItemResponse(
                        id=item.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        subtotal=item.subtotal
                    ) for item in order.order_items
                ]
            ) for order in orders
        ]
