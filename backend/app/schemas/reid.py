from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CandidateObservation(BaseModel):
    camera_id: str
    tracker_id: str
    plate_text: Optional[str] = "UNKNOWN"
    vehicle_type: Optional[str] = "UNKNOWN"
    vehicle_color: Optional[str] = "UNKNOWN"

class ReIDComparisonRequest(BaseModel):
    observation_a_id: Optional[str] = None
    observation_b_id: Optional[str] = None
    camera_a: str = Field(..., description="Camera ID of first observation, e.g. CAM01")
    camera_b: str = Field(..., description="Camera ID of second observation, e.g. CAM02")
    tracker_a: str = Field(..., description="Camera-local tracker ID A, e.g. CAM01-TRK-001")
    tracker_b: str = Field(..., description="Camera-local tracker ID B, e.g. CAM02-TRK-004")
    plate_a: Optional[str] = "UNKNOWN"
    plate_b: Optional[str] = "UNKNOWN"
    type_a: Optional[str] = "car"
    type_b: Optional[str] = "car"
    color_a: Optional[str] = "UNKNOWN"
    color_b: Optional[str] = "UNKNOWN"
    time_elapsed_sec: float = Field(default=120.0, ge=0.0)
    save_result: bool = Field(default=True, description="Save match decision to reid_matches table")

class ReIDComparisonResponse(BaseModel):
    match_id: Optional[str] = None
    decision: str = Field(..., description="MATCH, NO_MATCH, UNCERTAIN, IMPOSSIBLE_TRANSIT")
    composite_score: float
    visual_similarity: float = Field(..., description="Raw Cosine similarity [-1.0, 1.0]")
    plate_similarity: float
    vehicle_type_similarity: float
    color_similarity: float
    spatiotemporal_score: float
    spatiotemporal_feasible: bool
    transit_status: str
    reason: str
    candidate_a: CandidateObservation
    candidate_b: CandidateObservation
    time_elapsed_sec: float

class ReIDMatchRecordItem(BaseModel):
    id: int
    match_id: str
    observation_a_id: Optional[str] = None
    observation_b_id: Optional[str] = None
    camera_a: str
    camera_b: str
    tracker_a: str
    tracker_b: str
    time_elapsed_sec: float
    visual_similarity: float
    vehicle_type_similarity: float
    color_similarity: float
    plate_similarity: float
    spatiotemporal_feasible: bool
    composite_score: float
    decision: str
    reason: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ReIDStatsResponse(BaseModel):
    total_comparisons: int
    matches_count: int
    no_matches_count: int
    uncertain_count: int
    impossible_transit_count: int
    visual_threshold: float
    composite_threshold: float

class VehicleReIDMatchRequest(BaseModel):
    camera_a: str = Field(default="CAM01", description="Source camera ID")
    camera_b: str = Field(default="CAM02", description="Destination camera ID")
    tracker_a: Optional[str] = "CAM01-TRK-001"
    tracker_b: Optional[str] = "CAM02-TRK-001"
    plate_a: Optional[str] = None
    plate_b: Optional[str] = None
    vehicle_type_a: Optional[str] = "car"
    vehicle_type_b: Optional[str] = "car"
    color_a: Optional[str] = "UNKNOWN"
    color_b: Optional[str] = "UNKNOWN"
    time_elapsed_sec: float = Field(default=120.0, ge=0.0)

class VehicleReIDMatchResponse(BaseModel):
    appearance_similarity: float
    plate_similarity: float
    attribute_similarity: float
    trajectory_feasibility: bool
    trajectory_score: float
    composite_score: float
    decision: str
    reason: str
    reason_code: str
    breakdown: Dict[str, float]
    candidate_a: Dict[str, Any]
    candidate_b: Dict[str, Any]
    time_elapsed_sec: float

