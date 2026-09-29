import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.duplicate_plate import duplicate_plate_engine

def test_detect_cloned_plate_visual_mismatch():
    now = datetime.utcnow()
    new_obs = {
        "camera_id": "CAM04",
        "timestamp": now,
        "vehicle_type": "suv",
        "color": "BLACK",
        "plate_text": "TN38AB1234",
        "confidence": 0.95
    }
    hist_obs = [{
        "camera_id": "CAM01",
        "timestamp": now - timedelta(seconds=60),
        "vehicle_type": "sedan",
        "color": "WHITE",
        "plate_text": "TN38AB1234",
        "ocr_confidence": 0.96
    }]

    alert = duplicate_plate_engine.analyze_sighting(new_obs, hist_obs)
    assert alert is not None
    assert alert["alert_type"] == "POSSIBLE_DUPLICATE_PLATE"
    assert alert["severity"] == "CRITICAL"
    assert "REQUIRES_VERIFICATION" == alert["status"]
    assert "POSSIBLE DUPLICATE / CLONED PLATE" in alert["title"]

def test_detect_impossible_travel_teleportation():
    now = datetime.utcnow()
    new_obs = {
        "camera_id": "CAM04",
        "timestamp": now,
        "vehicle_type": "sedan",
        "color": "WHITE",
        "plate_text": "KA05MB9912",
        "confidence": 0.95
    }
    hist_obs = [{
        "camera_id": "CAM01",
        "timestamp": now - timedelta(seconds=10),  # 18km in 10s is impossible
        "vehicle_type": "sedan",
        "color": "WHITE",
        "plate_text": "KA05MB9912",
        "ocr_confidence": 0.95
    }]

    alert = duplicate_plate_engine.analyze_sighting(new_obs, hist_obs)
    assert alert is not None
    assert alert["alert_type"] == "IMPOSSIBLE_TRAVEL"
    assert alert["severity"] == "CRITICAL"
