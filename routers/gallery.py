from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
from fastapi import File, UploadFile, Form
import uuid
from app.db.database import get_db
from app.models.models import Gallery
from app.schemas.gallery import GalleryKeywordCreate, GalleryKeywordResponse, GalleryKeywordUpdate, GalleryResponse, GalleryUpdate
from app.services.gallery import create_keyword, delete_gallery, delete_keyword, get_gallery, get_all_galleries, get_keyword_by_id, get_keywords, update_gallery_key, update_keyword
from app.core.security import check_admin_role

router = APIRouter(prefix="/gallery", tags=["Gallery"])


@router.post("/create_gallery_keywords", response_model=GalleryKeywordResponse, dependencies=[Depends(check_admin_role)])
def create_gallery_keyword(keyword_data: GalleryKeywordCreate, db: Session = Depends(get_db)):
    return create_keyword(db, keyword_data)

@router.get("/get_gallery_keywords", response_model=list[GalleryKeywordResponse])
def get_all_gallery_keywords(db: Session = Depends(get_db)):
    return get_keywords(db)

@router.get("/get_gallery_keywords/{id}", response_model=GalleryKeywordResponse)
def get_gallery_keyword_by_id(id: int, db: Session = Depends(get_db)):
    keyword = get_keyword_by_id(db, id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.put("/update_gallery_keywords/{id}", response_model=GalleryKeywordResponse, dependencies=[Depends(check_admin_role)])
def update_gallery_keyword(id: int, data: GalleryKeywordUpdate, db: Session = Depends(get_db)):
    updated = update_keyword(db, id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return updated

@router.delete("/delete_gallery_keywords/{id}", response_model=GalleryKeywordResponse, dependencies=[Depends(check_admin_role)])
def delete_gallery_keyword(id: int, db: Session = Depends(get_db)):
    deleted = delete_keyword(db, id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return deleted


@router.get("/", response_model=list[GalleryResponse])
def get_all_galleries_api(db: Session = Depends(get_db)):
    return get_all_galleries(db)

@router.get("/{id}", response_model=GalleryResponse)
def get_gallery_by_id(id: int, db: Session = Depends(get_db)):
    gallery = get_gallery(db, id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return gallery


@router.delete("/{id}", status_code=200)
def delete_gallery_api(id: int, db: Session = Depends(get_db)):
    gallery = get_gallery(db, id)
    if not gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    
    delete_gallery(db, id)
    db.commit()    
    return {"message": "Gallery deleted successfully", "id": id} 

@router.put("/{id}/key", response_model=GalleryResponse,dependencies=[Depends(check_admin_role)])
def update_gallery_key_by_id(id: int, key_data: GalleryUpdate, db: Session = Depends(get_db)):
    updated_gallery = update_gallery_key(db, id, key_data.key)
    if not updated_gallery:
        raise HTTPException(status_code=404, detail="Gallery not found")
    return updated_gallery

UPLOAD_DIR = "assets/gallery"  # adjust this path as needed
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post(
    "/",
    response_model=List[GalleryResponse],
    dependencies=[Depends(check_admin_role)]
)
def upload_gallery_images(
    key: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    saved_images = []

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    for file in files:
        # Validate filename
        if not file.filename:
            continue

        # Generate unique filename
        file_ext = file.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        # Save file
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        image_url = f"/{file_path.replace(os.sep, '/')}"
        original_img_url = image_url

        new_gallery = Gallery(
            key=key,
            image_url=image_url,
            original_img_url=original_img_url
        )

        db.add(new_gallery)
        saved_images.append(new_gallery)

    db.commit()

    # Refresh all objects
    for img in saved_images:
        db.refresh(img)

    return saved_images


