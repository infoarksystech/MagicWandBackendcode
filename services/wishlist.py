from sqlalchemy.orm import Session, joinedload
from app.models.models import Wishlist, WishlistItem, Product, Variant
from app.schemas.wishlist import WishlistCreate, WishlistItemAdd
from app.utils.responses import ResponseHandler
from app.core.security import get_current_user


class WishlistService:

    # ✅ Create Wishlist
    @staticmethod
    def create_wishlist(user_data: dict, db: Session, wishlist_data: WishlistCreate):
        user_id = user_data.get("id")  # Extract user_id properly

        wishlist = Wishlist(name=wishlist_data.name, user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)

        return ResponseHandler.create_success("Wishlist", wishlist.id, wishlist)

    # ✅ Get All Wishlists for User
    @staticmethod
    def get_all_wishlists(user_data: dict, db: Session, page: int, limit: int):
        user_id = user_data.get("id")
        
        wishlists = db.query(Wishlist).filter(Wishlist.user_id == user_id).offset((page - 1) * limit).limit(limit).all()
        
        return ResponseHandler.success(f"Page {page} with {limit} wishlists", wishlists)

    # ✅ Get Wishlist by ID (Now Includes Variant Data)
    @staticmethod
    def get_wishlist(user_data: dict, db: Session, wishlist_id: int):
        user_id = user_data.get("id")
        
        wishlist = (
            db.query(Wishlist)
            .filter(Wishlist.id == wishlist_id, Wishlist.user_id == user_id)
            .options(joinedload(Wishlist.items).joinedload(WishlistItem.product).joinedload(Product.variants))  # Load variants
            .first()
        )

        if not wishlist:
            return ResponseHandler.not_found_error("Wishlist", wishlist_id)

        wishlist_data = {
            "id": wishlist.id,
            "name": wishlist.name,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "product_name": item.product.title,
                    "variant_id": item.variant_id,  # ✅ Include Variant ID
                    "variant_name": item.variant.value if item.variant else None,  # ✅ Show Variant Name
                    "product_price": item.variant.price if item.variant else item.product.price,  # ✅ Use Variant Price
                }
                for item in wishlist.items
            ],
        }

        return ResponseHandler.get_single_success("Wishlist", wishlist.id, wishlist_data)

    # ✅ Add Product (with Variant) to Wishlist
    @staticmethod
    def add_product_to_wishlist(user_data: dict, db: Session, wishlist_id: int, item_data: WishlistItemAdd):
        user_id = user_data.get("id")
        
        wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).first()
        if not wishlist:
            return ResponseHandler.not_found_error("Wishlist", wishlist_id)

        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            return ResponseHandler.not_found_error("Product", item_data.product_id)

        variant = None
        if item_data.variant_id:
            variant = db.query(Variant).filter(Variant.id == item_data.variant_id, Variant.product_id == item_data.product_id).first()
            if not variant:
                return ResponseHandler.not_found_error("Variant", item_data.variant_id)

        existing_item = db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist_id,
            WishlistItem.product_id == item_data.product_id,
            WishlistItem.variant_id == item_data.variant_id
        ).first()
        if existing_item:
            return ResponseHandler.conflict_error("Product variant already exists in wishlist")

        wishlist_item = WishlistItem(wishlist_id=wishlist_id, product_id=item_data.product_id, variant_id=item_data.variant_id)
        db.add(wishlist_item)
        db.commit()
        db.refresh(wishlist_item)

        return ResponseHandler.create_success("Wishlist Item", wishlist_item.id, wishlist_item)

    # ✅ Remove Product (with Variant) from Wishlist
    @staticmethod
    def remove_product_from_wishlist(user_data: dict, db: Session, wishlist_id: int, product_id: int, variant_id: int = None):
        user_id = user_data.get("id")
        
        wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).first()
        if not wishlist:
            return ResponseHandler.not_found_error("Wishlist", wishlist_id)

        wishlist_item_query = db.query(WishlistItem).filter(
            WishlistItem.wishlist_id == wishlist_id, 
            WishlistItem.product_id == product_id
        )
        
        if variant_id:
            wishlist_item_query = wishlist_item_query.filter(WishlistItem.variant_id == variant_id)

        wishlist_item = wishlist_item_query.first()
        if not wishlist_item:
            return ResponseHandler.not_found_error("Wishlist Item", product_id)

        db.delete(wishlist_item)
        db.commit()

        return ResponseHandler.delete_success("Wishlist Item", product_id, wishlist_item)

    # ✅ Delete Wishlist
    @staticmethod
    def delete_wishlist(user_data: dict, db: Session, wishlist_id: int):
        user_id = user_data.get("id")
        
        wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id, Wishlist.user_id == user_id).first()
        if not wishlist:
            return ResponseHandler.not_found_error("Wishlist", wishlist_id)

        db.query(WishlistItem).filter(WishlistItem.wishlist_id == wishlist_id).delete()
        db.delete(wishlist)
        db.commit()

        return ResponseHandler.delete_success("Wishlist", wishlist_id, wishlist)
