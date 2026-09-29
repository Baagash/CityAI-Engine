from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class DetectedObjectItem(BaseModel):
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] bounding box coordinates")
    center: List[float] = Field(..., description="[cx, cy] center point coordinates")
    vehicle_class: str = Field(..., alias="class", description="car, motorcycle, bus, truck")
    confidence: float = Field(..., description="Detection confidence score 0.0 - 1.0")

    model_config = ConfigDict(populate_by_name=True)

class DetectionItem(BaseModel):
    id: Optional[int] = None
    detection_id: str
    camera_id: str
    tracker_id: str
    frame_number: int
    timestamp: Optional[str] = None
    vehicle_class: str
    confidence: float
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2]")
    center: List[float] = Field(..., description="[cx, cy]")
    frame_dimensions: List[int] = Field(default=[640, 360])
    snapshot_path: Optional[str] = None
    crop_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ActiveTrackItem(BaseModel):
    tracker_id: str
    display_id: Optional[str] = None
    camera_id: str
    vehicle_class: str
    confidence: float
    bbox: List[float]
    center: List[float]
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_frames: int
    status: str
    trajectory_points: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class CameraTrackResponse(BaseModel):
    id: Optional[int] = None
    camera_id: str
    tracker_id: str
    vehicle_class: str
    status: str
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    total_frames: int
    avg_confidence: float
    last_bbox: List[float]
    trajectory_points: List[Dict[str, Any]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class DetectionStatsResponse(BaseModel):
    model_name: str
    device: str
    torch_version: str
    cuda_available: bool
    supported_classes: List[str]
    confidence_threshold: float
    total_detections_recorded: int
    active_tracks_count: int
    processing_fps: float
    avg_inference_ms: float

class LiveDetectionsResponse(BaseModel):
    status: str
    timestamp: str
    active_cameras: int
    total_active_tracks: int
    active_tracks: List[ActiveTrackItem]
    recent_detections: List[DetectionItem]
    hardware: Dict[str, Any]

class SingleFrameInferenceResponse(BaseModel):
    status: str
    timestamp: str
    inference_ms: float
    total_vehicles_detected: int
    vehicle_counts: Dict[str, int]
    detections: List[Dict[str, Any]]
