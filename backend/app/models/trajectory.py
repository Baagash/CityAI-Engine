from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Trajectory(Base):
    __tablename__ = "trajectories"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    camera_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, nullable=True)
    travel_time_from_prev_seconds = Column(Float, nullable=True)
    route_segment_from = Column(String(50), nullable=True)  # Previous camera_id
    route_confidence = Column(Float, default=1.0)
    is_anomaly = Column(Integer, default=0)  # 1 if impossible travel or timing violation

    vehicle = relationship("Vehicle", back_populates="trajectories")
