from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.vehicle import Vehicle
from app.models.trajectory import Trajectory
from app.schemas.schemas import TrajectoryPoint
from app.services.trajectory_engine import topology_engine

router = APIRouter(prefix="/trajectories", tags=["Trajectories"])

@router.get("/{identifier}", response_model=List[TrajectoryPoint])
def get_vehicle_trajectory(identifier: str, db: Session = Depends(get_db)):
    """
    Reconstructs the full multi-camera journey path for a vehicle by Global ID or Plate.
    """
    vehicle = db.query(Vehicle).filter(
        (Vehicle.global_id == identifier) | (Vehicle.primary_plate == identifier)
    ).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    points = db.query(Trajectory).filter(
        Trajectory.vehicle_id == vehicle.id
    ).order_by(Trajectory.timestamp.asc()).all()

    result = []
    for p in points:
        cam_info = topology_engine.get_camera(p.camera_id)
        cam_name = cam_info["name"] if cam_info else p.camera_id
        result.append(TrajectoryPoint(
            id=p.id,
            camera_id=p.camera_id,
            camera_name=cam_name,
            timestamp=p.timestamp,
            latitude=p.latitude,
            longitude=p.longitude,
            speed_kmh=p.speed_kmh,
            travel_time_from_prev_seconds=p.travel_time_from_prev_seconds,
            route_segment_from=p.route_segment_from,
            route_confidence=p.route_confidence,
            is_anomaly=p.is_anomaly
        ))
    return result
