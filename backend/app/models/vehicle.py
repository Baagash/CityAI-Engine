from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    global_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., VEH-000042
    primary_plate = Column(String(50), index=True, nullable=True)
    vehicle_type = Column(String(50), default="car")
    color = Column(String(50), default="UNKNOWN")
    confidence = Column(Float, default=0.85)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_sightings = Column(Integer, default=1)
    is_flagged = Column(Boolean, default=False)
    notes = Column(String(500), nullable=True)

    # Phase 5 Re-ID & Multi-Camera Tracking Fields
    appearance_embedding = Column(Text, nullable=True)  # JSON-encoded 512-D L2-normalized feature vector
    last_camera_id = Column(String(50), index=True, nullable=True)  # e.g., CAM01
    last_seen_timestamp = Column(DateTime, default=datetime.utcnow, nullable=True)
    reid_decision = Column(String(50), default="MATCH", nullable=True)  # MATCH, REVIEW_REQUIRED, REJECT
    reid_reason = Column(String(255), default="INITIAL_CREATION", nullable=True)

    detections = relationship("Detection", back_populates="vehicle", cascade="all, delete-orphan")
    trajectories = relationship("Trajectory", back_populates="vehicle", cascade="all, delete-orphan")

    def to_dict(self):
        import json
        emb = None
        if self.appearance_embedding:
            try:
                emb = json.loads(self.appearance_embedding)
            except Exception:
                emb = None
        return {
            "id": self.id,
            "global_id": self.global_id,
            "primary_plate": self.primary_plate,
            "vehicle_type": self.vehicle_type,
            "color": self.color,
            "confidence": round(self.confidence, 3),
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "total_sightings": self.total_sightings,
            "is_flagged": self.is_flagged,
            "notes": self.notes,
            "last_camera_id": self.last_camera_id,
            "last_seen_timestamp": self.last_seen_timestamp.isoformat() if self.last_seen_timestamp else None,
            "reid_decision": self.reid_decision,
            "reid_reason": self.reid_reason,
            "has_embedding": emb is not None
        }

