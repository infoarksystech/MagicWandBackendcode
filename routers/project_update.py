from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.models.models import Prompt
from app.schemas.project_update import ProductPreviewListResponse
from app.schemas.projects import ProjectResponse
from app.services.project_update import ProjectServiceUpdate
from app.db.database import get_db
from app.core.security import get_current_user,check_admin_role

router = APIRouter(prefix="/project-update", tags=["Projects-Update"])


@router.get("/related-previews", response_model=ProductPreviewListResponse)
def get_related_product_previews(
    product_id: int = Query(...),
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]
    return ProjectServiceUpdate.get_related_previews(db, product_id, user_id)

@router.post("/update-project", response_model=ProjectResponse)
def update_project_product(
    original_project_id: int = Query(...),
    new_product_id: int = Query(...),
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(get_current_user)
):
    user_id = token["id"]

    try:
        return ProjectServiceUpdate.update_product_with_existing_prompt(
            db=db,
            user_id=user_id,
            new_product_id=new_product_id,
            original_project_id=original_project_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/update-project-admin", response_model=ProjectResponse,dependencies=[Depends(check_admin_role)])
def update_project_product_admin(
    original_project_id: int = Query(...),
    new_product_id: int = Query(...),
    user_id  : int = Query(...),
    db: Session = Depends(get_db)
):

    try:
        return ProjectServiceUpdate.update_product_with_existing_prompt(
            db=db,
            user_id=user_id,
            new_product_id=new_product_id,
            original_project_id=original_project_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


