from pydantic import BaseModel

class FirebaseTokenLoginRequest(BaseModel):
    firebase_token: str
