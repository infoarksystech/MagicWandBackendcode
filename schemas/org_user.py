from pydantic import BaseModel
from typing import Optional


class OrgUserCreate(BaseModel):
    org_id: int
    full_name: str
    user_role: str
    user_type: str
    email_id: str
    phone: Optional[str] = None
    personal_id: Optional[str] = None
    id_type: Optional[str] = None
    status: Optional[str] = "active"
    address: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class OrgUserStatusUpdate(BaseModel):
    status: str
