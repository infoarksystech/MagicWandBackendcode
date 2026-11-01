from sqlalchemy.orm import Session
from app.models.models import Organization


def create_organization(db: Session, data):
    org = Organization(**data.dict())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def update_organization_status(db: Session, org_id: int, status: str):
    org = db.query(Organization).filter(Organization.org_id == org_id).first()
    if not org:
        return None
    org.status = status
    db.commit()
    return org
