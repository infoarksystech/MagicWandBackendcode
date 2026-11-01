import json
from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, UploadFile, File, Form
import os
from uuid import uuid4
from sqlalchemy import or_
from sqlalchemy.orm import Session,aliased
from app.db.database import SessionLocal
from app.models.models import ImageStyle, Product, ProductMetadata
from app.schemas.image_style import FieldTypeEnum, ImageStyleOut, LabelDeleteRequest, LabelEnum, UIParameter
from app.db.database import get_db
from app.services.image_style_service import (
    create_image_style,
    get_image_style,
    update_image_style,
    delete_image_style,
    get_filtered_image_styles
)

UPLOAD_DIR = "assets/styles"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/styles", tags=["Image Styles"])

def create_image_style(db: Session, style_name: str, file_path: str, endpoint: str,slno:str,style_category:str, ref_keywords:str,is_ai: bool,is_display:bool):
    # Logic to create a new ImageStyle in the database
    db_style = ImageStyle(
        slno=slno,
        style_category=style_category,
        style_name=style_name,
        url=file_path,
        endpoint=endpoint,
        ref_keywords=ref_keywords,  # ✅ pass it here
        is_ai=is_ai,
        is_display=is_display

    )
    db.add(db_style)
    db.commit()
    db.refresh(db_style)
    return db_style

def update_image_style(db: Session, style_id: int, style_name: str, file_path: str,slno:str,style_category:str, endpoint: str,ref_keywords:str, is_ai: bool,is_display:bool):
    # Logic to update an existing ImageStyle in the database
    db_style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if db_style:
        db_style.slno=slno
        db_style.style_category=style_category
        db_style.style_name = style_name
        db_style.url = file_path
        db_style.endpoint = endpoint
        db_style.ref_keywords=ref_keywords
        db_style.is_ai = is_ai
        db_style.is_display=is_display
        db.commit()
        db.refresh(db_style)
        return db_style
    return None


@router.post("/", response_model=ImageStyleOut)
def create_or_update_style(
    slno: Optional[str] = Form(None),
    style_category: Optional[str] = Form(None),
    file: UploadFile = File(None),
    style_name: str = Form(...),
    endpoint: str = Form(...),  # Single JSON string
    is_ai: bool = Form(False),
    is_display:bool=Form(False),
    style_id: Optional[str] = Form(None),  # For update
    ref_keywords: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    db_path = ""

    # Handle uploaded image file
    if file is not None:
        file_ext = file.filename.split(".")[-1]
        filename = f"{uuid4().hex}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())
        db_path = f"/{file_path.replace(os.sep, '/')}"

    # Parse and update endpoint data with db_path as 'ref_image'
    try:
        endpoint_data = json.loads(endpoint)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format in 'endpoint'"}

    # endpoint_data["ref_image"] = db_path
    endpoint_json = json.dumps(endpoint_data)

    # Update or create the image style
    if style_id:
        updated_style = update_image_style(
            db,
            slno=slno,
            style_category=style_category,
            style_id=style_id,
            style_name=style_name,
            file_path=db_path,
            endpoint=endpoint_json,
            ref_keywords=ref_keywords,
            is_ai=is_ai,
            is_display=is_display
        )
        if updated_style:
            return updated_style
        return {"error": "Image style not found for update"}
    
    return create_image_style(
        db,
        slno=slno,
        style_category=style_category,
        style_name=style_name,
        file_path=db_path,
        endpoint=endpoint_json,
        ref_keywords=ref_keywords,  # ✅ pass it here
        is_ai=is_ai,
        is_display=is_display
    )

@router.get("/{style_id}", response_model=ImageStyleOut)
def read_style(style_id: int, db: Session = Depends(get_db)):
    style = get_image_style(db, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style not found")
    return style

@router.get("/", response_model=list[ImageStyleOut])
def read_all_styles(
    search: Optional[str] = Query(default=None, description="Search keyword"),
    db: Session = Depends(get_db)
):
    return get_filtered_image_styles(db, search)

@router.delete("/{style_id}")
def delete_style(style_id: int, db: Session = Depends(get_db)):
    deleted = delete_image_style(db, style_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Style not found")
    return {"detail": "Style deleted"}

@router.post("/add-ui-parameter/{style_id}", response_model=ImageStyleOut)
def add_ui_parameter_form(
    style_id: int,
    label: Optional[LabelEnum] = Form(None),
    subject_suggestions: Optional[str] = Form(None),
    is_mandatory: Optional[bool] = Form(None),
    placeholder: Optional[str] = Form(None),
    field_type: Optional[FieldTypeEnum] = Form(None),
    db: Session = Depends(get_db)
):
    style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="Image Style not found")

    try:
        # Load existing or start new list
        existing = json.loads(style.ui_parameters or "[]")
        existing.append({
            "label": label,
            "subject_suggestions":subject_suggestions,
            "is_mandatory": is_mandatory,
            "placeholder": placeholder,
            "field_type": field_type
        })

        style.ui_parameters = json.dumps(existing)
        db.commit()
        db.refresh(style)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return style


@router.put("/update-ui-parameter/{style_id}", response_model=ImageStyleOut)
def update_ui_parameter_form(
    style_id: int,
    label: LabelEnum = Form(...),  # Required to find the field
    subject_suggestions:Optional[str] = Form(None),
    is_mandatory: Optional[bool] = Form(None),
    placeholder: Optional[str] = Form(None),
    field_type: Optional[FieldTypeEnum] = Form(None),
    db: Session = Depends(get_db)
):
    style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="Image Style not found")

    try:
        ui_list = json.loads(style.ui_parameters or "[]")
        updated = False

        for item in ui_list:
            if item.get("label") == label:
                if subject_suggestions is not None:
                    item["subject_suggestions"] = subject_suggestions
                if is_mandatory is not None:
                    item["is_mandatory"] = is_mandatory
                if placeholder is not None:
                    item["placeholder"] = placeholder
                if field_type is not None:
                    item["field_type"] = field_type
                updated = True
                break

        if not updated:
            raise HTTPException(status_code=404, detail="UI Parameter with this label not found")

        style.ui_parameters = json.dumps(ui_list)
        db.commit()
        db.refresh(style)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return style



@router.delete("/delete-ui-parameter/{style_id}", response_model=ImageStyleOut)
def delete_ui_parameter_by_label(
    style_id: int,
    payload: LabelDeleteRequest,  # ✅ JSON body expected as { "label": "..." }
    db: Session = Depends(get_db)
):
    style = db.query(ImageStyle).filter(ImageStyle.id == style_id).first()
    if not style:
        raise HTTPException(status_code=404, detail="Image Style not found")

    try:
        ui_list = json.loads(style.ui_parameters or "[]")

        print("Before deletion:", ui_list)
        new_ui_list = [item for item in ui_list if item.get("label") != payload.label]
        print("After deletion:", new_ui_list)

        if len(ui_list) == len(new_ui_list):
            raise HTTPException(status_code=404, detail="UI Parameter with this label not found")

        style.ui_parameters = json.dumps(new_ui_list)
        db.commit()
        db.refresh(style)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")

    return style


@router.get("/products/style_id", response_model=list)
def get_products_by_style_id(
    style_id: int = Query(..., description="Provide a single style_id"),
    db: Session = Depends(get_db)
):
    ProductMetadataAlias = aliased(ProductMetadata)

    s = str(style_id)
    metadata_filters = [
    ProductMetadataAlias.meta_value.like(f'[{s},%'),
    ProductMetadataAlias.meta_value.like(f'%,{s},%'),
    ProductMetadataAlias.meta_value.like(f'%,{s}]'),
    ProductMetadataAlias.meta_value.like(f'[%{s}%')
    ]

    products = (
        db.query(Product)
        .join(ProductMetadataAlias, Product.id == ProductMetadataAlias.product_id)
        .filter(ProductMetadataAlias.meta_key == 'style_id')
        .filter(or_(*metadata_filters))
        .distinct()
        .all()
    )

    if not products:
        raise HTTPException(status_code=404, detail="No products found with given style_id.")

    return [{"id": p.id, 
             "title": p.title,
             "description":p.description,
             "price":p.price,
             "thumbnail":p.thumbnail,
             "images":p.images} for p in products]  

