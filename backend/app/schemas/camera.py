from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re

class CameraBase(BaseModel):
    camera_name: str = Field(..., min_length=2, max_length=100, description="Human readable name of camera")
    location_name: str = Field(..., min_length=2, max_length=150, description="Intersection or road location")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="GIS Latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="GIS Longitude")
    zone: str = Field(default="Zone A - Downtown", max_length=100)
    direction: str = Field(default="NORTHBOUND", max_length=50)
    source_type: str = Field(default="LOCAL_VIDEO", description="LOCAL_VIDEO, WEBCAM, or RTSP")
    source_url: Optional[str] = Field(default=None, max_length=500)
    local_video_path: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None)
    is_demo: bool = Field(default=True)

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_sources = ["LOCAL_VIDEO", "WEBCAM", "RTSP"]
        v_upper = v.upper()
        if v_upper not in valid_sources:
            raise ValueError(f"source_type must be one of: {', '.join(valid_sources)}")
        return v_upper

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        valid_dirs = ["NORTHBOUND", "SOUTHBOUND", "EASTBOUND", "WESTBOUND", "BIDIRECTIONAL", "INTERSECTION"]
        v_upper = v.upper()
        if v_upper not in valid_dirs:
            return v_upper
        return v_upper

class CameraCreate(CameraBase):
    camera_id: str = Field(..., min_length=2, max_length=50, description="Unique camera identifier, e.g. CAM01")

    @field_validator("camera_id")
    @classmethod
    def validate_camera_id(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^[A-Z0-9_\-]+$", clean):
            raise ValueError("camera_id must contain only alphanumeric characters, dashes, or underscores")
        return clean

class CameraUpdate(BaseModel):
    camera_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    location_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    zone: Optional[str] = Field(default=None, max_length=100)
    direction: Optional[str] = Field(default=None, max_length=50)
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    local_video_path: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    is_demo: Optional[bool] = None

class CameraResponse(CameraBase):
    id: int
    camera_id: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class CameraStatusResponse(BaseModel):
    camera_id: str
    status: str
    is_streaming: bool
    fps: float
    resolution: str
    width: int
    height: int
    frame_number: int
    timestamp: Optional[str] = None
    source_type: str
    source_path: Optional[str] = None
    error: Optional[str] = None

class CameraTopologyResponse(BaseModel):
    id: int
    source_camera_id: str
    destination_camera_id: str
    distance_km: float
    expected_min_minutes: float
    expected_max_minutes: float
    direction: str

    model_config = ConfigDict(from_attributes=True)

class CameraStatsResponse(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    active_streams: int
