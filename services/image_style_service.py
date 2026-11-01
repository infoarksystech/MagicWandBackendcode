from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import ImageStyle
from typing import  Optional

def create_image_style(db: Session, style_name: str, file_path: str,slno:str,style_category:str, endpoint: str, ref_keywords:str, is_ai: bool = None,is_display: bool = None,ui_parameters: str = "[]"):
    new_style = ImageStyle(
        slno=slno,
        style_category=style_category,
        style_name=style_name,
        url=file_path,
        endpoint=endpoint,
        ref_keywords=ref_keywords,  # ✅ pass it here
        is_ai=is_ai,
        is_display=is_display
    )
    db.add(new_style)
    db.commit()
    db.refresh(new_style)
    return new_style

def get_image_style(db: Session, style_id: int):
    return db.query(ImageStyle).filter(ImageStyle.id == style_id).first()

def get_filtered_image_styles(db: Session, search: Optional[str] = None):
    query = db.query(ImageStyle)

    if search:
        search = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ImageStyle.slno.ilike(search),
                ImageStyle.style_category.ilike(search),
                ImageStyle.style_name.ilike(search),
                ImageStyle.url.ilike(search),
                ImageStyle.ref_keywords.ilike(search)
            )
        )

    return query.all()

def update_image_style(db: Session, style_id: int, style_name: str,slno:str,style_category:str, url: str, endpoint: str,ref_keywords:str, is_ai: bool,is_display: bool,ui_parameters: str = "[]"):
    style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if style:
        style.slno=slno
        style.style_category=style_category
        style.style_name = style_name
        style.url = url
        style.endpoint = endpoint
        style.ref_keywords=ref_keywords  # ✅ pass it here
        style.is_ai = is_ai
        is_display=is_display
        db.commit()
        db.refresh(style)
    return style

def delete_image_style(db: Session, style_id: int):
    style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if style:
        db.delete(style)
        db.commit()
    return style
