import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.camera import Camera, CameraTopology
from app.schemas.camera import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraStatusResponse,
    CameraTopologyResponse,
    CameraStatsResponse
)
from app.services.video_processor import stream_manager

logger = logging.getLogger("cityai.api.cameras")
router = APIRouter(prefix="/cameras", tags=["Camera Management & Ingestion"])

def resolve_video_path(source_type: str, local_path: Optional[str], source_url: Optional[str]) -> Optional[str]:
    """Helper to resolve video path or URL according to source_type."""
    if source_type == "LOCAL_VIDEO":
        if not local_path:
            return None
        p = Path(local_path)
        if p.is_absolute() and p.exists():
            return str(p)
        # Check in settings.VIDEOS_DIR
        video_dir_file = settings.VIDEOS_DIR / p.name
        if video_dir_file.exists():
            return str(video_dir_file)
        return str(local_path)
    elif source_type == "RTSP":
        return source_url
    elif source_type == "WEBCAM":
        return local_path or "0"
    return None

@router.get("", response_model=List[CameraResponse])
def list_cameras(
    zone: Optional[str] = Query(None, description="Filter cameras by zone"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    db: Session = Depends(get_db)
):
    """Retrieves all configured city traffic cameras with live status synchronization."""
    query = db.query(Camera)
    if zone:
        query = query.filter(Camera.zone == zone)
    if status_filter:
        query = query.filter(Camera.status == status_filter.upper())
    
    cameras = query.order_by(Camera.camera_id).all()
    
    # Sync runtime status from StreamManager
    result = []
    for cam in cameras:
        cam_dict = cam.to_dict()
        if stream_manager.is_camera_running(cam.camera_id):
            cam_dict["status"] = "ONLINE"
        result.append(cam_dict)
    
    return result

@router.get("/topology", response_model=List[CameraTopologyResponse])
def get_camera_topology(db: Session = Depends(get_db)):
    """Retrieves urban corridor transition graph edges between cameras."""
    transitions = db.query(CameraTopology).order_by(CameraTopology.id).all()
    return [t.to_dict() for t in transitions]

@router.get("/stats", response_model=CameraStatsResponse)
def get_camera_stats(db: Session = Depends(get_db)):
    """Retrieves real-time aggregated camera statistics."""
    cameras = db.query(Camera).all()
    total = len(cameras)
    
    active_streams = stream_manager.get_active_streams_count()
    online_count = 0
    offline_count = 0

    for cam in cameras:
        if stream_manager.is_camera_running(cam.camera_id):
            online_count += 1
        elif cam.status == "ONLINE":
            online_count += 1
        else:
            offline_count += 1

    return {
        "total_cameras": total,
        "online_cameras": online_count,
        "offline_cameras": offline_count,
        "active_streams": active_streams
    }

@router.post("", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
def create_camera(payload: CameraCreate, db: Session = Depends(get_db)):
    """Creates a new traffic camera node with source validation."""
    existing = db.query(Camera).filter(Camera.camera_id == payload.camera_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with ID '{payload.camera_id}' already exists."
        )

    # Validate source configuration
    if payload.source_type == "LOCAL_VIDEO" and not payload.local_video_path:
        # Default to a local video if not provided or mark as unassigned
        payload.local_video_path = f"backend/videos/{payload.camera_id.lower()}.mp4"
    elif payload.source_type == "RTSP" and not payload.source_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source URL is required when source_type is RTSP."
        )

    new_camera = Camera(
        camera_id=payload.camera_id,
        camera_name=payload.camera_name,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        zone=payload.zone,
        direction=payload.direction,
        source_type=payload.source_type,
        source_url=payload.source_url,
        local_video_path=payload.local_video_path,
        status="STOPPED",
        description=payload.description,
        is_demo=payload.is_demo
    )

    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    logger.info(f"Created new camera node: {new_camera.camera_id} - {new_camera.camera_name}")
    return new_camera.to_dict()

@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    """Retrieves a single camera by camera_id."""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )
    
    cam_dict = camera.to_dict()
    if stream_manager.is_camera_running(camera.camera_id):
        cam_dict["status"] = "ONLINE"
    return cam_dict

@router.patch("/{camera_id}", response_model=CameraResponse)
def update_camera(camera_id: str, payload: CameraUpdate, db: Session = Depends(get_db)):
    """Updates configuration fields for an existing camera."""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "source_type" and value:
            setattr(camera, field, value.upper())
        else:
            setattr(camera, field, value)

    db.commit()
    db.refresh(camera)
    logger.info(f"Updated camera node: {camera.camera_id}")
    return camera.to_dict()

@router.delete("/{camera_id}", status_code=status.HTTP_200_OK)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    """Deletes a camera node and cleanly terminates active video stream."""
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    # Stop stream if running
    stream_manager.stop_camera(camera.camera_id)

    db.delete(camera)
    db.commit()
    logger.info(f"Deleted camera node: {camera_id}")
    return {"status": "SUCCESS", "message": f"Camera '{camera_id}' deleted successfully."}

@router.post("/{camera_id}/start")
def start_camera_stream(camera_id: str, db: Session = Depends(get_db)):
    """
    Starts video ingestion for the specified camera using OpenCV VideoCapture.
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    resolved_path = resolve_video_path(camera.source_type, camera.local_video_path, camera.source_url)
    success, message = stream_manager.start_camera(camera.camera_id, camera.source_type, resolved_path)
    
    # Update status in DB
    camera.status = "ONLINE" if success else "ERROR"
    db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start camera: {message}"
        )

    return {
        "status": "SUCCESS",
        "camera_id": camera.camera_id,
        "message": message,
        "stream_url": f"/api/cameras/{camera.camera_id}/stream"
    }

@router.post("/{camera_id}/stop")
def stop_camera_stream(camera_id: str, db: Session = Depends(get_db)):
    """
    Stops video ingestion and releases OpenCV VideoCapture resources.
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    success, message = stream_manager.stop_camera(camera.camera_id)
    camera.status = "STOPPED"
    db.commit()

    return {
        "status": "SUCCESS",
        "camera_id": camera.camera_id,
        "message": message
    }

@router.get("/{camera_id}/status", response_model=CameraStatusResponse)
def get_camera_live_status(camera_id: str, db: Session = Depends(get_db)):
    """
    Returns real-time telemetry: FPS, resolution, frame number, timestamp, and stream status.
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    status_info = stream_manager.get_camera_status(
        camera.camera_id,
        fallback_source_type=camera.source_type,
        fallback_path=camera.local_video_path or camera.source_url
    )
    
    # Reconcile status with DB if not running
    if not status_info["is_streaming"] and camera.status == "ONLINE":
        status_info["status"] = "STOPPED"

    return status_info

@router.get("/{camera_id}/stream")
def get_camera_mjpeg_stream(
    camera_id: str,
    annotated: bool = Query(False, description="Stream AI HUD annotated stream if true"),
    db: Session = Depends(get_db)
):
    """
    Provides real-time MJPEG video stream encoded with OpenCV for HTML/React <img> consumption.
    Pass ?annotated=true to receive live YOLO bounding boxes, vehicle class tags, and tracker IDs.
    """
    camera = db.query(Camera).filter(Camera.camera_id == camera_id.upper()).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera '{camera_id}' not found."
        )

    # Auto-start stream if not running
    if not stream_manager.is_camera_running(camera.camera_id):
        resolved_path = resolve_video_path(camera.source_type, camera.local_video_path, camera.source_url)
        success, _ = stream_manager.start_camera(camera.camera_id, camera.source_type, resolved_path)
        if success:
            camera.status = "ONLINE"
            db.commit()

    return StreamingResponse(
        stream_manager.generate_mjpeg_stream(camera.camera_id, annotated=annotated),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/{camera_id}/annotated-stream")
def get_camera_annotated_stream(camera_id: str, db: Session = Depends(get_db)):
    """
    Direct endpoint for real-time AI HUD annotated MJPEG video stream.
    Overlays YOLO vehicle bounding boxes, local tracker IDs, confidence, and motion trajectories.
    """
    return get_camera_mjpeg_stream(camera_id=camera_id, annotated=True, db=db)

