from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import TrafficAnalyticsSummary
from app.services.traffic_analytics import traffic_analytics
from app.services.weather_engine import weather_service
from app.models.vehicle import Vehicle
from app.models.alert import Alert

router = APIRouter(prefix="/analytics", tags=["Traffic Analytics"])

@router.get("/summary", response_model=TrafficAnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    """Provides high-level city traffic intelligence telemetry, congestion indexes, and volume statistics."""
    summary = traffic_analytics.get_city_analytics_summary(weather_service.current_weather)
    
    # Real-time counts from database
    total_vehicles = db.query(Vehicle).count()
    active_alerts = db.query(Alert).filter(Alert.status == "REQUIRES_VERIFICATION").count()
    critical_alerts = db.query(Alert).filter(
        Alert.status == "REQUIRES_VERIFICATION",
        Alert.severity == "CRITICAL"
    ).count()

    summary["total_vehicles_tracked"] = max(total_vehicles, summary["total_vehicles_tracked"])
    summary["active_alerts_count"] = active_alerts
    summary["critical_alerts_count"] = critical_alerts
    return summary
