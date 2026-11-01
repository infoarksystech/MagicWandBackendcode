import shutil
from typing import List, Optional, Union
import json
from sqlalchemy.orm.attributes import flag_modified
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from app.db.database import get_db
from app.models.models import Product, ProductMetadata,product_categories,Category
from app.services.products import ProductService
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.schemas.products import (
    ProductCreate, ProductMetadataBase, ProductOut, ProductsOut, ProductOutDelete, ProductUpdate, VariantCreate, VariantUpdate,ProductBase,ProductCategoriesUpdate
)
from app.core.security import get_current_user, check_admin_role
from app.utils.responses import ResponseHandler
from fastapi import File, UploadFile, Form, Depends, HTTPException
import shutil
import os

router = APIRouter(tags=["Products"], prefix="/products")

@router.put("/products/{product_id}/categories")
def update_product_categories(
    product_id: int,
    payload: ProductCategoriesUpdate,
    db: Session = Depends(get_db)
):
    """
    Update only the categories of a product.
    - Pass empty list to remove all categories.
    - Pass multiple category IDs to assign multiple categories.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")

    if payload.category_ids:
        # Fetch only existing categories
        categories = db.query(Category).filter(Category.id.in_(payload.category_ids)).all()
        found_ids = {c.id for c in categories}
        missing_ids = set(payload.category_ids) - found_ids
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Categories not found: {list(missing_ids)}"
            )
        # Assign categories (many-to-many)
        product.categories = categories
    else:
        # Empty list → remove all categories
        product.categories = []

    db.commit()
    db.refresh(product)

    return {
        "message": f"Categories updated for product '{product.title}'",
        "product_id": product.id,
        "categories": [{"id": c.id, "name": c.name} for c in product.categories]
    }
# Create New Product
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=ProductOut,
    dependencies=[Depends(check_admin_role)])
def create_product(
        product: ProductCreate,
        db: Session = Depends(get_db)):
    return ProductService.create_product(db, product)



UPLOAD_DIR = "assets/products/"

@router.post("/{product_id}/upload-images", dependencies=[Depends(check_admin_role)])
def upload_multiple_images(
    product_id: int,
    images: List[UploadFile] = File(...),
    is_thumbnail: bool = Form(False),
    db: Session = Depends(get_db)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    uploaded_file_paths = []

    for image in images:
        if not image.filename:
            continue

        file_path = os.path.join(
            UPLOAD_DIR,
            f"{product_id}_{uuid4().hex}_{image.filename}"
        ).replace("\\", "/")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        uploaded_file_paths.append(file_path)

    if not uploaded_file_paths:
        raise HTTPException(status_code=400, detail="No valid images uploaded")

    if is_thumbnail:
        product.thumbnail = uploaded_file_paths[0]
    else:
        existing_images = list(product.images or [])
        existing_images.extend(uploaded_file_paths)

        product.images = existing_images
        flag_modified(product, "images")  # 🔥 critical

    db.commit()
    db.refresh(product)

    return {
        "message": "Images uploaded successfully",
        "images": product.images,
        "thumbnail": product.thumbnail
    }


@router.delete("/{product_id}/delete-image", dependencies=[Depends(check_admin_role)])
def delete_product_image(
    product_id: int,
    image_path: str = Query(..., description="Path of the image to delete"),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if image_path not in product.images:
        raise HTTPException(status_code=400, detail="Image not found in product images")

    # ✅ Remove the image from the list
    product.images = [img for img in product.images if img != image_path]

    # ✅ Delete the image from the file system (optional)
    if os.path.exists(image_path):
        os.remove(image_path)

    db.commit()
    db.refresh(product)

    return {
        "message": "Image deleted successfully",
        "remaining_images": product.images
    }

    
@router.get("/search", response_model=List[ProductBase])
def search_products(
    keyword: str = Query(..., description="Keyword to search products"),
    db: Session = Depends(get_db)
):
    # Convert keyword to lowercase for case-insensitive search
    keyword = keyword.lower()

    # Search by product fields or related category name
    products = (
        db.query(Product)
        .join(product_categories, Product.id == product_categories.c.product_id)
        .join(Category, Category.id == product_categories.c.category_id)
        .filter(
            or_(
                func.lower(Product.title).like(f"%{keyword}%"),
                func.lower(Product.description).like(f"%{keyword}%"),
                func.lower(Product.brand).like(f"%{keyword}%"),
                func.lower(Category.name).like(f"%{keyword}%")
            )
        )
        .distinct()
        .all()
    )

    return products

# Get All Products
@router.get("/")
def get_all_products(
    db: Session = Depends(get_db),
    page: int = Query(1, alias="page"),
    limit: int = Query(10, alias="limit"),
    search: str = Query(None, alias="search")
):
    return ProductService.get_all_products(db, page, limit, search)


@router.post("/create-product", status_code=201,
    dependencies=[Depends(check_admin_role)])
async def create_product(
    brand: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_ids: List[int] = Form(...),
    discount_percentage: float = Form(...),
    title: str = Form(...),
    is_published: bool = Form(...),
    description: str = Form(...),
    rating: Optional[int] = Form(None),
    images: List[UploadFile] = File(None),
    thumbnail: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    """API to create a new product"""
    product_data = {
        "brand": brand,
        "price": price,
        "stock": stock,
        "category_ids": category_ids,
        "discount_percentage": discount_percentage,
        "title": title,
        "is_published": is_published,
        "description": description,
        "rating": rating
    }

    return ProductService.create_product(db, product_data, images, thumbnail)


# Get Product By ID
@router.get("/{product_id}", status_code=status.HTTP_200_OK, response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return ProductService.get_product(db, product_id)


@router.put("/{product_id}", status_code=200, response_model=ProductOut,
            dependencies=[Depends(check_admin_role)])
async def update_product(
    product_id: int,
    brand: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    category_ids: Optional[List[str]] = Form(None),
    discount_percentage: Optional[float] = Form(None),
    title: Optional[str] = Form(None),
    is_published: Optional[bool] = Form(None),
    description: Optional[str] = Form(None),
    rating: Optional[int] = Form(None),
    images: Optional[List[Union[UploadFile, str]]] = File(None),
    thumbnail: Optional[Union[UploadFile, str]] = File(None),
    db: Session = Depends(get_db)
):
    """
    Update product details.
    Ignore empty strings or None for images, thumbnail, and other fields.
    """

    # ✅ Filter only valid UploadFiles
    valid_images = [
        img for img in (images or [])
        if isinstance(img, UploadFile) and img.filename
    ]
    valid_thumbnail = thumbnail if isinstance(thumbnail, UploadFile) and getattr(thumbnail, "filename", None) else None

    # ✅ Only include fields that are NOT None
    updated_data = {
        k: v for k, v in {
            "brand": brand,
            "price": price,
            "stock": stock,
            "category_ids": category_ids,
            "discount_percentage": discount_percentage,
            "title": title,
            "is_published": is_published,
            "description": description,
            "rating": rating
        }.items() if v is not None
    }

    return ProductService.update_product(
        db,
        product_id,
        updated_data,
        images=valid_images,
        thumbnail=valid_thumbnail
    )

# Delete Product By ID
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductOutDelete,
    dependencies=[Depends(check_admin_role)]
)
def delete_product(
        product_id: int,
        db: Session = Depends(get_db)
):
    return ProductService.delete_product(db, product_id)

# @router.post("/{product_id}/product_metadata", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin_role)])
# def add_product_metadata(
#     product_id: int,
#     meta_key: Optional[str] = Form(None),  # meta_key is optional
#     meta_value: Optional[str] = Form(None),  
#     image: UploadFile = File(None),  # Image is optional
#     db: Session = Depends(get_db)
# ):
#     product = db.query(Product).filter(Product.id == product_id).first()
    
#     if not product:
#         raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

#     # Handle Image Upload (Only if an image is provided)
#     if image:
#         file_ext = image.filename.split(".")[-1].lower()
#         allowed_extensions = {"jpg", "jpeg", "png", "webp"}

#         if file_ext not in allowed_extensions:
#             raise HTTPException(status_code=400, detail="Invalid file type. Allowed: jpg, jpeg, png, webp")

#         # Ensure assets/metadata/ directory exists
#         upload_dir = "/home/ubuntu/FastAPI-Ecommerce-API-main/assets/metadata"
#         os.makedirs(upload_dir, exist_ok=True)

#         # Use original image name with product_id prefix
#         file_name = f"{product_id}_{image.filename}"
#         file_path = os.path.join(upload_dir, file_name)

#         # Save image
#         with open(file_path, "wb") as f:
#             f.write(image.file.read())

#         # Convert Windows paths to URL format
#         meta_value = file_path.replace("\\", "/")

#         # Fix meta_key default issue
#         if not meta_key or meta_key.lower() == "string":
#             meta_key = "base-image"  # ✅ Set default only when needed

#     # If neither meta_key nor image is provided, return an error
#     if not meta_key:
#         raise HTTPException(status_code=400, detail="Either an image or a meta_key must be provided.")

#     # Create and save metadata
#     new_product_metadata = ProductMetadata(
#         product_id=product_id,
#         meta_key=meta_key,
#         meta_value=meta_value
#     )

#     db.add(new_product_metadata)
#     db.commit()
#     db.refresh(new_product_metadata)

#     return {
#         "message": "Product metadata added successfully",
#         "product_metadata": {
#             "id": new_product_metadata.id,
#             "meta_key": new_product_metadata.meta_key,
#             "meta_value": new_product_metadata.meta_value
#         }
#     }

@router.post("/{product_id}/product_metadata", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin_role)])
def add_product_metadata(
    product_id: int,
    meta_key: Optional[str] = Form(None),
    meta_value: Optional[str] = Form(None),
    images: List[UploadFile] = File(default_factory=list),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=404,
            detail=f"Product with ID {product_id} not found"
        )

    upload_dir = "/home/ubuntu/FastAPI-Ecommerce-API-main/assets/metadata"
    os.makedirs(upload_dir, exist_ok=True)

    saved_paths = []

    # ✅ Handle image upload
    if images:
        allowed_extensions = {"jpg", "jpeg", "png", "webp"}

        for image in images:
            if not image.filename:
                continue

            ext = image.filename.rsplit(".", 1)[-1].lower()
            if ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {image.filename}. Allowed: jpg, jpeg, png, webp"
                )

            file_name = f"{product_id}_{image.filename}"
            file_path = os.path.join(upload_dir, file_name)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            saved_paths.append(file_path.replace("\\", "/"))

        meta_key = meta_key if meta_key and meta_key != "string" else "base-image"
        meta_value = json.dumps(saved_paths)

    # ❌ No valid metadata provided
    if not meta_key or not meta_value:
        raise HTTPException(
            status_code=400,
            detail="Provide either images or both meta_key and meta_value"
        )

    new_metadata = ProductMetadata(
        product_id=product_id,
        meta_key=meta_key,
        meta_value=meta_value
    )

    db.add(new_metadata)
    db.commit()
    db.refresh(new_metadata)

    return {
        "message": "Product metadata added successfully",
        "product_metadata": {
            "id": new_metadata.id,
            "meta_key": new_metadata.meta_key,
            "meta_value": new_metadata.meta_value
        }
    }

@router.put("/{product_id}/product_metadata/{metadata_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def update_product_metadata(product_id: int, metadata_id: int, product_metadata: ProductMetadataBase, db: Session = Depends(get_db)):
        metadata = db.query(ProductMetadata).filter(ProductMetadata.id == metadata_id, ProductMetadata.product_id == product_id).first()

        if not metadata:
            raise HTTPException(status_code=404, detail=f"Metadata with ID {metadata_id} not found for Product ID {product_id}")

        # Update metadata fields
        metadata.meta_key = product_metadata.meta_key
        metadata.meta_value = product_metadata.meta_value

        db.commit()
        db.refresh(metadata)

        return {
            "message": "Product metadata updated successfully",
            "product_metadata": {
                "id": metadata.id,
                "meta_key": metadata.meta_key,
                "meta_value": metadata.meta_value
            }
        }

@router.delete("/{product_id}/product_metadata/{metadata_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def delete_product_metadata(product_id: int, metadata_id: int, db: Session = Depends(get_db)):
    metadata = db.query(ProductMetadata).filter(ProductMetadata.id == metadata_id, ProductMetadata.product_id == product_id).first()

    if not metadata:
        raise HTTPException(status_code=404, detail=f"Metadata with ID {metadata_id} not found for Product ID {product_id}")

    db.delete(metadata)
    db.commit()

    return {"message": f"Product metadata with ID {metadata_id} deleted successfully"}

# Get Products by Category
@router.get("/category/{category_id}", status_code=status.HTTP_200_OK, response_model=ProductsOut)
def get_products_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
):
    return ProductService.get_products_by_category(db, category_id, page, limit)


# Get Variants of a Product
@router.get("/{product_id}/variants", status_code=status.HTTP_200_OK)
def get_product_variants(product_id: int, db: Session = Depends(get_db)):
    return ProductService.get_product_variants(db, product_id)


# Add Variant to Product
@router.post("/{product_id}/variants", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_admin_role)])
def add_variant_to_product(product_id: int, variant_data: VariantCreate, db: Session = Depends(get_db)):
    return ProductService.add_variant(db, product_id, variant_data)


# Update Variant of a Product
@router.put("/{product_id}/variants/{variant_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def update_variant(product_id: int, variant_id: int, variant_data: VariantUpdate, db: Session = Depends(get_db)):
    return ProductService.update_variant(db, product_id, variant_id, variant_data)


# Delete Variant from Product
@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_200_OK, dependencies=[Depends(check_admin_role)])
def delete_variant(product_id: int, variant_id: int, db: Session = Depends(get_db)):
    return ProductService.delete_variant(db, product_id, variant_id)


@router.get(
    "/{product_id}/product_metadata",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_admin_role)]
)
def get_product_metadata_by_product_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

    metadata_list = db.query(ProductMetadata).filter(ProductMetadata.product_id == product_id).all()

    return {
        "product_id": product_id,
        "metadata": [
            {
                "id": metadata.id,
                "meta_key": metadata.meta_key,
                "meta_value": metadata.meta_value
            } for metadata in metadata_list
        ]
    }
