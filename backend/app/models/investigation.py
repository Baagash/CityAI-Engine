from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database import Base

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)  # CASE-2026-XXXX
    title = Column(String(200), nullable=False)
    assigned_officer = Column(String(100), default="Duty Officer - Traffic Intel")
    status = Column(String(50), default="OPEN")  # OPEN, UNDER_REVIEW, CLOSED_RESOLVED, CLOSED_FALSE_ALARM
    priority = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    target_plate = Column(String(50), index=True, nullable=True)
    target_vehicle_id = Column(String(50), nullable=True)
    summary = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)  # JSON or text logs of officer notes
    evidence_ids = Column(Text, nullable=True)  # comma separated or JSON array of evidence IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
