from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.org_user import OrgUserCreate, OrgUserStatusUpdate
from app.services.org_user import create_org_user, update_org_user_status


router = APIRouter(prefix="/org_user", tags=["Org Users"])


@router.post("/")
def create_user(payload: OrgUserCreate, db: Session = Depends(get_db)):
    return create_org_user(db, payload)


@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: OrgUserStatusUpdate,
    db: Session = Depends(get_db)
):
    user = update_org_user_status(db, user_id, payload.status)
    if not user:
        raise HTTPException(status_code=404, detail="Org user not found")
    return {"message": "Org user status updated", "status": user.status}
