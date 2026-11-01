# services/app_settings_service.py
from sqlalchemy.orm import Session
from app.models.models import AppSettings
from app.schemas.settings import AppSettingsCreate, AppSettingsUpdate


class SettingService:
    @staticmethod
    def create_setting(db: Session, setting: AppSettingsCreate):
        db_setting = AppSettings(**setting.dict())
        db.add(db_setting)
        db.commit()
        db.refresh(db_setting)
        return db_setting
    
    @staticmethod
    def get_setting(db: Session, setting_id: int):
        return db.query(AppSettings).filter(AppSettings.id == setting_id).first()
    
    @staticmethod
    def get_all_settings(db: Session, skip: int = 0, limit: int = 100):
        return db.query(AppSettings).offset(skip).limit(limit).all()

    @staticmethod
    def update_setting(db: Session, setting_id: int, updates: AppSettingsUpdate):
        db_setting = db.query(AppSettings).filter(AppSettings.id == setting_id).first()
        if not db_setting:
            return None
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(db_setting, key, value)
        db.commit()
        db.refresh(db_setting)
        return db_setting
    
    @staticmethod
    def delete_setting(db: Session, setting_id: int):
        db_setting = db.query(AppSettings).filter(AppSettings.id == setting_id).first()
        if db_setting:
            db.delete(db_setting)
            db.commit()
        return db_setting
