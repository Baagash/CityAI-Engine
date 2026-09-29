from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PlateObservationItem(BaseModel):
    id: Optional[int] = None
    observation_id: str
    camera_id: str
    tracker_id: str
    frame_number: int
    timestamp: Optional[str] = None
    plate_text: str = Field(default="UNKNOWN", description="Normalized plate string")
    raw_text: Optional[str] = None
    ocr_confidence: float = Field(default=0.0, description="OCR confidence score 0.0 - 1.0")
    detection_confidence: float = Field(default=0.0)
    validation_status: str = Field(default="UNKNOWN", description="VALID_FORMAT, INVALID_FORMAT, UNKNOWN")
    plate_bbox: Optional[List[float]] = None
    plate_crop_path: Optional[str] = None
    vehicle_type: str = Field(default="UNKNOWN")
    vehicle_color: str = Field(default="UNKNOWN")
    color_confidence: float = Field(default=0.0)

    model_config = ConfigDict(from_attributes=True)

class PlateSearchResponse(BaseModel):
    query: str
    total_matches: int
    matches: List[PlateObservationItem]

class VehicleAttributesItem(BaseModel):
    camera_id: str
    tracker_id: str
    vehicle_type: str
    vehicle_color: str
    color_confidence: float
    plate_text: str
    ocr_confidence: float
    validation_status: str
    last_seen: Optional[str] = None

class PlateStatsResponse(BaseModel):
    anpr_enabled: bool
    ocr_engine: str
    ocr_version: str
    device: str
    total_observations_recorded: int
    unique_plates_count: int
    valid_format_count: int
    invalid_format_count: int
    unknown_count: int
    supported_formats: List[str]

class SinglePlateOCRResponse(BaseModel):
    status: str
    timestamp: str
    inference_ms: float
    plate_text: str
    raw_text: Optional[str] = None
    ocr_confidence: float
    validation_status: str
    is_valid_format: bool
    vehicle_attributes: Optional[Dict[str, Any]] = None
