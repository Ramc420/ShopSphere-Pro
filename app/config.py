import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ShopSphere Pro"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    
    # JWT & Security
    SECRET_KEY: str = "shopsphere-super-secure-production-jwt-secret-key-32-chars-min!"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str = "sqlite:///./shopsphere_pro.db"
    
    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
    ]
    ALLOWED_DOCUMENT_TYPES: List[str] = [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    
    # Default super admin seed
    SUPER_ADMIN_EMAIL: str = "admin@shopsphere.com"
    SUPER_ADMIN_PASSWORD: str = "Admin@ShopSphere2026!"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

