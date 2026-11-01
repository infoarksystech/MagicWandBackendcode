from firebase_admin import auth
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import User
from app.core.otp_security import get_user_token_with_role

class OTPAuthService:

    @staticmethod
    async def login_with_firebase_token(firebase_token: str, db: Session):
        try:
            decoded = auth.verify_id_token(firebase_token)
            phone = decoded.get("phone_number")
            if not phone:
                raise HTTPException(status_code=400, detail="Phone number not found in token.")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid Firebase token.")

        # Check if user exists
        user = db.query(User).filter(User.phone == phone).first()
        if not user:
            user = User(
                phone=phone,
                username=phone,
                email=f"{phone}@gmail.com",
                full_name="Demo User",
                password="demo@123",  # placeholder
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return await get_user_token_with_role(user.id, user.role)
