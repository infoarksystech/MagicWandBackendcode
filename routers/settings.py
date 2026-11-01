# routers/app_settings.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.settings import SettingService
from app.schemas.settings import AppSettingsCreate, AppSettingsUpdate, AppSettingsOut
from app.db.database import get_db

router = APIRouter(prefix="/settings", tags=["App Settings"])

@router.post("/", response_model=AppSettingsOut)
def create(setting: AppSettingsCreate, db: Session = Depends(get_db)):
    return SettingService.create_setting(db, setting)

@router.get("/", response_model=list[AppSettingsOut])
def read_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return SettingService.get_all_settings(db, skip, limit)

@router.get("/{setting_id}", response_model=AppSettingsOut)
def read_one(setting_id: int, db: Session = Depends(get_db)):
    setting = SettingService.get_setting(db, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{setting_id}", response_model=AppSettingsOut)
def update(setting_id: int, updates: AppSettingsUpdate, db: Session = Depends(get_db)):
    updated = SettingService.update_setting(db, setting_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Setting not found")
    return updated

@router.delete("/{setting_id}")
def delete(setting_id: int, db: Session = Depends(get_db)):
    deleted = SettingService.delete_setting(db, setting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"detail": "Deleted successfully"}
