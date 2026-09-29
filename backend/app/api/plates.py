import cv2
import time
import numpy as np
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.config import settings
from app.models.plate import PlateRecord
from app.schemas.plate import (
    PlateObservationItem,
    PlateSearchResponse,
    VehicleAttributesItem,
    PlateStatsResponse,
    SinglePlateOCRResponse
)
from app.services.anpr import anpr_engine
from app.services.vehicle_attributes import attribute_service

router = APIRouter(prefix="/plates", tags=["ANPR & Plate Intelligence"])

@router.get("", response_model=List[PlateObservationItem])
def list_plate_observations(
    camera_id: Optional[str] = Query(None, description="Filter by camera ID"),
    validation_status: Optional[str] = Query(None, description="VALID_FORMAT, INVALID_FORMAT, UNKNOWN"),
    plate_text: Optional[str] = Query(None, description="Filter by plate substring"),
    vehicle_type: Optional[str] = Query(None, description="car, motorcycle, bus, truck"),
    vehicle_color: Optional[str] = Query(None, description="RED, BLUE, WHITE, BLACK, etc."),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieves recorded ANPR license plate observations with multi-modal filters.
    """
    query = db.query(PlateRecord)

    if camera_id:
        query = query.filter(PlateRecord.camera_id == camera_id.upper())
    if validation_status:
        query = query.filter(PlateRecord.validation_status == validation_status.upper())
    if plate_text:
        query = query.filter(PlateRecord.plate_text.ilike(f"%{plate_text.strip()}%"))
    if vehicle_type:
        query = query.filter(PlateRecord.vehicle_type == vehicle_type.lower())
    if vehicle_color:
        query = query.filter(PlateRecord.vehicle_color == vehicle_color.upper())

    records = query.order_by(PlateRecord.timestamp.desc()).offset(offset).limit(limit).all()
    
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

@router.get("/search", response_model=PlateSearchResponse)
def search_plates(
    q: str = Query(..., min_length=1, description="Plate query substring"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Searches plate observations by registration string or partial query.
    """
    cleaned_q = anpr_engine.clean_plate_text(q)
    query_str = cleaned_q if cleaned_q else q.strip().upper()

    query = db.query(PlateRecord).filter(
        (PlateRecord.plate_text.ilike(f"%{query_str}%")) |
        (PlateRecord.raw_text.ilike(f"%{query_str}%"))
    )
    total_count = query.count()
    records = query.order_by(PlateRecord.timestamp.desc()).limit(limit).all()

    matches = [
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

    return PlateSearchResponse(
        query=q,
        total_matches=total_count,
        matches=matches
    )

@router.get("/tracker/{tracker_id}", response_model=List[PlateObservationItem])
def get_tracker_plates(tracker_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all plate observations associated with a camera-local tracker ID.
    Note: Camera-local tracker IDs must NOT be treated as Global Vehicle IDs.
    """
    records = db.query(PlateRecord).filter(
        PlateRecord.tracker_id == tracker_id
    ).order_by(PlateRecord.timestamp.desc()).all()

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

@router.get("/stats", response_model=PlateStatsResponse)
def get_anpr_stats(db: Session = Depends(get_db)):
    """
    Returns operational statistics of the ANPR OCR Engine.
    """
    total_obs = db.query(PlateRecord).count()
    unique_plates = db.query(PlateRecord.plate_text).filter(PlateRecord.plate_text != "UNKNOWN").distinct().count()
    valid_count = db.query(PlateRecord).filter(PlateRecord.validation_status == "VALID_FORMAT").count()
    invalid_count = db.query(PlateRecord).filter(PlateRecord.validation_status == "INVALID_FORMAT").count()
    unknown_count = db.query(PlateRecord).filter(PlateRecord.validation_status == "UNKNOWN").count()

    return PlateStatsResponse(
        anpr_enabled=settings.ENABLE_ANPR,
        ocr_engine=anpr_engine.ocr_engine_name,
        ocr_version=anpr_engine.ocr_version,
        device=anpr_engine.device,
        total_observations_recorded=total_obs,
        unique_plates_count=unique_plates,
        valid_format_count=valid_count,
        invalid_format_count=invalid_count,
        unknown_count=unknown_count,
        supported_formats=[
            "Standard: SSNNXXNNNN (e.g. TN38AB1234, DL01CA1024, KA05MB9912)",
            "Single-Digit RTO: SSNXXNNNN (e.g. DL1CA1234)",
            "Bharat Series: YYBHNNNNXX (e.g. 22BH1234AA)",
            "Commercial/Short: SSNNNNNN (e.g. TN091234)"
        ]
    )

@router.post("/recognize", response_model=SinglePlateOCRResponse)
async def recognize_single_image(file: UploadFile = File(...)):
    """
    Executes instant real EasyOCR recognition on an uploaded vehicle or license plate image.
    Zero fabrication: uncertain images return UNKNOWN with 0.0 confidence.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image (JPEG, PNG, WEBP)."
        )

    content = await file.read()
    nparr = np.frombuffer(content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode uploaded image file."
        )

    start_time = time.perf_counter()
    
    # Extract color and attributes
    color, color_conf = attribute_service.extract_color(image)
    
    # Run OCR on plate ROI or direct image if already a plate banner
    h, w = image.shape[:2]
    aspect_ratio = w / max(1, h)
    if aspect_ratio >= 2.0:
        ocr_result = anpr_engine.recognize_plate(image)
    else:
        plate_roi, _ = anpr_engine.localize_plate_roi(image)
        ocr_result = anpr_engine.recognize_plate(plate_roi if plate_roi is not None else image)
        if ocr_result["plate_text"] == "UNKNOWN":
            # Fallback to full crop
            ocr_result = anpr_engine.recognize_plate(image)
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    return SinglePlateOCRResponse(
        status="SUCCESS",
        timestamp=datetime.now(timezone.utc).isoformat(),
        inference_ms=round(elapsed_ms, 2),
        plate_text=ocr_result["plate_text"],
        raw_text=ocr_result.get("raw_text"),
        ocr_confidence=ocr_result["ocr_confidence"],
        validation_status=ocr_result["validation_status"],
        is_valid_format=ocr_result["is_valid_format"],
        vehicle_attributes={
            "dominant_color": color,
            "color_confidence": color_conf,
            "resolution": f"{image.shape[1]}x{image.shape[0]}"
        }
    )

# Dedicated vehicle plates router for /api/vehicles/{vehicle_id}/plates
vehicle_router = APIRouter(prefix="/vehicles", tags=["Vehicles & Tracker Plates"])

@vehicle_router.get("/{vehicle_id}/plates", response_model=List[PlateObservationItem])
def get_vehicle_plates(vehicle_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all plate observations associated with a vehicle_id or tracker_id.
    Note: Camera-local tracker IDs must NOT be treated as Global Vehicle IDs.
    """
    records = db.query(PlateRecord).filter(
        (PlateRecord.tracker_id == vehicle_id) |
        (PlateRecord.plate_text.ilike(f"%{vehicle_id.strip()}%"))
    ).order_by(PlateRecord.timestamp.desc()).limit(100).all()

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

