from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from app.schemas.categories import CategoryBase


# ✅ Variant Schemas
class VariantBase(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    product_id: int
    value: str

    class Config:
        from_attributes = True


class VariantCreate(BaseModel):
    name: str
    price: float
    stock: int
    product_id: int
    value: str


class VariantUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    value: Optional[str] = None


class ProductMetadataBase(BaseModel):
    meta_key: str
    meta_value: str


class ProductMetadataOut(ProductMetadataBase):
    id: int
    meta_key: str
    meta_value: str
    
    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    id: int
    title: str
    description: str
    price: float
    discount_percentage: Optional[float] = None
    rating: Optional[float] = None
    stock: int
    brand: str
    thumbnail: str
    images: List[str] = []
    is_published: bool
    created_at: str
    categories: List["CategoryBase"]
    product_metadata: List[ProductMetadataOut] 

    class Config:
        from_attributes = True

    @field_validator("created_at", mode="before")
    @classmethod
    def convert_created_at(cls, value):
        """Convert datetime to ISO string format"""
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)  # Ensure it's always a string


class ProductCreate(BaseModel):
    brand: str
    price: float
    stock: int
    category_ids: List[int]
    discount_percentage: float
    title: str
    is_published: bool
    description: str
    rating: Optional[int] = None


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    discount_percentage: Optional[float] = None
    rating: Optional[float] = None
    stock: Optional[int] = None
    brand: Optional[str] = None
    thumbnail: Optional[str] = None
    images: Optional[List[str]] = None
    is_published: Optional[bool] = None
    category_ids: Optional[List[int]] = None


# ✅ Response Models
class ProductsOut(BaseModel):
    message: str
    data: dict  # Contains total count and product list


class ProductOut(BaseModel):
    message: str
    data: ProductBase

class ProductOutDelete(BaseModel):
    message: str
    data: dict  # Keep it generic to avoid validation errors

class ProductCategoriesUpdate(BaseModel):
    category_ids: List[int] 