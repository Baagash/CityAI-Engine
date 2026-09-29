import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.vehicle_reid import reid_service

def test_identical_vehicle_reid():
    res = reid_service.match_vehicles(
        plate_a="TN38AB1234", type_a="sedan", color_a="WHITE", cam_a="CAM01",
        plate_b="TN38AB1234", type_b="sedan", color_b="WHITE", cam_b="CAM02",
        time_elapsed_sec=300.0
    )
    assert res["overall_match_confidence"] >= 0.85
    assert res["classification"] == "HIGH CONFIDENCE MATCH"
    assert res["plate_similarity"] == 1.0
    assert res["type_match"] == 1.0
    assert res["colour_similarity"] == 1.0

def test_conflicting_color_and_type_reid():
    res = reid_service.match_vehicles(
        plate_a="TN38AB1234", type_a="sedan", color_a="WHITE", cam_a="CAM01",
        plate_b="TN38AB1234", type_b="truck", color_b="BLACK", cam_b="CAM04",
        time_elapsed_sec=120.0
    )
    assert res["overall_match_confidence"] < 0.70
    assert res["classification"] in ["PROBABLE MATCH", "UNCERTAIN MATCH"]
    assert res["colour_similarity"] == 0.0
    assert res["type_match"] == 0.0
