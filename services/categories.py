import os
import shutil
from typing import Optional
from fastapi import UploadFile
from sqlalchemy.orm import Session, joinedload
from app.models.models import Category, product_categories, Product
from app.schemas.categories import CategoryCreate, CategoryOut, CategoryUpdate
from app.utils.responses import ResponseHandler


UPLOAD_DIR = "assets/categories"

class CategoryService:
    @staticmethod
    def get_all_categories(db: Session, page: int, limit: int, search: str = ""):
        categories = (
            db.query(Category)
            .order_by(Category.id.asc())
            .filter(Category.name.contains(search))
            .options(joinedload(Category.products))
            .limit(limit)
            .offset((page - 1) * limit)
            .all()
        )
        
        total = db.query(Category).count()
        
        # Store categories in a dictionary to prevent duplicates
        category_dict = {}
        
        for category in categories:
            if category.id not in category_dict:
                category_dict[category.id] = {
                    "id": category.id,
                    "name": category.name,
                    "parent_id": category.parent_id,
                    "product_ids": [product.id for product in category.products],
                    "children": [],
                    "image_url": category.image_url
                }

        # Build tree structure
        for category in category_dict.values():
            if category["parent_id"]:
                parent = category_dict.get(category["parent_id"])
                if parent:
                    if category not in parent["children"]:  # Prevent duplicates
                        parent["children"].append(category)

        # Extract only top-level categories
        root_categories = [cat for cat in category_dict.values() if cat["parent_id"] is None]

        return {
        "message": f"Page {page} with {limit} categories",
        "total": total,
        "data": root_categories
    }

    @staticmethod
    def get_category(db: Session, category_id: int):
        category = (
            db.query(Category)
            .filter(Category.id == category_id)
            .options(joinedload(Category.products))  # Load associated products
            .first()
        )

        if not category:
            return ResponseHandler.not_found_error("Category", category_id)

        # Fetch child categories
        child_categories = db.query(Category).filter(Category.parent_id == category_id).all()

        product_ids = [product.id for product in category.products]

        category_data = {
            "id": category.id,
            "name": category.name,
            "product_ids": product_ids,
            "image_url": category.image_url,
            "children": [
                {
                    "id": child.id,
                    "name": child.name,
                    "product_ids": [p.id for p in child.products],
                    "image_url": child.image_url,
                }
                for child in child_categories
            ],  # Append child categories
        }

        return ResponseHandler.get_single_success(category.name, category.id, category_data)
    


    UPLOAD_DIR = "assets/categories"
    @staticmethod
    def create_category(db: Session, name: str, parent_id: Optional[int] = None, image: Optional[UploadFile] = None):
        """Handles category creation, including file uploads."""

        # Ensure the upload directory exists
        # os.makedirs(UPLOAD_DIR, exist_ok=True)
         # Ensure root categories use NULL instead of 0
        parent_id = None if parent_id in [0, "0", ""] else parent_id

        image_url = None
        if image:
            # Normalize the file path and replace backslashes with forward slashes
            file_path = os.path.normpath(os.path.join(UPLOAD_DIR, f"{parent_id or 'root'}_{image.filename}")).replace("\\", "/")

            # Save the uploaded file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            image_url = file_path  # Store formatted file path

        # Create the new category
        new_category = Category(name=name, parent_id=parent_id, image_url=image_url)
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        return ResponseHandler.success("Category created successfully", new_category)

    @staticmethod
    def update_category(db: Session, category_id: int, updated_category: CategoryUpdate):
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return ResponseHandler.not_found_error("Category", category_id)
        
        updated_fields = updated_category.model_dump()
        for key, value in updated_fields.items():
            setattr(db_category, key, value)
        
        db.commit()
        db.refresh(db_category)
        
        return ResponseHandler.update_success(db_category.name, db_category.id, db_category)

    @staticmethod
    def get_category_tree(db: Session, parent_id: int = None):
        categories = db.query(Category).filter(Category.parent_id == parent_id).all()

        category_tree = [
            {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id,
                "image_url": category.image_url,
                "children": CategoryService.get_category_tree(db, category.id),
            }
            for category in categories
        ]

        return category_tree

    @staticmethod
    def delete_category(db: Session, category_id: int):
        db_category = db.query(Category).filter(Category.id == category_id).first()
        if not db_category:
            return ResponseHandler.not_found_error("Category", category_id)
        
        has_products = db.query(product_categories).filter(product_categories.c.category_id == category_id).first()
        if has_products:
            return ResponseHandler.conflict_error("Category cannot be deleted as it has associated products", category_id)
        
        db.delete(db_category)
        db.commit()
        return ResponseHandler.delete_success(db_category.name, db_category.id, db_category)