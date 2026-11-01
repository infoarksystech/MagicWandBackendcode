from datetime import timedelta
from app.core.security import (
    get_token_payload,
    create_access_token,
    create_refresh_token
)
from app.schemas.auth import TokenResponse
from app.core.config import settings


# Generate user token with role after OTP verification
async def get_user_token_with_role(id: int, role: str = "user", refresh_token=None):
    payload = {"id": id, "role": role}

    access_token_expiry = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = await create_access_token(payload, access_token_expiry)

    if not refresh_token:
        refresh_token = await create_refresh_token(payload)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=access_token_expiry.seconds,
        role=role
    )


# Optional if you want to extract user ID & role from token in OTP routes
def get_current_user_role(token):
    payload = get_token_payload(token)
    return payload.get('id'), payload.get('role')
