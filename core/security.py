from fastapi.security.http import HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta
from app.core.config import settings
from jose import JWTError, jwt
from app.schemas.auth import TokenResponse
from fastapi import HTTPException, Depends
from app.models.models import User
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer
from app.db.database import get_db
from app.utils.responses import ResponseHandler

# ✅ ARGON2 — no bcrypt dependency
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

auth_scheme = HTTPBearer()

# -----------------------
# Password helpers
# -----------------------

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------
# Token helpers
# -----------------------

async def get_user_token(id: int, refresh_token=None):
    payload = {"id": id}

    access_token_expiry = timedelta(
        minutes=settings.access_token_expire_minutes
    )

    access_token = await create_access_token(payload)

    if not refresh_token:
        refresh_token = await create_refresh_token(payload)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=access_token_expiry.seconds
    )


async def create_access_token(data: dict):
    payload = data.copy()
    payload.update({
        "exp": datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    })
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


async def create_refresh_token(data: dict):
    return jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)


def get_token_payload(token: str):
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
    except JWTError:
        raise ResponseHandler.invalid_token("access")


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme)
):
    return get_token_payload(token.credentials)


def check_admin_role(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    payload = get_token_payload(token.credentials)
    user = db.query(User).filter(User.id == payload["id"]).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
