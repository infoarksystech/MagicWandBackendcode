from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.security import check_admin_role
from app.db.database import get_db
from app.models.models import Tag, Product
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.schemas.products import ProductBase

router = APIRouter(prefix="/tags", tags=["Tags"])

# Create a tag
@router.post("/", response_model=TagResponse,dependencies=[Depends(check_admin_role)])
def create_tag(tag: TagCreate, db: Session = Depends(get_db)):
    db_tag = Tag(name=tag.name)
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

# Get all tags
@router.get("/", response_model=List[TagResponse])
def get_all_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()

# Get tag by ID
@router.get("/{tag_id}", response_model=TagResponse)
def get_tag_by_id(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

# Update a tag
@router.put("/{tag_id}", response_model=TagResponse,dependencies=[Depends(check_admin_role)])
def update_tag(tag_id: int, tag: TagUpdate, db: Session = Depends(get_db)):
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db_tag.name = tag.name
    db.commit()
    db.refresh(db_tag)
    return db_tag

# Delete a tag
@router.delete("/{tag_id}",dependencies=[Depends(check_admin_role)])
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    db_tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(db_tag)
    db.commit()
    return {"detail": "Tag deleted"}

# Assign multiple tags to a product
@router.post("/assign-to-product/{product_id}",dependencies=[Depends(check_admin_role)])
def assign_tags_to_product(product_id: int, tag_ids: List[int], db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    if not tags:
        raise HTTPException(status_code=404, detail="No valid tags found")

    product.tags = tags
    db.commit()
    return {"detail": "Tags assigned to product"}

# Unassign a single tag from a product
@router.post("/unassign-from-product/{product_id}/{tag_id}",dependencies=[Depends(check_admin_role)])
def unassign_tag_from_product(product_id: int, tag_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag in product.tags:
        product.tags.remove(tag)
        db.commit()
        return {"detail": f"Tag ID {tag_id} removed from product ID {product_id}"}
    else:
        raise HTTPException(status_code=400, detail="Tag is not assigned to the product")

# Get all products by tag
@router.get("/{tag_id}/products", response_model=List[ProductBase])
def get_products_by_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    return tag.products

# Get all tags assigned to a product
@router.get("/product/{product_id}/tags", response_model=List[TagResponse],dependencies=[Depends(check_admin_role)])
def get_tags_by_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.tags

