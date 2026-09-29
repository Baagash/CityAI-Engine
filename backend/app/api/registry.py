from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.registry import DemoRegistryVehicle
from app.schemas.schemas import RegistryVehicleResponse, RegistryVehicleCreate

router = APIRouter(prefix="/registry", tags=["Demo Vehicle Registry"])

@router.get("", response_model=List[RegistryVehicleResponse])
def list_registry(
    plate: Optional[str] = Query(None, description="Search plate"),
    status: Optional[str] = Query(None, description="ACTIVE, STOLEN, SUSPENDED"),
    db: Session = Depends(get_db)
):
    """Searches official Demo DMV/RTO registry database."""
    query = db.query(DemoRegistryVehicle)
    if plate:
        query = query.filter(DemoRegistryVehicle.registration_number.ilike(f"%{plate.strip()}%"))
    if status:
        query = query.filter(DemoRegistryVehicle.status == status.upper())
    return query.order_by(DemoRegistryVehicle.id.desc()).all()

@router.post("", response_model=RegistryVehicleResponse)
def add_registry_vehicle(payload: RegistryVehicleCreate, db: Session = Depends(get_db)):
    """Enrolls a vehicle in the Demo DMV database."""
    existing = db.query(DemoRegistryVehicle).filter(
        DemoRegistryVehicle.registration_number == payload.registration_number.upper()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Vehicle already registered in DMV database")

    new_reg = DemoRegistryVehicle(
        registration_number=payload.registration_number.upper(),
        vehicle_type=payload.vehicle_type,
        make_model=payload.make_model,
        registered_color=payload.registered_color.upper(),
        owner_name=payload.owner_name,
        registration_date=payload.registration_date or "2024-01-01",
        status=payload.status.upper(),
        notes=payload.notes
    )
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)
    return new_reg

@router.put("/{registration_number}/flag", response_model=RegistryVehicleResponse)
def flag_vehicle_status(registration_number: str, status: str = Query(..., description="ACTIVE, STOLEN, SUSPENDED"), db: Session = Depends(get_db)):
    """Flags a vehicle as STOLEN or SUSPENDED to test automatic alert triggering."""
    reg = db.query(DemoRegistryVehicle).filter(
        DemoRegistryVehicle.registration_number == registration_number.upper()
    ).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Vehicle not found in registry")

    reg.status = status.upper()
    db.commit()
    db.refresh(reg)
    return reg
