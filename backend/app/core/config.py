import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicEye AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DESCRIPTION: str = "Multimodal AI-Powered Civic Intelligence Platform"
    
    # Environment & Host
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Origins as comma-separated string or JSON string from .env
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        if self.CORS_ORIGINS.strip().startswith("[") and self.CORS_ORIGINS.strip().endswith("]"):
            import json
            try:
                return json.loads(self.CORS_ORIGINS)
            except Exception:
                pass
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]
    
    # Authentication & Security
    SECRET_KEY: str = "civiceye_development_fallback_secret_key_min_32_chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite:///./civiceye_dev.db"  # Defaults to SQLite dev database, overrides via env for PostgreSQL/Supabase
    
    # External AI Services (Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Local Computer Vision (YOLO)
    YOLO_MODEL_PATH: str = "models/weights/road_damage_yolov8.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.35
    YOLO_DEVICE: str = "cpu"
    
    # Local Speech Recognition (faster-whisper)
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    
    # Media Storage
    MEDIA_UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 25
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
