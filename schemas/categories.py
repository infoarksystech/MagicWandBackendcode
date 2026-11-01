from typing import List, Optional
from pydantic import BaseModel


class CategoryBase(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    product_ids: List[int] = []
    children: List["CategoryBase"] = []
    image_url: Optional[str] = None  # Add image field

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True  # Required for SQLAlchemy serialization

class CategoryCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None  # Allows creating subcategories

class CategoryUpdate(BaseModel):
    name: str
    parent_id: Optional[int] = None  # Allows updating parent-child relationship

class CategoryOut(BaseModel):
    message: str
    data: CategoryBase  # Single category response

class CategoriesOut(BaseModel):
    message: str
    data: List[CategoryBase]  # Multiple categories response

class CategoryDelete(BaseModel):
    id: int
    name: str

class CategoryOutDelete(BaseModel):
    message: str
    data: CategoryDelete
