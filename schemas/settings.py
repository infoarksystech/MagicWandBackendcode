# schemas.py
from pydantic import BaseModel

class AppSettingsBase(BaseModel):
    app_key: str
    label: str
    app_value: str

class AppSettingsCreate(AppSettingsBase):
    pass

class AppSettingsUpdate(BaseModel):
    label: str = None
    app_value: str = None

class AppSettingsOut(AppSettingsBase):
    id: int

    class Config:
        from_attributes = True
