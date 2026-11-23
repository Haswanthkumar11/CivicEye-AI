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
    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000,"
        "https://frontend-jc64-r7u81vqfy-haswanth1.vercel.app"
    )
    
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
    GEMINI_MODEL: str = "gemini-3.8-flash"
    AI_ANALYSIS_ENABLED: bool = True
    
    # Local Computer Vision (YOLO)
    YOLO_MODEL_PATH: str = "models/weights/road_damage_yolov8.onnx"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.35
    YOLO_DEVICE: str = "cpu"

    @property
    def resolved_yolo_model_path(self) -> str:
        """
        Dynamically locates YOLO model weights across different execution working directories:
        1. Exact relative/absolute path
        2. From backend/ directory looking at project root (../models/...)
        3. From project root looking inside backend/ (backend/models/...)
        """
        raw_path = self.YOLO_MODEL_PATH
        candidates = [raw_path]
        if raw_path.endswith(".pt"):
            candidates.append(raw_path.replace(".pt", ".onnx"))
        elif raw_path.endswith(".onnx"):
            candidates.append(raw_path.replace(".onnx", ".pt"))

        config_dir = os.path.dirname(os.path.abspath(__file__))  # app/core
        backend_dir = os.path.dirname(os.path.dirname(config_dir))  # backend
        project_root = os.path.dirname(backend_dir)  # project root

        for c in candidates:
            if os.path.isfile(c):
                return os.path.abspath(c)
            cand_root = os.path.join(project_root, c)
            if os.path.isfile(cand_root):
                return os.path.abspath(cand_root)
            cand_backend = os.path.join(backend_dir, c)
            if os.path.isfile(cand_backend):
                return os.path.abspath(cand_backend)
            cand_rel_parent = os.path.abspath(os.path.join("..", c))
            if os.path.isfile(cand_rel_parent):
                return os.path.abspath(cand_rel_parent)

        return raw_path

    # Local Speech Recognition (faster-whisper)
    WHISPER_MODEL_SIZE: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # Media Storage & Supabase Cloud Storage
    MEDIA_UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 25
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET: str = "civiceye-media"
    
    model_config = SettingsConfigDict(
        env_file=(
            ".env",
            "backend/.env",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backend", ".env"),
        ),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
