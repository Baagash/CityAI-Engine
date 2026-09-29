from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import json
from app.database import get_db
from app.models.investigation import InvestigationCase
from app.models.vehicle import Vehicle
from app.models.alert import Alert
from app.models.detection import Detection
from app.models.plate import Plate
from app.schemas.schemas import InvestigationCaseResponse, CaseCreate, CaseUpdate

router = APIRouter(prefix="/investigations", tags=["Investigation Cases"])

@router.get("", response_model=List[InvestigationCaseResponse])
def list_cases(db: Session = Depends(get_db)):
    """Lists all open and resolved investigation cases."""
    return db.query(InvestigationCase).order_by(InvestigationCase.updated_at.desc()).all()

@router.post("", response_model=InvestigationCaseResponse)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    """Creates a new formal investigation case."""
    case_num = f"CASE-2026-{datetime.utcnow().strftime('%m%d')}-{db.query(InvestigationCase).count() + 1:03d}"
    
    new_case = InvestigationCase(
        case_id=case_num,
        title=payload.title,
        assigned_officer=payload.assigned_officer,
        status="OPEN",
        priority=payload.priority,
        target_plate=payload.target_plate,
        target_vehicle_id=payload.target_vehicle_id,
        summary=payload.summary,
        evidence_ids=json.dumps(payload.evidence_ids) if payload.evidence_ids else "[]",
        notes=f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}] Case initialized by {payload.assigned_officer}."
    )
    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return new_case

@router.get("/{case_id}", response_model=InvestigationCaseResponse)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Retrieves case details by case_id."""
    case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")
    return case

@router.put("/{case_id}", response_model=InvestigationCaseResponse)
def update_case(case_id: str, payload: CaseUpdate, db: Session = Depends(get_db)):
    """Updates case status, summary, or appends officer notes."""
    case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")

    if payload.status:
        case.status = payload.status
    if payload.priority:
        case.priority = payload.priority
    if payload.summary:
        case.summary = payload.summary
    if payload.notes:
        existing_notes = case.notes or ""
        timestamp_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        case.notes = f"{existing_notes}\n[{timestamp_str}] {payload.notes}".strip()

    db.commit()
    db.refresh(case)
    return case

@router.get("/{case_id}/dossier")
def generate_case_dossier(case_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Generates a comprehensive official Intelligence Dossier JSON export with timeline,
    sighting audit logs, and evidence comparison metrics.
    """
    case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Investigation case not found")

    related_alerts = []
    if case.target_plate:
        alerts = db.query(Alert).filter(Alert.plate_text == case.target_plate).all()
        for a in alerts:
            related_alerts.append({
                "alert_id": a.alert_id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "description": a.description,
                "timestamp": a.timestamp.isoformat(),
                "status": a.status
            })

    related_detections = []
    if case.target_plate:
        dets = db.query(Detection).join(Plate).filter(Plate.plate_text == case.target_plate).order_by(Detection.timestamp.asc()).all()
        for d in dets:
            related_detections.append({
                "detection_id": d.detection_id,
                "camera_id": d.camera_id,
                "timestamp": d.timestamp.isoformat(),
                "vehicle_class": d.vehicle_class,
                "color": d.color,
                "speed_kmh": d.speed_estimate,
                "ocr_confidence": d.plate.ocr_confidence if d.plate else 0.9
            })

    return {
        "dossier_header": {
            "case_id": case.case_id,
            "title": case.title,
            "classification": "LAW ENFORCEMENT & TRAFFIC INTELLIGENCE EVIDENCE",
            "generated_at": datetime.utcnow().isoformat(),
            "assigned_officer": case.assigned_officer,
            "status": case.status,
            "priority": case.priority
        },
        "target_subject": {
            "plate_number": case.target_plate,
            "vehicle_id": case.target_vehicle_id,
            "total_recorded_sightings": len(related_detections)
        },
        "executive_summary": case.summary,
        "investigator_chronicle_notes": case.notes,
        "associated_alerts": related_alerts,
        "sighting_audit_timeline": related_detections,
        "legal_disclaimer": "This intelligence report represents automated computer vision observations and human-in-the-loop analyst notes. It serves as evidence-support documentation for authorized investigative review."
    }
