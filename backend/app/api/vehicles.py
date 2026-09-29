from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.vehicle import Vehicle
from app.models.detection import Detection
from app.models.trajectory import Trajectory
from app.models.registry import DemoRegistryVehicle
from app.models.plate import PlateRecord
from app.schemas.schemas import VehicleDetailResponse, TrajectoryPoint, DetectionResponse, PlateResponse
from app.schemas.plate import PlateObservationItem
from app.schemas.reid import VehicleReIDMatchRequest, VehicleReIDMatchResponse
from app.services.vehicle_reid import reid_service
from app.services.trajectory_engine import topology_engine

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("", response_model=List[VehicleDetailResponse])
def search_vehicles(
    plate: Optional[str] = Query(None, description="Registration plate query"),
    global_id: Optional[str] = Query(None, description="Global identity query"),
    vehicle_type: Optional[str] = Query(None, description="Type filter: sedan, suv, truck, bus, motorcycle"),
    color: Optional[str] = Query(None, description="Color filter"),
    colour: Optional[str] = Query(None, description="Colour filter (alias)"),
    db: Session = Depends(get_db)
):
    """Searches global vehicle identities with multi-modal filters."""
    query = db.query(Vehicle)
    if plate:
        query = query.filter(Vehicle.primary_plate.ilike(f"%{plate.strip()}%"))
    if global_id:
        query = query.filter(Vehicle.global_id.ilike(f"%{global_id.strip()}%"))
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type.ilike(f"%{vehicle_type.strip()}%"))
    
    color_filter_val = color or colour
    if color_filter_val:
        query = query.filter(Vehicle.color.ilike(f"%{color_filter_val.strip()}%"))

    vehicles = query.order_by(Vehicle.last_seen.desc()).limit(50).all()
    
    result = []
    for v in vehicles:
        reg = db.query(DemoRegistryVehicle).filter(DemoRegistryVehicle.registration_number == v.primary_plate).first()
        reg_dict = None
        if reg:
            reg_dict = {
                "owner_name": reg.owner_name,
                "make_model": reg.make_model,
                "registered_color": reg.registered_color,
                "status": reg.status,
                "registration_date": reg.registration_date
            }
        
        # Load trajectories
        trajs = db.query(Trajectory).filter(Trajectory.vehicle_id == v.id).order_by(Trajectory.timestamp.asc()).all()
        # Load recent detections
        dets = db.query(Detection).filter(
            (Detection.vehicle_id == v.id) | (Detection.global_vehicle_id == v.global_id)
        ).order_by(Detection.timestamp.desc()).limit(10).all()

        det_responses = []
        for d in dets:
            p_resp = None
            if hasattr(d, 'plate') and d.plate:
                p_resp = PlateResponse(
                    id=d.plate.id,
                    plate_text=d.plate.plate_text,
                    raw_text=d.plate.raw_text,
                    ocr_confidence=d.plate.ocr_confidence,
                    validation_status=d.plate.validation_status,
                    plate_crop_path=d.plate.plate_crop_path,
                    timestamp=d.plate.timestamp,
                    camera_id=d.plate.camera_id
                )
            det_responses.append(DetectionResponse(
                id=d.id,
                detection_id=d.detection_id,
                camera_id=d.camera_id,
                tracker_id=d.tracker_id,
                frame_number=d.frame_number,
                timestamp=d.timestamp,
                vehicle_class=d.vehicle_class,
                confidence=d.confidence,
                bbox_x1=d.bbox_x1,
                bbox_y1=d.bbox_y1,
                bbox_x2=d.bbox_x2,
                bbox_y2=d.bbox_y2,
                color="UNKNOWN",
                color_confidence=0.8,
                speed_estimate=None,
                direction_heading="North",
                snapshot_path=d.snapshot_path,
                plate=p_resp
            ))

        traj_responses = [
            TrajectoryPoint(
                id=t.id,
                camera_id=t.camera_id,
                camera_name=topology_engine.get_camera(t.camera_id).get("name") if topology_engine.get_camera(t.camera_id) else t.camera_id,
                timestamp=t.timestamp,
                latitude=t.latitude,
                longitude=t.longitude,
                speed_kmh=t.speed_kmh,
                travel_time_from_prev_seconds=t.travel_time_from_prev_seconds,
                route_segment_from=t.route_segment_from,
                route_confidence=t.route_confidence,
                is_anomaly=t.is_anomaly
            ) for t in trajs
        ]

        result.append(VehicleDetailResponse(
            id=v.id,
            global_id=v.global_id,
            primary_plate=v.primary_plate,
            vehicle_type=v.vehicle_type,
            color=v.color,
            confidence=v.confidence,
            first_seen=v.first_seen,
            last_seen=v.last_seen,
            total_sightings=v.total_sightings,
            is_flagged=v.is_flagged,
            notes=v.notes,
            last_camera_id=v.last_camera_id,
            last_seen_timestamp=v.last_seen_timestamp,
            reid_decision=v.reid_decision or "MATCH",
            reid_reason=v.reid_reason,
            registered_data=reg_dict,
            trajectories=traj_responses,
            detections=det_responses
        ))

    return result

@router.post("/reid/match", response_model=VehicleReIDMatchResponse)
def match_vehicle_observations(
    req: VehicleReIDMatchRequest
):
    """
    Step 17 Re-ID Match API.
    Compares two vehicle observations/crops and returns explainable multimodal breakdown:
    appearance similarity, plate similarity, attribute similarity, trajectory feasibility,
    composite score, decision (MATCH, REVIEW_REQUIRED, REJECT), and reason code.
    """
    res = reid_service.match_observations(
        cam_a=req.camera_a,
        cam_b=req.camera_b,
        tracker_a=req.tracker_a or f"{req.camera_a}-TRK-001",
        tracker_b=req.tracker_b or f"{req.camera_b}-TRK-001",
        plate_a=req.plate_a,
        plate_b=req.plate_b,
        type_a=req.vehicle_type_a or "car",
        type_b=req.vehicle_type_b or "car",
        color_a=req.color_a or "UNKNOWN",
        color_b=req.color_b or "UNKNOWN",
        time_elapsed_sec=req.time_elapsed_sec
    )

    return VehicleReIDMatchResponse(
        appearance_similarity=res["visual_similarity"],
        plate_similarity=res["plate_similarity"],
        attribute_similarity=res["attribute_similarity"],
        trajectory_feasibility=res["spatiotemporal_feasible"],
        trajectory_score=res["spatiotemporal_score"],
        composite_score=res["composite_score"],
        decision=res["decision"],
        reason=res["reason"],
        reason_code=res["reason_code"],
        breakdown=res["breakdown"],
        candidate_a=res["candidate_a"],
        candidate_b=res["candidate_b"],
        time_elapsed_sec=res["time_elapsed_sec"]
    )

@router.get("/{global_id}/trajectories", response_model=List[TrajectoryPoint])
def get_vehicle_trajectories(global_id: str, db: Session = Depends(get_db)):
    """
    Step 17 Trajectory API.
    Retrieves chronological camera route waypoints for a specific vehicle.
    """
    vehicle = db.query(Vehicle).filter(
        (Vehicle.global_id == global_id) | (Vehicle.primary_plate == global_id)
    ).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle identity '{global_id}' not found."
        )

    trajs = db.query(Trajectory).filter(Trajectory.vehicle_id == vehicle.id).order_by(Trajectory.timestamp.asc()).all()
    
    return [
        TrajectoryPoint(
            id=t.id,
            camera_id=t.camera_id,
            camera_name=topology_engine.get_camera(t.camera_id).get("name") if topology_engine.get_camera(t.camera_id) else t.camera_id,
            timestamp=t.timestamp,
            latitude=t.latitude,
            longitude=t.longitude,
            speed_kmh=t.speed_kmh,
            travel_time_from_prev_seconds=t.travel_time_from_prev_seconds,
            route_segment_from=t.route_segment_from,
            route_confidence=t.route_confidence,
            is_anomaly=t.is_anomaly
        ) for t in trajs
    ]

@router.get("/{global_id}", response_model=VehicleDetailResponse)
def get_vehicle_detail(global_id: str, db: Session = Depends(get_db)):
    """Retrieves full vehicle dossier, trajectory map points, and sighting logs."""
    vehicle = db.query(Vehicle).filter(
        (Vehicle.global_id == global_id) | (Vehicle.primary_plate == global_id)
    ).first()
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vehicle identity '{global_id}' not found."
        )

    reg = db.query(DemoRegistryVehicle).filter(DemoRegistryVehicle.registration_number == vehicle.primary_plate).first()
    reg_dict = None
    if reg:
        reg_dict = {
            "owner_name": reg.owner_name,
            "make_model": reg.make_model,
            "registered_color": reg.registered_color,
            "status": reg.status,
            "registration_date": reg.registration_date
        }

    trajs = db.query(Trajectory).filter(Trajectory.vehicle_id == vehicle.id).order_by(Trajectory.timestamp.asc()).all()
    dets = db.query(Detection).filter(
        (Detection.vehicle_id == vehicle.id) | (Detection.global_vehicle_id == vehicle.global_id)
    ).order_by(Detection.timestamp.desc()).limit(20).all()

    det_responses = []
    for d in dets:
        p_resp = None
        if hasattr(d, 'plate') and d.plate:
            p_resp = PlateResponse(
                id=d.plate.id,
                plate_text=d.plate.plate_text,
                raw_text=d.plate.raw_text,
                ocr_confidence=d.plate.ocr_confidence,
                validation_status=d.plate.validation_status,
                plate_crop_path=d.plate.plate_crop_path,
                timestamp=d.plate.timestamp,
                camera_id=d.plate.camera_id
            )
        det_responses.append(DetectionResponse(
            id=d.id,
            detection_id=d.detection_id,
            camera_id=d.camera_id,
            tracker_id=d.tracker_id,
            frame_number=d.frame_number,
            timestamp=d.timestamp,
            vehicle_class=d.vehicle_class,
            confidence=d.confidence,
            bbox_x1=d.bbox_x1,
            bbox_y1=d.bbox_y1,
            bbox_x2=d.bbox_x2,
            bbox_y2=d.bbox_y2,
            color="UNKNOWN",
            color_confidence=0.8,
            speed_estimate=None,
            direction_heading="North",
            snapshot_path=d.snapshot_path,
            plate=p_resp
        ))

    traj_responses = [
        TrajectoryPoint(
            id=t.id,
            camera_id=t.camera_id,
            camera_name=topology_engine.get_camera(t.camera_id).get("name") if topology_engine.get_camera(t.camera_id) else t.camera_id,
            timestamp=t.timestamp,
            latitude=t.latitude,
            longitude=t.longitude,
            speed_kmh=t.speed_kmh,
            travel_time_from_prev_seconds=t.travel_time_from_prev_seconds,
            route_segment_from=t.route_segment_from,
            route_confidence=t.route_confidence,
            is_anomaly=t.is_anomaly
        ) for t in trajs
    ]

    return VehicleDetailResponse(
        id=vehicle.id,
        global_id=vehicle.global_id,
        primary_plate=vehicle.primary_plate,
        vehicle_type=vehicle.vehicle_type,
        color=vehicle.color,
        confidence=vehicle.confidence,
        first_seen=vehicle.first_seen,
        last_seen=vehicle.last_seen,
        total_sightings=vehicle.total_sightings,
        is_flagged=vehicle.is_flagged,
        notes=vehicle.notes,
        last_camera_id=vehicle.last_camera_id,
        last_seen_timestamp=vehicle.last_seen_timestamp,
        reid_decision=vehicle.reid_decision or "MATCH",
        reid_reason=vehicle.reid_reason,
        registered_data=reg_dict,
        trajectories=traj_responses,
        detections=det_responses
    )

@router.get("/{vehicle_id}/plates", response_model=List[PlateObservationItem])
def get_vehicle_plates(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all recorded plate observations associated with a vehicle or tracker ID.
    Supports lookups by numeric Vehicle ID, global_id, plate string, or local tracker_id.
    """
    v = None
    if vehicle_id.isdigit():
        v = db.query(Vehicle).filter(Vehicle.id == int(vehicle_id)).first()
    if not v:
        v = db.query(Vehicle).filter(
            (Vehicle.global_id == vehicle_id) | (Vehicle.primary_plate == vehicle_id)
        ).first()

    query = db.query(PlateRecord)
    if v and v.primary_plate and v.primary_plate != "UNKNOWN":
        query = query.filter(
            (PlateRecord.plate_text == v.primary_plate) |
            (PlateRecord.global_vehicle_id == v.global_id) |
            (PlateRecord.tracker_id == vehicle_id)
        )
    elif v:
        query = query.filter(
            (PlateRecord.global_vehicle_id == v.global_id) |
            (PlateRecord.tracker_id == vehicle_id)
        )
    else:
        query = query.filter(
            (PlateRecord.tracker_id == vehicle_id) |
            (PlateRecord.plate_text.ilike(f"%{vehicle_id.strip()}%"))
        )

    records = query.order_by(PlateRecord.timestamp.desc()).limit(100).all()

    return [
        PlateObservationItem(
            id=r.id,
            observation_id=r.observation_id,
            camera_id=r.camera_id,
            tracker_id=r.tracker_id,
            frame_number=r.frame_number,
            timestamp=r.timestamp.isoformat() if r.timestamp else None,
            plate_text=r.plate_text,
            raw_text=r.raw_text,
            ocr_confidence=r.ocr_confidence,
            detection_confidence=r.detection_confidence,
            validation_status=r.validation_status,
            plate_bbox=[r.plate_bbox_x1, r.plate_bbox_y1, r.plate_bbox_x2, r.plate_bbox_y2] if r.plate_bbox_x1 is not None else None,
            plate_crop_path=r.plate_crop_path,
            vehicle_type=r.vehicle_type,
            vehicle_color=r.vehicle_color,
            color_confidence=r.color_confidence
        ) for r in records
    ]


