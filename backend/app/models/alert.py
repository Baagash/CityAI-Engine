from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from app.database import Base

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, index=True, nullable=False)  # ALT-XXXXXX
    alert_type = Column(String(50), nullable=False)  # POSSIBLE_DUPLICATE_PLATE, IMPOSSIBLE_TRAVEL, REGISTRY_MISMATCH, TRAFFIC_CONGESTION
    severity = Column(String(20), default="WARNING")  # CRITICAL, WARNING, INFO
    status = Column(String(50), default="REQUIRES_VERIFICATION")  # REQUIRES_VERIFICATION, UNDER_INVESTIGATION, VERIFIED_ANOMALY, DISMISSED_FALSE_POSITIVE, CASE_CREATED
    plate_text = Column(String(50), index=True, nullable=True)
    vehicle_id = Column(Integer, nullable=True)
    source_camera_id = Column(String(50), nullable=True)
    target_camera_id = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    evidence_score = Column(Float, default=0.85)  # AI match discrepancy score or anomaly probability
    details_json = Column(Text, nullable=True)  # JSON payload with metrics, differences, side-by-side data
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
