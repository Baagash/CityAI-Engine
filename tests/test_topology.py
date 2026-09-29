import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.trajectory_engine import topology_engine

def test_topology_graph_nodes():
    cameras = topology_engine.get_all_cameras()
    assert len(cameras) >= 4
    cam_ids = [c["camera_id"] for c in cameras]
    assert "CAM01" in cam_ids
    assert "CAM02" in cam_ids
    assert "CAM03" in cam_ids
    assert "CAM04" in cam_ids

def test_inter_camera_distance():
    route = topology_engine.get_distance_and_transit("CAM01", "CAM02")
    assert route is not None
    assert route["distance_km"] == 3.5
    assert route["min_time_sec"] > 0

def test_impossible_speed_calculation():
    # 18km in 10 seconds -> ~6480 km/h -> IMPOSSIBLE
    dist_km, speed_kmh, is_impossible, explanation = topology_engine.calculate_inter_camera_speed(
        "CAM01", "CAM04", 10.0
    )
    assert is_impossible is True
    assert speed_kmh > 150.0
    assert "IMPOSSIBLE" in explanation

def test_normal_feasible_speed_calculation():
    # 3.5km in 300 seconds (5 mins) -> 42 km/h -> FEASIBLE
    dist_km, speed_kmh, is_impossible, explanation = topology_engine.calculate_inter_camera_speed(
        "CAM01", "CAM02", 300.0
    )
    assert is_impossible is False
    assert 35.0 <= speed_kmh <= 50.0
