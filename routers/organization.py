from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.organization import OrganizationCreate, OrganizationStatusUpdate
from app.services.organization import create_organization, update_organization_status

router = APIRouter(prefix="/organization", tags=["Organizations"])


@router.post("/")
def create_org(payload: OrganizationCreate, db: Session = Depends(get_db)):
    return create_organization(db, payload)


@router.patch("/{org_id}/status")
def update_org_status(
    org_id: int,
    payload: OrganizationStatusUpdate,
    db: Session = Depends(get_db)
):
    org = update_organization_status(db, org_id, payload.status)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"message": "Organization status updated", "status": org.status}
