from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class Camera(Base):
    """
    SQLAlchemy Model for City Traffic Camera nodes.
    Supports LOCAL_VIDEO, WEBCAM, and RTSP video ingestion sources.
    """
    __tablename__ = "cameras"

    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    camera_name = Column(String(100), nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone = Column(String(100), default="Downtown", nullable=False)
    direction = Column(String(50), default="NORTHBOUND", nullable=False)
    source_type = Column(String(50), default="LOCAL_VIDEO", nullable=False)  # LOCAL_VIDEO, WEBCAM, RTSP
    source_url = Column(String(500), nullable=True)
    local_video_path = Column(String(500), nullable=True)
    status = Column(String(50), default="STOPPED", nullable=False)  # ONLINE, OFFLINE, STARTING, STOPPED, ERROR, LOW_VISIBILITY
    description = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "zone": self.zone,
            "direction": self.direction,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "local_video_path": self.local_video_path,
            "status": self.status,
            "description": self.description,
            "is_demo": self.is_demo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class CameraTopology(Base):
    """
    SQLAlchemy Model for Corridor Transitions between Cameras in the City Road Network.
    Stores distance and transit timing constraints for future trajectory intelligence.
    """
    __tablename__ = "camera_topology"

    id = Column(Integer, primary_key=True, index=True)
    source_camera_id = Column(String(50), index=True, nullable=False)
    destination_camera_id = Column(String(50), index=True, nullable=False)
    distance_km = Column(Float, nullable=False)
    expected_min_minutes = Column(Float, nullable=False)
    expected_max_minutes = Column(Float, nullable=False)
    direction = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "source_camera_id": self.source_camera_id,
            "destination_camera_id": self.destination_camera_id,
            "distance_km": self.distance_km,
            "expected_min_minutes": self.expected_min_minutes,
            "expected_max_minutes": self.expected_max_minutes,
            "direction": self.direction,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
