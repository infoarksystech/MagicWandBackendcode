from pydantic import BaseModel
from typing import List, Optional


# ✅ Create Wishlist
class WishlistCreate(BaseModel):
    name: str


# ✅ Add Product to Wishlist (Supports Variants)
class WishlistItemAdd(BaseModel):
    product_id: int
    variant_id: Optional[int] = None  # ✅ New: Allows selecting a product variant
