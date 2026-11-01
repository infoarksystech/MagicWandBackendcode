import os
import shutil
from PIL import Image
import uuid
from fastapi import UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import Product, Category, Variant
from datetime import datetime
from app.schemas.categories import CategoryBase
from app.schemas.products import (
    ProductBase, ProductCreate, ProductUpdate, ProductsOut,
    VariantBase, VariantCreate, VariantUpdate
)
from app.utils.responses import ResponseHandler


UPLOAD_DIR = "assets/products"  # Define the upload directory

class ProductService:
    @staticmethod
    def create_product(
        db: Session,
        product_data: dict,
        images: Optional[List[UploadFile]] = None,
        thumbnail: Optional[UploadFile] = None
    ):
        """Create a product and upload images (including a separate thumbnail)."""

        # Ensure the upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)  # ✅ Create directory if it doesn't exist

        # Validate category IDs
        if "category_ids" not in product_data or not product_data["category_ids"]:
            return ResponseHandler.bad_request("Category IDs are required.")

        category_ids = product_data["category_ids"]
        categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
        if not categories or len(categories) != len(category_ids):
            return ResponseHandler.not_found_error("One or more categories", category_ids)

        # Create product object
        product_dict = {key: product_data[key] for key in product_data if key != "category_ids"}
        db_product = Product(**product_dict, categories=categories)
        db.add(db_product)
        db.commit()
        db.refresh(db_product)

        # Upload thumbnail
        if thumbnail:
            thumbnail_path = os.path.join(UPLOAD_DIR, f"{db_product.id}_thumbnail_{thumbnail.filename}").replace("\\", "/")
            with open(thumbnail_path, "wb") as buffer:
                shutil.copyfileobj(thumbnail.file, buffer)
            db_product.thumbnail = thumbnail_path  # ✅ Save thumbnail path

        # Upload images
        uploaded_image_paths = []
        if images:
            for image in images:
                file_path = os.path.join(UPLOAD_DIR, f"{db_product.id}_{image.filename}").replace("\\", "/")
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                uploaded_image_paths.append(file_path)

            # Save images in the database
            db_product.images = uploaded_image_paths

        db.commit()
        db.refresh(db_product)

        return ResponseHandler.create_success(db_product.title, db_product.id, db_product)

    @staticmethod
    def get_all_products(db: Session, page: int = 1, limit: int = 10, search: str = None):
        query = db.query(Product)

        # Apply search filter if search keyword is provided
        if search:
            query = query.filter(Product.title.ilike(f"%{search}%"))

        # Apply pagination
        products = query.offset((page - 1) * limit).limit(limit).all()

        if not products:
            return ResponseHandler.not_found_error("Products", "all")

        return {
            "status": "success",
            "message": "Products retrieved successfully",
            "data": [
                {
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "discount_percentage": product.discount_percentage,
                    "rating": product.rating,
                    "stock": product.stock,
                    "brand": product.brand,
                    "thumbnail": product.thumbnail,
                    "images": product.images,
                    "is_published": product.is_published,
                    "created_at": product.created_at.isoformat() if isinstance(product.created_at, datetime) else product.created_at,
                    "categories": [{"id": cat.id, "name": cat.name} for cat in product.categories],
                    "product_metadata": [
                        {"id": meta.id, "meta_key": meta.meta_key, "meta_value": meta.meta_value}
                        for meta in (product.product_metadata or [])
                    ]
                }
                for product in products
            ]
        }



    @staticmethod
    def get_product(db: Session, product_id: int):
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return ResponseHandler.not_found_error("Product", product_id)

        product_metadata_list = [
            {"id": meta.id,"meta_key": meta.meta_key, "meta_value": meta.meta_value}
            for meta in (product.product_metadata or [])
        ]

        return ResponseHandler.get_single_success(product.title, product_id, {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "discount_percentage": product.discount_percentage,
            "rating": product.rating,
            "stock": product.stock,
            "brand": product.brand,
            "thumbnail": product.thumbnail,
            "images": product.images,
            "is_published": product.is_published,
            "created_at": product.created_at.isoformat() if isinstance(product.created_at, datetime) else product.created_at,
            "categories": [{"id": cat.id, "name": cat.name} for cat in product.categories],
            "product_metadata": product_metadata_list if product_metadata_list else []
        })


    @staticmethod
    def update_product(
        db: Session,
        product_id: int,
        updated_product: dict,
        images: Optional[List[UploadFile]] = None,
        thumbnail: Optional[UploadFile] = None
    ):
        """Update an existing product including optional image and thumbnail uploads."""

        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return ResponseHandler.not_found_error("Product", product_id)

        # ✅ Update product details except category_ids
        for key, value in updated_product.items():
            if key != "category_ids":
                setattr(db_product, key, value)

        # ✅ Update categories if provided
        if "category_ids" in updated_product and updated_product["category_ids"]:
            category_ids = updated_product["category_ids"]
            categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
            if not categories or len(categories) != len(category_ids):
                return ResponseHandler.not_found_error("One or more categories", category_ids)
            db_product.categories = categories

        # ✅ Handle Thumbnail Update
        if thumbnail:
            thumbnail_path = os.path.join(UPLOAD_DIR, f"{db_product.id}_thumbnail_{thumbnail.filename}").replace("\\", "/")
            
            # Remove old thumbnail if exists
            if db_product.thumbnail and os.path.exists(db_product.thumbnail):
                os.remove(db_product.thumbnail)

            # Save new thumbnail
            with open(thumbnail_path, "wb") as buffer:
                shutil.copyfileobj(thumbnail.file, buffer)
            db_product.thumbnail = thumbnail_path

        # ✅ Handle Image Updates
        if images:
            new_image_paths = []
            for image in images:
                image_path = os.path.join(UPLOAD_DIR, f"{db_product.id}_{image.filename}").replace("\\", "/")
                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                new_image_paths.append(image_path)

            # Remove old images if they exist
            if db_product.images:
                for old_image in db_product.images:
                    if os.path.exists(old_image):
                        os.remove(old_image)

            db_product.images = new_image_paths

        db.commit()
        db.refresh(db_product)

        return ResponseHandler.update_success(db_product.title, db_product.id, db_product)

    @staticmethod
    def delete_product(db: Session, product_id: int):
        """Delete a product by its ID safely."""
        
        db_product = db.query(Product).filter(Product.id == product_id).first()
        if not db_product:
            return ResponseHandler.not_found_error("Product", product_id)

        # Delete associated images and thumbnail if they exist
        if db_product.thumbnail:
            try:
                os.remove(db_product.thumbnail)
            except FileNotFoundError:
                pass  # Ignore missing file

        if db_product.images:
            for image_path in db_product.images:
                try:
                    os.remove(image_path)
                except FileNotFoundError:
                    pass  # Ignore missing files

        db.delete(db_product)
        db.commit()

        # Return a dictionary instead of a model instance
        return {"message": f"Product '{db_product.title}' (ID: {db_product.id}) deleted successfully.","data": {"id": db_product.id, "title": db_product.title}}
        
    @staticmethod
    def get_products_by_category(db: Session, category_id: int, page: int, limit: int):
        offset = (page - 1) * limit
        products = (
            db.query(Product)
            .join(Product.categories)
            .filter(Category.id == category_id)
            .offset(offset)
            .limit(limit)
            .all()
        )

        total = db.query(Product).join(Product.categories).filter(Category.id == category_id).count()

        product_list = [
            ProductBase.model_validate(
                {
                    "id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "price": product.price,
                    "discount_percentage": product.discount_percentage,
                    "rating": product.rating,
                    "stock": product.stock,
                    "brand": product.brand,
                    "thumbnail": product.thumbnail,
                    "images": product.images,
                    "is_published": product.is_published,
                    "created_at": product.created_at,
                    "categories": [{"id": cat.id, "name": cat.name} for cat in product.categories],
                    # "variants": [
                    #     {
                    #         "id": var.id, "name": var.name, "price": var.price,
                    #         "stock": var.stock, "product_id": var.product_id,
                    #         "images": var.images  # ✅ Added variant images
                    #     } for var in product.variants
                    # ] if product.variants else []

                "product_metadata": [
                        {"id": meta.id, "meta_key": meta.meta_key, "meta_value": meta.meta_value}
                        for meta in (product.product_metadata or [])
                    ]
                }
            )
            for product in products
        ]

        return ProductsOut(
            message="Products fetched successfully",
            data={"total": total, "products": product_list}
        )

    # VARIANT MANAGEMENT

    @staticmethod
    def get_product_variants(db: Session, product_id: int):
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            ResponseHandler.not_found_error("Product", product_id)

        return ResponseHandler.get_single_success(
            f"Variants for {product.title}",
            product_id,
            product.variants
        )

    @staticmethod
    def add_variant(db: Session, product_id: int, variant_data):
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            ResponseHandler.not_found_error("Product", product_id)

        # ✅ Ensure product_id is included before converting to Pydantic model
        if isinstance(variant_data, dict):
            variant_data["product_id"] = product_id  # 🔥 Fix: Add missing product_id
            variant_data = VariantCreate(**variant_data)  # Now it won't raise an error

        db_variant = Variant(**variant_data.model_dump())  # ✅ Now it works fine
        db.add(db_variant)
        db.commit()
        db.refresh(db_variant)

        return ResponseHandler.create_success(db_variant.name, db_variant.id, db_variant)

    @staticmethod
    def update_variant(db: Session, product_id: int, variant_id: int, updated_variant: VariantUpdate):
        variant = db.query(Variant).filter(Variant.id == variant_id, Variant.product_id == product_id).first()
        if not variant:
            ResponseHandler.not_found_error("Variant", variant_id)

        for key, value in updated_variant.dict(exclude_unset=True).items():
            setattr(variant, key, value)

        db.commit()
        db.refresh(variant)
        return ResponseHandler.update_success(variant.name, variant.id, variant)

    @staticmethod
    def delete_variant(db: Session, product_id: int, variant_id: int):
        variant = db.query(Variant).filter(Variant.id == variant_id, Variant.product_id == product_id).first()
        if not variant:
            ResponseHandler.not_found_error("Variant", variant_id)

        db.delete(variant)
        db.commit()
        return ResponseHandler.delete_success(variant.name, variant.id, variant)
