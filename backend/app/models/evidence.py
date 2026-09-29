from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database import Base

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(String(50), unique=True, index=True, nullable=False)  # EVD-XXXXXX
    alert_id = Column(String(50), index=True, nullable=True)
    case_id = Column(String(50), index=True, nullable=True)
    evidence_type = Column(String(50), default="SPLIT_VIEW")  # SPLIT_VIEW, CROP_COMPARISON, TRAJECTORY_MAP, OCR_BREAKDOWN
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    image_path_a = Column(String(255), nullable=True)
    image_path_b = Column(String(255), nullable=True)
    meta_data_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
