import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.reid import ReIDMatch
from app.schemas.reid import (
    ReIDComparisonRequest,
    ReIDComparisonResponse,
    ReIDMatchRecordItem,
    ReIDStatsResponse,
    CandidateObservation
)
from app.services.vehicle_reid import reid_service

router = APIRouter(prefix="/reid", tags=["Vehicle Re-Identification (Phase 5)"])

@router.post("/compare", response_model=ReIDComparisonResponse)
def compare_vehicle_observations(
    req: ReIDComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Performs pairwise Vehicle Re-Identification comparison between two camera observations.
    Evaluates visual appearance embeddings, vehicle attributes, and camera graph spatiotemporal feasibility.
    Explicitly outputs: MATCH, NO_MATCH, UNCERTAIN, or IMPOSSIBLE_TRANSIT.
    Does NOT assign Global Vehicle Identities.
    """
    res = reid_service.match_observations(
        plate_a=req.plate_a,
        plate_b=req.plate_b,
        type_a=req.type_a or "UNKNOWN",
        type_b=req.type_b or "UNKNOWN",
        color_a=req.color_a or "UNKNOWN",
        color_b=req.color_b or "UNKNOWN",
        cam_a=req.camera_a,
        cam_b=req.camera_b,
        tracker_a=req.tracker_a,
        tracker_b=req.tracker_b,
        time_elapsed_sec=req.time_elapsed_sec
    )

    match_id = f"REID-{uuid.uuid4().hex[:10].upper()}"

    if req.save_result:
        try:
            match_rec = ReIDMatch(
                match_id=match_id,
                observation_a_id=req.observation_a_id,
                observation_b_id=req.observation_b_id,
                camera_a=req.camera_a.upper(),
                camera_b=req.camera_b.upper(),
                tracker_a=req.tracker_a,
                tracker_b=req.tracker_b,
                time_elapsed_sec=req.time_elapsed_sec,
                visual_similarity=res["visual_similarity"],
                vehicle_type_similarity=res["vehicle_type_similarity"],
                color_similarity=res["color_similarity"],
                plate_similarity=res["plate_similarity"],
                spatiotemporal_feasible=res["spatiotemporal_feasible"],
                composite_score=res["composite_score"],
                decision=res["decision"],
                reason=res["reason"]
            )
            db.add(match_rec)
            db.commit()
        except Exception as e:
            db.rollback()

    return ReIDComparisonResponse(
        match_id=match_id,
        decision=res["decision"],
        composite_score=res["composite_score"],
        visual_similarity=res["visual_similarity"],
        plate_similarity=res["plate_similarity"],
        vehicle_type_similarity=res["vehicle_type_similarity"],
        color_similarity=res["color_similarity"],
        spatiotemporal_score=res["spatiotemporal_score"],
        spatiotemporal_feasible=res["spatiotemporal_feasible"],
        transit_status=res["transit_status"],
        reason=res["reason"],
        candidate_a=CandidateObservation(**res["candidate_a"]),
        candidate_b=CandidateObservation(**res["candidate_b"]),
        time_elapsed_sec=res["time_elapsed_sec"]
    )

@router.get("/matches", response_model=List[ReIDMatchRecordItem])
def list_reid_matches(
    decision: Optional[str] = Query(None, description="Filter by decision: MATCH, NO_MATCH, UNCERTAIN, IMPOSSIBLE_TRANSIT"),
    camera_id: Optional[str] = Query(None, description="Filter by camera A or B"),
    tracker_id: Optional[str] = Query(None, description="Filter by local tracker ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Retrieves recorded pairwise Re-ID candidate match results.
    """
    query = db.query(ReIDMatch)
    if decision:
        query = query.filter(ReIDMatch.decision == decision.upper())
    if camera_id:
        c_upper = camera_id.upper()
        query = query.filter((ReIDMatch.camera_a == c_upper) | (ReIDMatch.camera_b == c_upper))
    if tracker_id:
        query = query.filter((ReIDMatch.tracker_a == tracker_id) | (ReIDMatch.tracker_b == tracker_id))

    records = query.order_by(ReIDMatch.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        ReIDMatchRecordItem(
            id=r.id,
            match_id=r.match_id,
            observation_a_id=r.observation_a_id,
            observation_b_id=r.observation_b_id,
            camera_a=r.camera_a,
            camera_b=r.camera_b,
            tracker_a=r.tracker_a,
            tracker_b=r.tracker_b,
            time_elapsed_sec=r.time_elapsed_sec,
            visual_similarity=r.visual_similarity,
            vehicle_type_similarity=r.vehicle_type_similarity,
            color_similarity=r.color_similarity,
            plate_similarity=r.plate_similarity,
            spatiotemporal_feasible=r.spatiotemporal_feasible,
            composite_score=r.composite_score,
            decision=r.decision,
            reason=r.reason,
            created_at=r.created_at.isoformat() if r.created_at else None
        ) for r in records
    ]

@router.get("/matches/{match_id}", response_model=ReIDMatchRecordItem)
def get_reid_match_detail(match_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a single Re-ID match decision record.
    """
    rec = db.query(ReIDMatch).filter(ReIDMatch.match_id == match_id).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Re-ID Match record '{match_id}' not found."
        )
    return ReIDMatchRecordItem(
        id=rec.id,
        match_id=rec.match_id,
        observation_a_id=rec.observation_a_id,
        observation_b_id=rec.observation_b_id,
        camera_a=rec.camera_a,
        camera_b=rec.camera_b,
        tracker_a=rec.tracker_a,
        tracker_b=rec.tracker_b,
        time_elapsed_sec=rec.time_elapsed_sec,
        visual_similarity=rec.visual_similarity,
        vehicle_type_similarity=rec.vehicle_type_similarity,
        color_similarity=rec.color_similarity,
        plate_similarity=rec.plate_similarity,
        spatiotemporal_feasible=rec.spatiotemporal_feasible,
        composite_score=rec.composite_score,
        decision=rec.decision,
        reason=rec.reason,
        created_at=rec.created_at.isoformat() if rec.created_at else None
    )

@router.get("/stats", response_model=ReIDStatsResponse)
def get_reid_stats(db: Session = Depends(get_db)):
    """
    Returns statistics of all Re-ID comparisons and decision categories.
    """
    total = db.query(ReIDMatch).count()
    matches = db.query(ReIDMatch).filter(ReIDMatch.decision == "MATCH").count()
    no_matches = db.query(ReIDMatch).filter(ReIDMatch.decision == "NO_MATCH").count()
    uncertain = db.query(ReIDMatch).filter(ReIDMatch.decision == "UNCERTAIN").count()
    impossible = db.query(ReIDMatch).filter(ReIDMatch.decision == "IMPOSSIBLE_TRANSIT").count()

    return ReIDStatsResponse(
        total_comparisons=total,
        matches_count=matches,
        no_matches_count=no_matches,
        uncertain_count=uncertain,
        impossible_transit_count=impossible,
        visual_threshold=settings.REID_VISUAL_SIMILARITY_THRESHOLD,
        composite_threshold=settings.REID_COMPOSITE_MATCH_THRESHOLD
    )
