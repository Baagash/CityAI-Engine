import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app, seed_demo_cameras_and_topology
from app.database import init_db, SessionLocal
from app.models.camera import Camera, CameraTopology
from app.services.video_processor import stream_manager

@pytest.fixture(scope="module", autouse=True)
def setup_phase2_db():
    init_db()
    seed_demo_cameras_and_topology()
    yield
    # Cleanup any active streams
    for cam_id in list(stream_manager._processors.keys()):
        stream_manager.stop_camera(cam_id)

client = TestClient(app)

def test_system_health_phase2():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "online"
    assert data["database"] == "connected"
    assert data["camera_service"] == "ready"
    assert data["ai_engine"] in ["ready", "online", "not_initialized"]
    assert "subsystems" in data
    assert data["subsystems"]["camera_service"]["status"] == "READY"
    assert data["subsystems"]["ai_engine"]["status"] in ["READY", "ONLINE", "NOT INITIALIZED"]


def test_list_demo_cameras():
    response = client.get("/api/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert len(cameras) >= 4
    cam_ids = [c["camera_id"] for c in cameras]
    assert "CAM01" in cam_ids
    assert "CAM02" in cam_ids
    assert "CAM03" in cam_ids
    assert "CAM04" in cam_ids
    
    cam1 = next(c for c in cameras if c["camera_id"] == "CAM01")
    assert cam1["is_demo"] is True
    assert cam1["source_type"] == "LOCAL_VIDEO"
    assert "Demo Junction North" in cam1["location_name"]

def test_get_single_camera():
    response = client.get("/api/cameras/CAM01")
    assert response.status_code == 200
    data = response.json()
    assert data["camera_id"] == "CAM01"
    assert data["zone"] == "Zone A - Downtown"
    assert data["direction"] == "NORTHBOUND"

def test_get_nonexistent_camera():
    response = client.get("/api/cameras/CAM_NONEXISTENT")
    assert response.status_code == 404

def test_create_and_delete_custom_camera():
    # 1. Create camera
    new_cam_payload = {
        "camera_id": "TEST_CAM99",
        "camera_name": "Test Interchange Station",
        "location_name": "Test Plaza Blvd",
        "latitude": 13.0500,
        "longitude": 80.2500,
        "zone": "Zone T - Test",
        "direction": "WESTBOUND",
        "source_type": "LOCAL_VIDEO",
        "local_video_path": "backend/videos/test.mp4",
        "description": "Automated pytest node",
        "is_demo": False
    }
    create_res = client.post("/api/cameras", json=new_cam_payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["camera_id"] == "TEST_CAM99"

    # 2. Duplicate camera creation should fail (409)
    dup_res = client.post("/api/cameras", json=new_cam_payload)
    assert dup_res.status_code == 409

    # 3. Update camera (PATCH)
    patch_res = client.patch("/api/cameras/TEST_CAM99", json={"camera_name": "Updated Test Plaza"})
    assert patch_res.status_code == 200
    assert patch_res.json()["camera_name"] == "Updated Test Plaza"

    # 4. Delete camera
    del_res = client.delete("/api/cameras/TEST_CAM99")
    assert del_res.status_code == 200

    # 5. Verify deletion
    verify_res = client.get("/api/cameras/TEST_CAM99")
    assert verify_res.status_code == 404

def test_camera_validation_errors():
    # Invalid coordinates
    invalid_coords = {
        "camera_id": "INVALID_COORD",
        "camera_name": "Bad Coords",
        "location_name": "Bad Location",
        "latitude": 120.0,  # Invalid: > 90
        "longitude": 80.0,
        "source_type": "LOCAL_VIDEO"
    }
    res = client.post("/api/cameras", json=invalid_coords)
    assert res.status_code == 422

    # Invalid source_type
    invalid_source = {
        "camera_id": "INVALID_SRC",
        "camera_name": "Bad Source",
        "location_name": "Bad Location",
        "latitude": 13.0,
        "longitude": 80.0,
        "source_type": "MICROWAVE_LINK"  # Unsupported
    }
    res2 = client.post("/api/cameras", json=invalid_source)
    assert res2.status_code == 422

def test_camera_topology_transitions():
    response = client.get("/api/cameras/topology")
    assert response.status_code == 200
    topology = response.json()
    assert len(topology) >= 4
    
    edges = [(t["source_camera_id"], t["destination_camera_id"]) for t in topology]
    assert ("CAM01", "CAM02") in edges
    assert ("CAM02", "CAM03") in edges
    assert ("CAM01", "CAM04") in edges
    assert ("CAM04", "CAM03") in edges

def test_camera_stats():
    response = client.get("/api/cameras/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cameras"] >= 4
    assert "online_cameras" in data
    assert "offline_cameras" in data
    assert "active_streams" in data

def test_camera_start_and_stop_stream():
    # Start CAM01
    start_res = client.post("/api/cameras/CAM01/start")
    assert start_res.status_code == 200
    assert start_res.json()["status"] == "SUCCESS"

    # Check status
    status_res = client.get("/api/cameras/CAM01/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["camera_id"] == "CAM01"
    assert status_data["is_streaming"] is True
    assert status_data["status"] == "ONLINE"
    assert status_data["fps"] > 0
    assert status_data["width"] > 0
    assert status_data["height"] > 0

    # Stop CAM01
    stop_res = client.post("/api/cameras/CAM01/stop")
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "SUCCESS"

    # Verify stopped status
    status_res2 = client.get("/api/cameras/CAM01/status")
    assert status_res2.status_code == 200
    assert status_res2.json()["is_streaming"] is False
    assert status_res2.json()["status"] == "STOPPED"

def test_start_nonexistent_camera():
    res = client.post("/api/cameras/UNKNOWN_CAM/start")
    assert res.status_code == 404
