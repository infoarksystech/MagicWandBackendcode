from sqlalchemy.orm import Session
from app.models.models import Gallery, GalleryKeyword
from app.schemas.gallery import GalleryKeywordCreate, GalleryKeywordUpdate


def get_gallery(db: Session, gallery_id: int):
    return db.query(Gallery).filter(Gallery.id == gallery_id).first()

def get_all_galleries(db: Session):
    return db.query(Gallery).order_by(Gallery.id.desc()).all()

def update_gallery_key(db: Session, gallery_id: int, new_key: str):
    gallery = db.query(Gallery).filter(Gallery.id == gallery_id).first()
    if not gallery:
        return None
    gallery.key = new_key
    db.commit()
    db.refresh(gallery)
    return gallery

def create_keyword(db: Session, keyword_data: GalleryKeywordCreate):
    keyword = GalleryKeyword(**keyword_data.dict())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword

def get_keywords(db: Session):
    return db.query(GalleryKeyword).all()

def get_keyword_by_id(db: Session, keyword_id: int):
    return db.query(GalleryKeyword).filter(GalleryKeyword.id == keyword_id).first()

def update_keyword(db: Session, keyword_id: int, data: GalleryKeywordUpdate):
    keyword = db.query(GalleryKeyword).filter(GalleryKeyword.id == keyword_id).first()
    if not keyword:
        return None
    for field, value in data.dict(exclude_unset=True).items():
        setattr(keyword, field, value)
    db.commit()
    db.refresh(keyword)
    return keyword

def delete_keyword(db: Session, keyword_id: int):
    keyword = db.query(GalleryKeyword).filter(GalleryKeyword.id == keyword_id).first()
    if not keyword:
        return None
    db.delete(keyword)
    db.commit()
    return keyword    


def delete_gallery(db: Session, id: int):
    gallery = db.query(Gallery).filter(Gallery.id == id).first()
    if gallery:
        db.delete(gallery)
        db.commit()    