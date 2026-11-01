from sqlalchemy.orm import Session
from app.models.models import OrgUser



def create_org_user(db: Session, data):
    user = OrgUser(**data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_org_user_status(db: Session, user_id: int, status: str):
    user = db.query(OrgUser).filter(OrgUser.user_id == user_id).first()
    if not user:
        return None
    user.status = status
    db.commit()
    return user
