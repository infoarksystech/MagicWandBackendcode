from fastapi import APIRouter, Depends, status
from app.schemas.otp_auth import FirebaseTokenLoginRequest, OTPTokenResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.otp_auth import OTPAuthService

router = APIRouter(prefix="/otp", tags=["OTP Auth"])

@router.post("/token-login", response_model=OTPTokenResponse)
async def token_login(
    request: FirebaseTokenLoginRequest,
    db: Session = Depends(get_db),
):
    return await OTPAuthService.login_with_firebase_token(request.firebase_token, db)
