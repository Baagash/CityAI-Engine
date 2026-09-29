from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json
import torch

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CityAI Traffic Intelligence"
    SYSTEM_TITLE: str = "CITY AI TRAFFIC COMMAND CENTER"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Routing
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/api/v1"
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8001",
        "*"
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        return v
    
    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'traffic_intelligence.db'}"
    
    # Static & Storage Directories
    VIDEOS_DIR: Path = BASE_DIR / "videos"
    SNAPSHOT_DIR: Path = BASE_DIR / "snapshots"
    EVIDENCE_DIR: Path = BASE_DIR / "evidence"
    DATA_DIR: Path = BASE_DIR.parent / "data"

    # AI Detection & Tracking Configuration (Phase 3)
    YOLO_MODEL_NAME: str = "yolov8n.pt"
    YOLO_MODEL_PATH: Path = BASE_DIR / "yolov8n.pt"
    VEHICLE_DETECTION_CONFIDENCE: float = 0.35
    DEVICE: str = "cuda" if torch.cuda.is_available() else "cpu"
    TRACKER_IOU_THRESHOLD: float = 0.30
    TRACKER_MAX_AGE: int = 25  # Frames to retain track without detection
    FRAME_SKIP: int = 2  # Run detection on every Nth frame for real-time efficiency
    ENABLE_DETECTION: bool = True
    ENABLE_TRACKING: bool = True
    MAX_SIMULTANEOUS_STREAMS: int = 8

    # Target Vehicle Classes
    SUPPORTED_VEHICLE_CLASSES: List[str] = ["car", "motorcycle", "bus", "truck"]

    # ANPR & OCR Configuration (Phase 4)
    ENABLE_ANPR: bool = True
    ANPR_OCR_FRAME_INTERVAL: int = 5  # Run OCR every N frames per active track
    ANPR_MIN_OCR_CONFIDENCE: float = 0.40
    ANPR_GPU: bool = False  # EasyOCR CPU by default
    ANPR_MAX_OCR_OPS_PER_SEC: int = 4
    ENABLE_VEHICLE_ATTRIBUTES: bool = True

    # Vehicle Re-Identification Configuration (Phase 5)
    ENABLE_REID: bool = True
    REID_VISUAL_SIMILARITY_THRESHOLD: float = 0.75  # Configurable default
    REID_COMPOSITE_MATCH_THRESHOLD: float = 0.80   # Configurable default
    REID_WEIGHT_VISUAL: float = 0.40               # 40%
    REID_WEIGHT_PLATE: float = 0.30                # 30%
    REID_WEIGHT_ATTRIBUTES: float = 0.15           # 15% (Type + Colour)
    REID_WEIGHT_SPATIOTEMPORAL: float = 0.15       # 15%
    REID_EMBEDDING_DIM: int = 512
    REID_CANDIDATE_SEARCH_WINDOW_SEC: float = 3600.0  # Search candidates within 1 hour
    REID_MIN_STABLE_FRAMES: int = 3                # Frames before embedding extraction

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow"
    )


settings = Settings()

# Ensure directories exist
settings.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
settings.SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
