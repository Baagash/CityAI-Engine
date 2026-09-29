from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.database import Base

class DemoRegistryVehicle(Base):
    __tablename__ = "demo_registry_vehicles"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(50), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # Sedan, SUV, Hatchback, Truck, Bus, Motorcycle
    make_model = Column(String(100), nullable=False)   # e.g., Honda City, Toyota Fortuner
    registered_color = Column(String(50), nullable=False)  # White, Black, Silver, Blue, Red
    owner_name = Column(String(100), nullable=False)
    registration_date = Column(String(50), default="2023-05-12")
    status = Column(String(50), default="ACTIVE")  # ACTIVE, STOLEN, SUSPENDED, EXPIRED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
