from pydantic import BaseModel
from typing import Optional


class OrganizationCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    org_type: str
    brn_no: Optional[str] = None
    personal_id: Optional[str] = None
    id_type: Optional[str] = None
    status: Optional[str] = "active"
    address1: Optional[str] = None
    address2: Optional[str] = None
    floor_no: Optional[str] = None
    unit_no: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    timezone: Optional[str] = None
    map_url: Optional[str] = None
    location_source: Optional[str] = None
    accuracy_meters: Optional[float] = None
    parent_org_id: Optional[int] = None



class OrganizationStatusUpdate(BaseModel):
    status: str
