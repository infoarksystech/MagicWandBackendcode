import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from app.db.database import get_db
from app.models.models import Category
from app.routers.products import UPLOAD_DIR
from app.services.categories import CategoryService
from sqlalchemy.orm import Session
from app.schemas.categories import CategoryCreate, CategoryOut, CategoriesOut, CategoryOutDelete, CategoryUpdate
from app.core.security import check_admin_role
from app.utils.responses import ResponseHandler
from typing import Dict, Any


router = APIRouter(tags=["Categories"], prefix="/categories")

def get_all_child_categories(category: Category) -> List[Category]:
    """
    Recursively collect all child categories of a category.
    """
    children = []
    for child in category.children:
        children.append(child)
        children.extend(get_all_child_categories(child))
    return children

@router.get("/{parent_category_id}/all-products", response_model=Dict[str, Any])
def get_all_products_under_category(
    parent_category_id: int,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    per_page: int = Query(20, gt=0, le=100, description="Number of items per page")
):
    """
    Get all products under a parent category and all its child categories in a single array with pagination.
    """
    parent_category = db.query(Category).filter(Category.id == parent_category_id).first()
    if not parent_category:
        raise HTTPException(status_code=404, detail=f"Category with id {parent_category_id} not found")
    
    # Get parent + all child categories
    all_categories = [parent_category] + get_all_child_categories(parent_category)
    
    # Use a set to avoid duplicate products
    all_products_set = set()
    for cat in all_categories:
        for product in cat.products:
            all_products_set.add(product)
    
    # Convert set to list and apply pagination
    all_products_list = list(all_products_set)
    total_items = len(all_products_list)
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    paginated_products = all_products_list[start_index:end_index]
    
    # Format response
    products_data = []
    for product in paginated_products:
        products_data.append({
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "discount_percentage": product.discount_percentage,
            "stock": product.stock,
            "brand": product.brand,
            "thumbnail": product.thumbnail,
            "images": product.images,
            "is_published": product.is_published,
            "categories": [{"id": c.id, "name": c.name} for c in product.categories]
        })

    return {
        "page": page,
        "per_page": per_page,
        "total_items": total_items,
        "total_pages": (total_items + per_page - 1) // per_page,
        "products": products_data
    }

@router.get(
    "/tree/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Fetch hierarchical category tree"
)
def get_category_tree(db: Session = Depends(get_db)):
    """
    Fetches all categories in a **tree structure**, including parent-child relationships.
    """
    category_tree = CategoryService.get_all_categories(db, page=1, limit=1000)  # Large limit to fetch all
    return ResponseHandler.success("Category tree fetched successfully", category_tree)


# Get All Categories with Pagination & Search
@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=CategoriesOut  # Ensure it supports hierarchical data
)
def get_all_categories(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query("", description="Search based on category name"),
):
    return CategoryService.get_all_categories(db, page, limit, search)


# Get Category By ID
@router.get(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryOut  # Ensure it includes child categories
)
def get_category(category_id: int, db: Session = Depends(get_db)):
    return CategoryService.get_category(db, category_id)



@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin_role)]
)
def create_category(
    name: str,
    parent_id: Optional[int] = None,
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """Calls the CategoryService to create a category."""
    return CategoryService.create_category(db, name, parent_id, image)

# Update Existing Category
@router.put(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryOut,
    dependencies=[Depends(check_admin_role)]
)
def update_category(
    category_id: int,
    name: Optional[str] = None,
    parent_id: Optional[int] = None,
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Handle file upload
    if image:
        file_path = f"{UPLOAD_DIR}/{category_id}_{image.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        db_category.image_url = file_path  # Update image URL

    # Update other fields
    if name:
        db_category.name = name
    if parent_id is not None:
        db_category.parent_id = parent_id

    db.commit()
    db.refresh(db_category)

    return {"message": "Category updated successfully", "data": db_category}


# Delete Category By ID
@router.delete(
    "/{category_id}",
    status_code=status.HTTP_200_OK,
    response_model=CategoryOutDelete,
    dependencies=[Depends(check_admin_role)])
def delete_category(category_id: int, db: Session = Depends(get_db)):
    return CategoryService.delete_category(db, category_id)
