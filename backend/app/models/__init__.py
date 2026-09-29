"""
Database Models Package for CityAI Traffic Intelligence
"""

from app.models.camera import Camera, CameraTopology
from app.models.detection import DetectionRecord, CameraTrack
from app.models.plate import PlateRecord, Plate
from app.models.reid import ReIDMatch

__all__ = ["Camera", "CameraTopology", "DetectionRecord", "CameraTrack", "PlateRecord", "Plate", "ReIDMatch"]

