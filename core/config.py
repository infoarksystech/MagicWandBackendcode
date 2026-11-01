from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Config
    db_username: str
    db_password: str
    db_hostname: str
    db_port: str
    db_name: str
    openai_api_key: str  # Ensure this field exists in .env
    stability_key: str
    ideogram_key:str
    segment_api:str

    # JWT Config
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    class Config:
        env_file = ".env"


settings = Settings()
