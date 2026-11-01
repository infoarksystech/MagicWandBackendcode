from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.models import Project, Prompt
from app.schemas.projects import ProjectCreate, ProjectDisplayOnUi, ProjectResponse, ProjectResponsebyAdmin, ProjectResponsebyUser
from app.services.projects import ProjectService
# from app.services.projects import create_project
from app.db.database import get_db
from app.core.security import check_admin_role, get_current_user
import json
from datetime import date


router = APIRouter(prefix="/projects", tags=["Projects"])

# ✅ Static Route: Get all projects by admin
@router.get("/all_projects", status_code=200, response_model=List[ProjectResponsebyAdmin],
            dependencies=[Depends(check_admin_role)])
def all_projects(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search by keyword"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)")
):
    project_data = ProjectService.all_projects(db, search, start_date, end_date)
    projects = []

    for project in project_data:
        preview_urls = project.get("preview_image_urls")

        if isinstance(preview_urls, str):
            try:
                preview_urls = json.loads(preview_urls)
                if not isinstance(preview_urls, list):
                    preview_urls = [preview_urls]
            except json.JSONDecodeError:
                preview_urls = [preview_urls]
        elif not isinstance(preview_urls, list):
            preview_urls = []

        projects.append(
            ProjectResponsebyAdmin(
                id=project.get("id"),
                prompt_id=project.get("prompt_id"),
                user_id=project.get("user_id"),
                product_id=project.get("product_id"),
                product_title=project.get("product_title"),
                preview_img=preview_urls,
                display_on_ui=project.get("display_on_ui", False),
                created_at=project.get("created_at")
            )
        )

    return projects


# ✅ Create project
@router.post("/", response_model=ProjectResponse)
def create_project_api(
    product_id: int = Form(...),
    type: Optional[str] = Form(None),
    imageType: Optional[str] = Form(None),
    imageStyle: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    background: Optional[str] = Form(None),
    colorPreference: Optional[str] = Form(None),
    otherKeywords: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    textStyle: Optional[str] = Form(None),
    textColor: Optional[str] = Form(None),
    imageFormat: Optional[str] = Form(None),
    regenerated: Optional[bool] = Form(False),
    remix: bool = Form(False),
    ref_image_url: UploadFile = File(None),
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]

    user_parameters = {
        "type": type,
        "imageType": imageType,
        "imageStyle": imageStyle,
        "subject": subject,
        "background": background,
        "colorPreference": colorPreference,
        "otherKeywords": otherKeywords,
        "text": text,
        "textStyle": textStyle,
        "textColor": textColor,
        "imageFormat": imageFormat
    }

    project_data = ProjectCreate(
        product_id=product_id,
        user_parameters=user_parameters,
        regenerated=regenerated,
        remix=remix
    )

    return ProjectService.create_project(
        db=db,
        project_data=project_data,
        user_id=user_id,
        ref_image_file=ref_image_url
    )

# ✅ Get user-specific projects
@router.get("/", response_model=List[ProjectResponsebyUser])
def get_user_projects_api(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]
    return ProjectService.get_projects_by_user_id(db, user_id)

# ✅ Get specific project by ID
@router.get("/{project_id}", response_model=ProjectResponsebyUser)
def get_project_by_id(
    project_id: int,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]
    return ProjectService.get_project_by_id(db, project_id, user_id)


@router.put("/update-display-on-ui", response_model=ProjectDisplayOnUi, 
            dependencies=[Depends(check_admin_role)])
def update_display_on_ui(
    project_id: int = Query(...),
    display_on_ui: bool = Query(...),
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]
    
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.display_on_ui = display_on_ui
    db.commit()
    db.refresh(project)  # ✅ refresh to get updated data

    # ✅ manually map the fields
    return ProjectDisplayOnUi(
        project_id=project.id,
        display_on_ui=project.display_on_ui
    )


# ✅ Create project
@router.post("/admin/", response_model=ProjectResponse,dependencies=[Depends(check_admin_role)])
def create_project_by_admin(
    product_id: int = Form(...),
    type: Optional[str] = Form(None),
    imageType: Optional[str] = Form(None),
    imageStyle: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    background: Optional[str] = Form(None),
    colorPreference: Optional[str] = Form(None),
    otherKeywords: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    textStyle: Optional[str] = Form(None),
    textColor: Optional[str] = Form(None),
    imageFormat: Optional[str] = Form(None),
    regenerated: Optional[bool] = Form(False),
    remix: bool = Form(False),
    ref_image_url: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_id : int = Form(...)
):

    user_parameters = {
        "type": type,
        "imageType": imageType,
        "imageStyle": imageStyle,
        "subject": subject,
        "background": background,
        "colorPreference": colorPreference,
        "otherKeywords": otherKeywords,
        "text": text,
        "textStyle": textStyle,
        "textColor": textColor,
        "imageFormat": imageFormat
    }

    project_data = ProjectCreate(
        product_id=product_id,
        user_parameters=user_parameters,
        regenerated=regenerated,
        remix=remix
    )

    return ProjectService.create_project(
        db=db,
        project_data=project_data,
        user_id=user_id,
        ref_image_file=ref_image_url
    )


@router.delete("/{project_id}", status_code=200)
def soft_delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id,
        Project.is_deleted == False
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.is_deleted = True
    db.commit()
    return {"message": "Project deleted successfully (soft delete)"}    

  


