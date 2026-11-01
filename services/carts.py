from sqlalchemy.orm import Session, joinedload
from app.models.models import Cart, CartItem, Product, Variant
from app.schemas.carts import CartUpdate, CartCreate
from app.utils.responses import ResponseHandler
from app.core.security import get_current_user


class CartService:
    # Get All Carts
    @staticmethod
    def get_all_carts(token, db: Session, page: int, limit: int):
        user = get_current_user(token)  
        user_id = user.get("id")
        carts = (
            db.query(Cart)
            .filter(Cart.user_id == user_id)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return ResponseHandler.success(f"Page {page} with {limit} carts", carts)

    # Get A Cart By ID
    @staticmethod
    def get_cart(token, db: Session, cart_id: int):
        user = get_current_user(token)  
        user_id = user.get("id")
        cart = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user_id).first()
        if not cart:
            return ResponseHandler.not_found_error("Cart", cart_id)
        return ResponseHandler.get_single_success("cart", cart_id, cart)

    # Create or Update a Cart
    @staticmethod
    def create_cart(token, db: Session, cart: CartCreate):
        user = get_current_user(token)
        user_id = user.get("id")

        if not user_id:
            return ResponseHandler.unauthorized_error("Invalid user token")

        cart_db = db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart_db:
            cart_db = Cart(user_id=user_id, total_amount=0)
            db.add(cart_db)
            db.commit()
            db.refresh(cart_db)

        total_amount = 0

        for item_data in cart.cart_items:
            product_id = item_data.product_id
            variant_id = item_data.variant_id  # ✅ Handle variant selection
            quantity = item_data.quantity

            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return ResponseHandler.not_found_error("Product", product_id)

            price = product.price
            if variant_id:
                variant = db.query(Variant).filter(Variant.id == variant_id, Variant.product_id == product_id).first()
                if not variant:
                    return ResponseHandler.not_found_error("Variant", variant_id)
                price = variant.price  # ✅ Use variant price if available

            subtotal = quantity * price * (1 - product.discount_percentage / 100)

            cart_item = db.query(CartItem).filter(
                CartItem.cart_id == cart_db.id,
                CartItem.product_id == product_id,
                CartItem.variant_id == variant_id  # ✅ Ensure variant match
            ).first()

            if cart_item:
                cart_item.quantity += quantity
                cart_item.subtotal = cart_item.quantity * price * (1 - product.discount_percentage / 100)
                db.refresh(cart_item)  # ✅ Fix potential stale data
            else:
                cart_item = CartItem(cart_id=cart_db.id, product_id=product_id, variant_id=variant_id, quantity=quantity, subtotal=subtotal)
                db.add(cart_item)

            total_amount += cart_item.subtotal

        cart_db.total_amount = total_amount
        db.commit()
        db.refresh(cart_db)

        return ResponseHandler.create_success("Cart", cart_db.id, cart_db)

    # Update Cart & CartItem
    @staticmethod
    def update_cart(token, db: Session, cart_id: int, updated_cart: CartUpdate):
        user = get_current_user(token)
        user_id = user.get("id")

        cart = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user_id).first()
        if not cart:
            return ResponseHandler.not_found_error("Cart", cart_id)

        existing_cart_items = db.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        existing_items_map = {(item.product_id, item.variant_id): item for item in existing_cart_items}

        total_amount = 0

        for item in updated_cart.cart_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                return ResponseHandler.not_found_error("Product", item.product_id)

            price = product.price
            if item.variant_id:
                variant = db.query(Variant).filter(Variant.id == item.variant_id, Variant.product_id == item.product_id).first()
                if not variant:
                    return ResponseHandler.not_found_error("Variant", item.variant_id)
                price = variant.price

            subtotal = item.quantity * price * (1 - product.discount_percentage / 100)

            key = (item.product_id, item.variant_id)
            if key in existing_items_map:
                cart_item = existing_items_map[key]
                if item.quantity == 0:
                    db.delete(cart_item)
                else:
                    cart_item.quantity = item.quantity
                    cart_item.subtotal = subtotal
                    db.refresh(cart_item)  # ✅ Ensure fresh data
            else:
                if item.quantity > 0:
                    new_cart_item = CartItem(
                        cart_id=cart_id,
                        product_id=item.product_id,
                        variant_id=item.variant_id,
                        quantity=item.quantity,
                        subtotal=subtotal
                    )
                    db.add(new_cart_item)

            total_amount += subtotal if item.quantity > 0 else 0

        db.commit()

        # ✅ If no items remain, delete the cart
        remaining_items = db.query(CartItem).filter(CartItem.cart_id == cart_id).count()
        if remaining_items == 0:
            db.delete(cart)
            db.commit()
            return ResponseHandler.success("Cart deleted successfully.")

        cart.total_amount = total_amount
        db.commit()
        db.refresh(cart)

        return ResponseHandler.update_success("cart", cart.id, cart)

    # Delete Cart & CartItems
    @staticmethod
    def delete_cart(token, db: Session, cart_id: int):
        user = get_current_user(token)
        user_id = user.get("id")

        cart = (
            db.query(Cart)
            .options(joinedload(Cart.cart_items).joinedload(CartItem.product))
            .filter(Cart.id == cart_id, Cart.user_id == user_id)
            .first()
        )
        if not cart:
            return ResponseHandler.not_found_error("Cart", cart_id)

        # ✅ Properly delete cart items before deleting the cart
        for cart_item in cart.cart_items:
            db.delete(cart_item)

        db.delete(cart)
        db.commit()

        return ResponseHandler.delete_success("Cart", cart_id, cart)
