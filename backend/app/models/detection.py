from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from app.database import Base

class DetectionRecord(Base):
    """
    SQLAlchemy Model for Individual Vehicle Detections on a per-frame basis.
    Records bounding boxes, class, confidence, local tracker ID, and spatial center coordinates.
    """
    __tablename__ = "detection_records"

    id = Column(Integer, primary_key=True, index=True)
    detection_id = Column(String(60), unique=True, index=True, nullable=False)
    camera_id = Column(String(50), index=True, nullable=False)
    tracker_id = Column(String(50), index=True, nullable=False)  # Local tracker ID, e.g. CAM01-TRK-17
    frame_number = Column(Integer, default=0, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
    vehicle_class = Column(String(50), default="car", nullable=False)  # car, motorcycle, bus, truck
    confidence = Column(Float, default=0.85, nullable=False)
    
    # Bounding Box normalized or pixel coordinates
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    
    # Center Point
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    
    # Frame Dimensions
    frame_width = Column(Integer, default=640)
    frame_height = Column(Integer, default=360)
    
    # Optional image crops
    snapshot_path = Column(String(255), nullable=True)
    crop_path = Column(String(255), nullable=True)

    # Global Vehicle Association (Phase 5)
    global_vehicle_id = Column(String(50), index=True, nullable=True)  # e.g., VEH-000042
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)

    vehicle = relationship("Vehicle", back_populates="detections", foreign_keys=[vehicle_id])

    def to_dict(self):
        return {
            "id": self.id,
            "detection_id": self.detection_id,
            "camera_id": self.camera_id,
            "tracker_id": self.tracker_id,
            "global_vehicle_id": self.global_vehicle_id,
            "vehicle_id": self.vehicle_id,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "vehicle_class": self.vehicle_class,
            "confidence": round(self.confidence, 3),
            "bbox": [round(self.bbox_x1, 1), round(self.bbox_y1, 1), round(self.bbox_x2, 1), round(self.bbox_y2, 1)],
            "center": [round(self.center_x, 1), round(self.center_y, 1)],
            "frame_dimensions": [self.frame_width, self.frame_height],
            "snapshot_path": self.snapshot_path,
            "crop_path": self.crop_path
        }

class CameraTrack(Base):
    """
    SQLAlchemy Model for Per-Camera Multi-Object Tracking History.
    Maintains track lifetime, bounding box sequence, and intra-camera trajectory.
    Note: Camera-local tracker IDs must NOT be treated as Global Vehicle IDs.
    """
    __tablename__ = "camera_tracks"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), index=True, nullable=False)
    tracker_id = Column(String(50), index=True, nullable=False)  # Local tracker ID, e.g. CAM01-TRK-17
    vehicle_class = Column(String(50), default="car", nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, LOST, COMPLETED
    
    first_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    total_frames = Column(Integer, default=1, nullable=False)
    avg_confidence = Column(Float, default=0.85, nullable=False)
    
    # Last Known Bounding Box
    last_bbox_x1 = Column(Float, nullable=False)
    last_bbox_y1 = Column(Float, nullable=False)
    last_bbox_x2 = Column(Float, nullable=False)
    last_bbox_y2 = Column(Float, nullable=False)
    
    # In-camera spatial trajectory points as JSON
    trajectory_points_json = Column(Text, default="[]", nullable=False)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "tracker_id": self.tracker_id,
            "vehicle_class": self.vehicle_class,
            "status": self.status,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "total_frames": self.total_frames,
            "avg_confidence": round(self.avg_confidence, 3),
            "last_bbox": [round(self.last_bbox_x1, 1), round(self.last_bbox_y1, 1), round(self.last_bbox_x2, 1), round(self.last_bbox_y2, 1)],
            "trajectory_points": json.loads(self.trajectory_points_json) if self.trajectory_points_json else []
        }

# Alias for backwards compatibility
Detection = DetectionRecord

