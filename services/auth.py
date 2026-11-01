from fastapi import HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models.models import User
from app.core.security import (
    verify_password,
    get_user_token,
    get_password_hash,
    get_token_payload
)
from app.utils.responses import ResponseHandler
from app.schemas.auth import Signup


class AuthService:

    @staticmethod
    async def login(
        user_credentials: OAuth2PasswordRequestForm,
        db: Session
    ):
        user = (
            db.query(User)
            .filter(User.username == user_credentials.username)
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid credentials"
            )

        if not verify_password(
            user_credentials.password,
            user.password
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid credentials"
            )

        return await get_user_token(id=user.id)

    @staticmethod
    async def signup(db: Session, user: Signup):
        hashed_password = get_password_hash(user.password)

        db_user = User(
            username=user.username,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            password=hashed_password
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return ResponseHandler.create_success(
            "User created successfully",
            db_user.id,
            db_user
        )

    @staticmethod
    async def get_refresh_token(token: str, db: Session):
        payload = get_token_payload(token)
        user_id = payload.get("id")

        if not user_id:
            raise ResponseHandler.invalid_token("refresh")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ResponseHandler.invalid_token("refresh")

        return await get_user_token(
            id=user.id,
            refresh_token=token
        )
