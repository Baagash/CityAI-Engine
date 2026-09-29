from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.database import Base

class ReIDMatch(Base):
    """
    SQLAlchemy Model for Pairwise Vehicle Re-Identification Candidate Results.
    Stores multi-modal visual appearance similarity, attribute comparisons,
    spatiotemporal feasibility checks, and explicit decision categories.
    
    Decisions:
    - MATCH: Strong visual and spatiotemporal evidence of same vehicle
    - NO_MATCH: Visual or attribute conflict
    - UNCERTAIN: Inconclusive or ambiguous similarity
    - IMPOSSIBLE_TRANSIT: Physically impossible travel time between cameras (teleportation/anomaly)
    """
    __tablename__ = "reid_matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(60), unique=True, index=True, nullable=False)
    
    # Candidate Observations / Trackers
    observation_a_id = Column(String(60), index=True, nullable=True)
    observation_b_id = Column(String(60), index=True, nullable=True)
    camera_a = Column(String(50), index=True, nullable=False)
    camera_b = Column(String(50), index=True, nullable=False)
    tracker_a = Column(String(50), index=True, nullable=False)  # Local tracker ID, e.g. CAM01-TRK-017
    tracker_b = Column(String(50), index=True, nullable=False)  # Local tracker ID, e.g. CAM02-TRK-004
    time_elapsed_sec = Column(Float, default=0.0, nullable=False)

    # Multi-Modal Similarity Signals
    visual_similarity = Column(Float, default=0.0, nullable=False)  # Cosine similarity in [-1.0, 1.0]
    vehicle_type_similarity = Column(Float, default=0.0, nullable=False)  # [0.0, 1.0]
    color_similarity = Column(Float, default=0.0, nullable=False)  # [0.0, 1.0]
    plate_similarity = Column(Float, default=0.0, nullable=False)  # Auxiliary string similarity [0.0, 1.0]
    spatiotemporal_feasible = Column(Boolean, default=True, nullable=False)
    
    # Composite Decision Score
    composite_score = Column(Float, default=0.0, nullable=False)
    decision = Column(String(50), index=True, nullable=False)  # MATCH, NO_MATCH, UNCERTAIN, IMPOSSIBLE_TRANSIT
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "match_id": self.match_id,
            "observation_a_id": self.observation_a_id,
            "observation_b_id": self.observation_b_id,
            "camera_a": self.camera_a,
            "camera_b": self.camera_b,
            "tracker_a": self.tracker_a,
            "tracker_b": self.tracker_b,
            "time_elapsed_sec": round(self.time_elapsed_sec, 2),
            "visual_similarity": round(self.visual_similarity, 4),
            "vehicle_type_similarity": round(self.vehicle_type_similarity, 3),
            "color_similarity": round(self.color_similarity, 3),
            "plate_similarity": round(self.plate_similarity, 3),
            "spatiotemporal_feasible": self.spatiotemporal_feasible,
            "composite_score": round(self.composite_score, 4),
            "decision": self.decision,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
