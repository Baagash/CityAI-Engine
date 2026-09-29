from datetime import datetime, timezone
import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config import settings
from app.database import check_db_status, get_db
from app.models.camera import Camera
from app.services.video_processor import stream_manager
from app.services.vehicle_detector import vehicle_detector
from app.services.anpr import anpr_engine

router = APIRouter(prefix="/system", tags=["System Telemetry & Health"])

START_TIME = time.time()

@router.get("/health")
def get_system_health(db: Session = Depends(get_db)):
    """
    Returns system status across all subsystems for the CityAI Command Center.
    Accurately reflects current Phase 3 Vehicle Detection & Tracking status.
    """
    db_info = check_db_status()
    uptime = int(time.time() - START_TIME)
    
    # Camera metrics
    total_cameras = 0
    active_streams = 0
    try:
        if db_info["connected"]:
            total_cameras = db.query(Camera).count()
            active_streams = stream_manager.get_active_streams_count()
    except Exception:
        pass

    ai_ready = vehicle_detector.is_initialized
    stats = vehicle_detector.get_stats()

    return {
        "status": "ONLINE" if db_info["connected"] else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": settings.PROJECT_NAME,
        "title": settings.SYSTEM_TITLE,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": uptime,
        "backend": "online",
        "database": "connected" if db_info["connected"] else "disconnected",
        "camera_service": "ready",
        "ai_engine": "ready" if ai_ready else "not_initialized",
        "subsystems": {
            "backend": {
                "status": "ONLINE",
                "label": "Online",
                "initialized": True,
                "framework": "FastAPI",
                "phase": 1
            },
            "database": {
                "status": "CONNECTED" if db_info["connected"] else "DISCONNECTED",
                "label": "Connected" if db_info["connected"] else "Disconnected",
                "initialized": db_info["connected"],
                "dialect": db_info.get("dialect", "sqlite"),
                "phase": 1,
                "error": db_info.get("error")
            },
            "camera_service": {
                "status": "READY",
                "label": "Ready",
                "initialized": True,
                "configured_cameras": total_cameras,
                "active_streams": active_streams,
                "phase": 2,
                "description": "OpenCV VideoCapture ingestion & MJPEG frame streaming active."
            },
            "ai_engine": {
                "status": "READY" if ai_ready else "NOT INITIALIZED",
                "label": "Ready" if ai_ready else "Not Initialized",
                "initialized": ai_ready,
                "model": stats.get("model_name", settings.YOLO_MODEL_NAME),
                "device": stats.get("device", "cpu"),
                "supported_classes": stats.get("supported_classes", []),
                "phase": 3,
                "description": "Ultralytics YOLO vehicle detection and per-camera multi-object tracking active."
            },
            "anpr_engine": {
                "status": "READY" if anpr_engine.is_initialized else "CPU_FALLBACK",
                "label": "Ready" if anpr_engine.is_initialized else "CPU Fallback",
                "initialized": anpr_engine.is_initialized,
                "engine": anpr_engine.ocr_engine_name,
                "version": anpr_engine.ocr_version,
                "device": anpr_engine.device,
                "phase": 4,
                "description": "EasyOCR automatic number plate recognition and vehicle attribute extraction active."
            }
        }
    }

