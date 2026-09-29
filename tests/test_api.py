import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app, seed_database
from app.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()
    seed_database()

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ONLINE", "HEALTHY"]
    assert "subsystems" in data
    assert data["subsystems"]["backend"]["status"] == "ONLINE"

def test_list_cameras():
    response = client.get("/api/v1/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert len(cameras) >= 4
    assert any(c["camera_id"] == "CAM01" for c in cameras)

def test_topology_endpoint():
    response = client.get("/api/v1/cameras/topology")
    assert response.status_code == 200
    edges = response.json()
    assert len(edges) >= 4

def test_camera_stats():
    response = client.get("/api/v1/cameras/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cameras"] >= 4

def test_detection_stats():
    response = client.get("/api/v1/detections/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "yolov8n.pt"
    assert "car" in data["supported_classes"]

def test_live_detections():
    response = client.get("/api/v1/detections/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "active_tracks" in data
