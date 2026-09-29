import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app
from app.database import init_db, check_db_status

@pytest.fixture(scope="module", autouse=True)
def setup_phase1():
    init_db()

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "PHASE" in data["phase"]
    assert "endpoints" in data

def test_system_health_endpoint_v1():
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "subsystems" in data
    assert data["subsystems"]["backend"]["status"] == "ONLINE"
    assert data["subsystems"]["backend"]["initialized"] is True
    assert data["subsystems"]["database"]["status"] == "CONNECTED"
    assert data["subsystems"]["ai_engine"]["status"] in ["READY", "ONLINE", "NOT INITIALIZED"]
    assert (

        "camera_service" in data["subsystems"] or 
        "camera_network" in data["subsystems"]
    )

def test_system_health_endpoint_api():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["subsystems"]["backend"]["status"] == "ONLINE"
    assert data["subsystems"]["database"]["status"] == "CONNECTED"

def test_database_status_check():
    status = check_db_status()
    assert status["connected"] is True
    assert status["status"] == "CONNECTED"
    assert status["dialect"] == "sqlite"
