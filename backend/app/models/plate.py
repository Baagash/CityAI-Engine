from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.database import Base

class PlateRecord(Base):
    """
    SQLAlchemy Model for ANPR License Plate Observations and Associated Vehicle Attributes.
    Maintains link to camera-local tracker ID (never conflated with Global Vehicle ID).
    """
    __tablename__ = "plate_records"

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(String(60), unique=True, index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=False)
    tracker_id = Column(String(50), index=True, nullable=False)  # Local tracker ID, e.g. CAM01-TRK-001
    frame_number = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    
    # Plate Recognition Data
    plate_text = Column(String(50), index=True, nullable=False, default="UNKNOWN")  # Normalized clean text or UNKNOWN
    raw_text = Column(String(100), nullable=True)  # Raw OCR characters
    ocr_confidence = Column(Float, default=0.0, nullable=False)
    detection_confidence = Column(Float, default=0.0, nullable=False)
    validation_status = Column(String(50), default="UNKNOWN", nullable=False)  # VALID_FORMAT, INVALID_FORMAT, UNKNOWN
    
    # Plate Localization Coordinates (within frame or vehicle crop)
    plate_bbox_x1 = Column(Float, nullable=True)
    plate_bbox_y1 = Column(Float, nullable=True)
    plate_bbox_x2 = Column(Float, nullable=True)
    plate_bbox_y2 = Column(Float, nullable=True)
    plate_crop_path = Column(String(255), nullable=True)

    # Associated Vehicle Attributes
    vehicle_type = Column(String(50), default="UNKNOWN", nullable=False)  # car, motorcycle, bus, truck
    vehicle_color = Column(String(50), default="UNKNOWN", nullable=False)  # RED, BLUE, WHITE, BLACK, etc.
    color_confidence = Column(Float, default=0.0, nullable=False)

    # Global Vehicle Association (Phase 5)
    global_vehicle_id = Column(String(50), index=True, nullable=True)  # e.g., VEH-000042

    def to_dict(self):
        return {
            "id": self.id,
            "observation_id": self.observation_id,
            "camera_id": self.camera_id,
            "tracker_id": self.tracker_id,
            "global_vehicle_id": self.global_vehicle_id,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "plate_text": self.plate_text,
            "raw_text": self.raw_text,
            "ocr_confidence": round(self.ocr_confidence, 3),
            "detection_confidence": round(self.detection_confidence, 3),
            "validation_status": self.validation_status,
            "plate_bbox": [
                round(self.plate_bbox_x1, 1), round(self.plate_bbox_y1, 1),
                round(self.plate_bbox_x2, 1), round(self.plate_bbox_y2, 1)
            ] if self.plate_bbox_x1 is not None else None,
            "plate_crop_path": self.plate_crop_path,
            "vehicle_type": self.vehicle_type,
            "vehicle_color": self.vehicle_color,
            "color_confidence": round(self.color_confidence, 3)
        }

# Alias for backwards compatibility
Plate = PlateRecord
