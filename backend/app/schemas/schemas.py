from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Camera Schemas ---
class CameraBase(BaseModel):
    camera_id: str
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    zone: str = "Downtown"
    direction: str = "Northbound"
    stream_type: str = "SYNTHETIC"
    stream_url_or_path: Optional[str] = None
    status: str = "ACTIVE"
    fps: float = 15.0

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    id: int
    created_at: datetime
    active_vehicles_count: Optional[int] = 0
    average_speed_kmh: Optional[float] = 45.0
    congestion_level: Optional[str] = "LOW"

    model_config = ConfigDict(from_attributes=True)

# --- Topology Graph Edge ---
class TopologyEdge(BaseModel):
    source_camera: str
    destination_camera: str
    distance_km: float
    expected_min_travel_time_sec: float
    expected_max_travel_time_sec: float
    direction: str

# --- Plate & Detection Schemas ---
class PlateResponse(BaseModel):
    id: int
    plate_text: str
    raw_text: Optional[str] = None
    ocr_confidence: float
    validation_status: str
    plate_crop_path: Optional[str] = None
    timestamp: datetime
    camera_id: str

    model_config = ConfigDict(from_attributes=True)

class DetectionResponse(BaseModel):
    id: int
    detection_id: str
    camera_id: str
    tracker_id: str
    frame_number: int
    timestamp: datetime
    vehicle_class: str
    confidence: float
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    color: str
    color_confidence: float
    speed_estimate: Optional[float] = None
    direction_heading: str
    snapshot_path: Optional[str] = None
    plate: Optional[PlateResponse] = None

    model_config = ConfigDict(from_attributes=True)

# --- Global Vehicle Schemas ---
class TrajectoryPoint(BaseModel):
    id: int
    camera_id: str
    camera_name: Optional[str] = None
    timestamp: datetime
    latitude: float
    longitude: float
    speed_kmh: Optional[float] = None
    travel_time_from_prev_seconds: Optional[float] = None
    route_segment_from: Optional[str] = None
    route_confidence: float = 1.0
    is_anomaly: int = 0

    model_config = ConfigDict(from_attributes=True)

class VehicleDetailResponse(BaseModel):
    id: int
    global_id: str
    primary_plate: Optional[str] = None
    vehicle_type: str
    color: str
    confidence: float
    first_seen: datetime
    last_seen: datetime
    total_sightings: int
    is_flagged: bool
    notes: Optional[str] = None
    last_camera_id: Optional[str] = None
    last_seen_timestamp: Optional[datetime] = None
    reid_decision: Optional[str] = "MATCH"
    reid_reason: Optional[str] = None
    registered_data: Optional[Dict[str, Any]] = None
    trajectories: List[TrajectoryPoint] = []
    detections: List[DetectionResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- Alert Schemas ---
class AlertReviewRequest(BaseModel):
    status: str = Field(..., description="VERIFIED_ANOMALY, DISMISSED_FALSE_POSITIVE, UNDER_INVESTIGATION")
    reviewed_by: str = "Duty Officer"
    review_notes: Optional[str] = None

class AlertResponse(BaseModel):
    id: int
    alert_id: str
    alert_type: str
    severity: str
    status: str
    plate_text: Optional[str] = None
    vehicle_id: Optional[int] = None
    source_camera_id: Optional[str] = None
    target_camera_id: Optional[str] = None
    title: str
    description: str
    evidence_score: float
    details_json: Optional[str] = None
    timestamp: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --- Investigation Case Schemas ---
class CaseCreate(BaseModel):
    title: str
    assigned_officer: str = "Duty Officer - Traffic Intel"
    priority: str = "HIGH"
    target_plate: Optional[str] = None
    target_vehicle_id: Optional[str] = None
    summary: str
    evidence_ids: Optional[List[str]] = []
    alert_id: Optional[str] = None

class CaseUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None

class InvestigationCaseResponse(BaseModel):
    id: int
    case_id: str
    title: str
    assigned_officer: str
    status: str
    priority: str
    target_plate: Optional[str] = None
    target_vehicle_id: Optional[str] = None
    summary: str
    notes: Optional[str] = None
    evidence_ids: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Registry Schemas ---
class RegistryVehicleCreate(BaseModel):
    registration_number: str
    vehicle_type: str
    make_model: str
    registered_color: str
    owner_name: str
    registration_date: Optional[str] = "2024-01-15"
    status: str = "ACTIVE"
    notes: Optional[str] = None

class RegistryVehicleResponse(RegistryVehicleCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Analytics & Simulation Schemas ---
class TrafficAnalyticsSummary(BaseModel):
    total_vehicles_tracked: int
    active_alerts_count: int
    critical_alerts_count: int
    average_city_speed_kmh: float
    overall_congestion_index: float  # 0.0 to 1.0
    weather_condition: str
    zone_stats: Dict[str, Any]
    hourly_flow: List[Dict[str, Any]]
    camera_health: Dict[str, str]

class SimulationScenarioRequest(BaseModel):
    scenario_type: str = Field(..., description="CLONED_PLATE, IMPOSSIBLE_SPEED, CONGESTION, STOLEN_VEHICLE, NORMAL_TRAFFIC")
    weather: Optional[str] = None  # CLEAR, RAIN, NIGHT, FOG
    target_camera: Optional[str] = None
