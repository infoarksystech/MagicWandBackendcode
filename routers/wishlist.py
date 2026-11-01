from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.wishlist import WishlistService
from app.schemas.wishlist import WishlistCreate, WishlistItemAdd
from app.core.security import get_current_user
from app.db.database import get_db

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


# ✅ Create a Wishlist
@router.post("/")
def create_wishlist(
    wishlist_data: WishlistCreate, 
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return WishlistService.create_wishlist(user_data, db, wishlist_data)


# ✅ Get All Wishlists
@router.get("/")
def get_all_wishlists(
    page: int = 1, limit: int = 10, 
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return WishlistService.get_all_wishlists(user_data, db, page, limit)


# ✅ Get Wishlist by ID
@router.get("/{wishlist_id}")
def get_wishlist(
    wishlist_id: int, 
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return WishlistService.get_wishlist(user_data, db, wishlist_id)


# ✅ Add Product/Variant to Wishlist
@router.post("/{wishlist_id}/add")
def add_product_to_wishlist(
    wishlist_id: int, 
    item_data: WishlistItemAdd, 
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Adds a product to the wishlist. If `variant_id` is provided, the variant will be added instead.
    """
    return WishlistService.add_product_to_wishlist(user_data, db, wishlist_id, item_data)


# ✅ Remove Product/Variant from Wishlist
@router.delete("/{wishlist_id}/remove/{product_id}")
def remove_product_from_wishlist(
    wishlist_id: int, 
    product_id: int, 
    variant_id: int = None,  # ✅ Optional variant removal
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Removes a product (or specific variant) from the wishlist.
    """
    return WishlistService.remove_product_from_wishlist(user_data, db, wishlist_id, product_id, variant_id)


# ✅ Delete Wishlist
@router.delete("/{wishlist_id}")
def delete_wishlist(
    wishlist_id: int, 
    user_data: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    return WishlistService.delete_wishlist(user_data, db, wishlist_id)
