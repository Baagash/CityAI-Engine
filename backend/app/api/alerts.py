from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.alert import Alert
from app.models.investigation import InvestigationCase
from app.schemas.schemas import AlertResponse, AlertReviewRequest

router = APIRouter(prefix="/alerts", tags=["Alerts & Human Verification"])

@router.get("", response_model=List[AlertResponse])
def list_alerts(
    severity: Optional[str] = Query(None, description="CRITICAL, WARNING, INFO"),
    status: Optional[str] = Query(None, description="REQUIRES_VERIFICATION, VERIFIED_ANOMALY, DISMISSED_FALSE_POSITIVE, UNDER_INVESTIGATION"),
    alert_type: Optional[str] = Query(None, description="POSSIBLE_DUPLICATE_PLATE, IMPOSSIBLE_TRAVEL, REGISTRY_MISMATCH"),
    db: Session = Depends(get_db)
):
    """Retrieves alerts requiring human-in-the-loop verification and historical decisions."""
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if status:
        query = query.filter(Alert.status == status.upper())
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)

    alerts = query.order_by(Alert.timestamp.desc()).limit(100).all()
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Fetches full details of a specific alert with correlation JSON payload."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/{alert_id}/review", response_model=AlertResponse)
def review_alert(alert_id: str, payload: AlertReviewRequest, db: Session = Depends(get_db)):
    """
    Human-In-The-Loop action endpoint:
    Allows authorized officer to verify anomaly, dismiss as false positive, or mark under investigation.
    """
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = payload.status
    alert.reviewed_by = payload.reviewed_by
    alert.reviewed_at = datetime.utcnow()
    alert.review_notes = payload.review_notes

    # If verified or under investigation, optionally create linked case
    if payload.status in ["VERIFIED_ANOMALY", "UNDER_INVESTIGATION"]:
        existing_case = db.query(InvestigationCase).filter(InvestigationCase.target_plate == alert.plate_text).first()
        if not existing_case:
            new_case = InvestigationCase(
                case_id=f"CASE-2026-{alert.alert_id[-4:]}",
                title=f"Investigation: {alert.title}",
                assigned_officer=payload.reviewed_by,
                status="OPEN",
                priority="HIGH" if alert.severity == "CRITICAL" else "MEDIUM",
                target_plate=alert.plate_text,
                summary=f"Case opened following officer review of alert {alert.alert_id}: {alert.description}",
                notes=f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] Reviewer Note: {payload.review_notes or 'Initial verification complete.'}"
            )
            db.add(new_case)

    db.commit()
    db.refresh(alert)
    return alert
