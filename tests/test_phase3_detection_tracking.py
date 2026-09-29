import sys
import pytest
import numpy as np
import cv2
import io
from pathlib import Path
from fastapi.testclient import TestClient
from datetime import datetime, timezone

backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.main import app, seed_demo_cameras_and_topology
from app.config import settings
from app.database import init_db, SessionLocal
from app.models.detection import DetectionRecord, CameraTrack
from app.services.vehicle_detector import VehicleDetector, vehicle_detector, COCO_VEHICLE_CLASSES
from app.services.tracker import CameraObjectTracker, calculate_iou, TrackedVehicle
from app.services.video_processor import VideoProcessor, stream_manager

@pytest.fixture(scope="module", autouse=True)
def setup_phase3_db():
    init_db()
    seed_demo_cameras_and_topology()
    yield
    # Cleanup any active streams
    for cam_id in list(stream_manager._processors.keys()):
        stream_manager.stop_camera(cam_id)

client = TestClient(app)

# =========================================================================
# 1. Detector Initialization & Configuration Tests
# =========================================================================

def test_detector_initialization():
    """Validates that Ultralytics YOLO vehicle detector initializes cleanly with CPU fallback."""
    assert vehicle_detector.is_initialized is True
    assert vehicle_detector.model is not None
    assert vehicle_detector.device in ["cpu", "cuda", "cuda:0"]

def test_supported_vehicle_classes():
    """Verifies that only real vehicle classes (car, motorcycle, bus, truck) are targeted."""
    assert set(settings.SUPPORTED_VEHICLE_CLASSES) == {"car", "motorcycle", "bus", "truck"}
    assert 2 in COCO_VEHICLE_CLASSES and COCO_VEHICLE_CLASSES[2] == "car"
    assert 3 in COCO_VEHICLE_CLASSES and COCO_VEHICLE_CLASSES[3] == "motorcycle"
    assert 5 in COCO_VEHICLE_CLASSES and COCO_VEHICLE_CLASSES[5] == "bus"
    assert 7 in COCO_VEHICLE_CLASSES and COCO_VEHICLE_CLASSES[7] == "truck"

def test_detector_stats_structure():
    """Validates structure and data types of detector runtime telemetry."""
    stats = vehicle_detector.get_stats()
    assert "model_name" in stats
    assert "device" in stats
    assert "supported_classes" in stats
    assert "confidence_threshold" in stats
    assert isinstance(stats["avg_inference_ms"], float)
    assert isinstance(stats["processing_fps"], float)

# =========================================================================
# 2. Bounding Box & Inference Validation Tests
# =========================================================================

def test_synthetic_frame_detection_and_coordinates():
    """
    Feeds a synthetic image frame to detector and ensures no crashes,
    valid coordinate boundaries (0 <= x1 < x2 <= width), and valid confidence.
    """
    # Create a 640x360 test image
    test_img = np.zeros((360, 640, 3), dtype=np.uint8)
    # Draw simple vehicle shape
    cv2.rectangle(test_img, (100, 150), (250, 280), (120, 120, 120), -1)
    cv2.circle(test_img, (140, 280), 20, (30, 30, 30), -1)
    cv2.circle(test_img, (210, 280), 20, (30, 30, 30), -1)

    detections = vehicle_detector.detect(test_img, confidence_threshold=0.1)
    assert isinstance(detections, list)

    for det in detections:
        assert det["class"] in settings.SUPPORTED_VEHICLE_CLASSES
        assert 0.0 <= det["confidence"] <= 1.0
        x1, y1, x2, y2 = det["bbox"]
        assert 0 <= x1 < x2 <= 640
        assert 0 <= y1 < y2 <= 360
        cx, cy = det["center"]
        assert x1 <= cx <= x2
        assert y1 <= cy <= y2

def test_detect_from_bytes():
    """Tests byte buffer decoding and single-frame detection helper."""
    # Create test image and encode to JPEG
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    
    dets, meta = vehicle_detector.detect_from_bytes(buffer.tobytes())
    assert isinstance(dets, list)
    assert "inference_ms" in meta
    assert "resolution" in meta

def test_draw_hud_annotations():
    """Tests OpenCV HUD annotation rendering without mutating original shape."""
    img = np.zeros((360, 640, 3), dtype=np.uint8)
    dummy_tracks = [
        {
            "tracker_id": "CAM01-TRK-001",
            "display_id": "1",
            "vehicle_class": "car",
            "confidence": 0.92,
            "bbox": [100.0, 100.0, 200.0, 200.0],
            "trajectory_points": [{"cx": 150, "cy": 150}, {"cx": 155, "cy": 155}]
        }
    ]
    annotated = vehicle_detector.draw_hud_annotations(
        frame=img,
        tracks=dummy_tracks,
        camera_id="CAM01",
        fps=24.5
    )
    assert annotated.shape == img.shape
    assert isinstance(annotated, np.ndarray)

# =========================================================================
# 3. Multi-Object Tracking & Camera-Local Separation Tests
# =========================================================================

def test_iou_calculation():
    """Validates mathematical IoU metric."""
    box1 = [0.0, 0.0, 10.0, 10.0]
    box2 = [0.0, 0.0, 10.0, 10.0]
    assert calculate_iou(box1, box2) == 1.0

    box3 = [10.0, 10.0, 20.0, 20.0]
    assert calculate_iou(box1, box3) == 0.0

    box4 = [5.0, 0.0, 15.0, 10.0]  # Half overlap
    assert 0.3 < calculate_iou(box1, box4) < 0.4

def test_tracker_lifecycle_and_persistence():
    """Tests track creation, spatial update, and trajectory point accumulation."""
    tracker = CameraObjectTracker(camera_id="CAM01", iou_threshold=0.3, max_age=3)
    
    # Frame 1: Detection 1
    det_f1 = [{"bbox": [50.0, 50.0, 100.0, 100.0], "center": [75.0, 75.0], "class": "car", "confidence": 0.90}]
    tracks_f1 = tracker.update(det_f1, frame_number=1)
    assert len(tracks_f1) == 1
    t1 = tracks_f1[0]
    assert t1.track_id == 1
    assert t1.local_tracker_id == "CAM01-TRK-001"
    assert t1.total_frames == 1

    # Frame 2: Same object moved slightly
    det_f2 = [{"bbox": [53.0, 52.0, 103.0, 102.0], "center": [78.0, 77.0], "class": "car", "confidence": 0.91}]
    tracks_f2 = tracker.update(det_f2, frame_number=2)
    assert len(tracks_f2) == 1
    assert tracks_f2[0].track_id == 1
    assert tracks_f2[0].total_frames == 2
    assert len(tracks_f2[0].trajectory_points) == 2

def test_camera_local_tracker_separation():
    """
    CRITICAL REQUIREMENT:
    Validates that Camera CAM01 and Camera CAM02 maintain independent local tracker IDs.
    CAM01-TRK-001 must not conflict with CAM02-TRK-001.
    """
    tracker_cam1 = CameraObjectTracker(camera_id="CAM01")
    tracker_cam2 = CameraObjectTracker(camera_id="CAM02")

    det = [{"bbox": [100.0, 100.0, 200.0, 200.0], "center": [150.0, 150.0], "class": "car", "confidence": 0.88}]

    tracks_cam1 = tracker_cam1.update(det, frame_number=1)
    tracks_cam2 = tracker_cam2.update(det, frame_number=1)

    assert tracks_cam1[0].local_tracker_id == "CAM01-TRK-001"
    assert tracks_cam2[0].local_tracker_id == "CAM02-TRK-001"
    assert tracks_cam1[0].camera_id == "CAM01"
    assert tracks_cam2[0].camera_id == "CAM02"

# =========================================================================
# 4. Database Persistence Tests
# =========================================================================

def test_detection_record_persistence():
    """Tests saving and retrieving real DetectionRecord and CameraTrack in SQLite."""
    import uuid
    unique_det_id = f"DET-TEST-{uuid.uuid4().hex[:12].upper()}"
    db = SessionLocal()
    try:
        det_record = DetectionRecord(
            detection_id=unique_det_id,
            camera_id="CAM01",
            tracker_id="CAM01-TRK-001",
            frame_number=12,
            vehicle_class="truck",
            confidence=0.94,
            bbox_x1=50.0,
            bbox_y1=60.0,
            bbox_x2=150.0,
            bbox_y2=160.0,
            center_x=100.0,
            center_y=110.0,
            frame_width=640,
            frame_height=360
        )
        db.add(det_record)
        db.commit()

        # Query back
        saved = db.query(DetectionRecord).filter(DetectionRecord.detection_id == unique_det_id).first()
        assert saved is not None
        assert saved.camera_id == "CAM01"
        assert saved.vehicle_class == "truck"
        assert saved.confidence == 0.94
        assert saved.to_dict()["bbox"] == [50.0, 60.0, 150.0, 160.0]

    finally:
        db.close()

# =========================================================================
# 5. REST API Endpoints Tests
# =========================================================================

def test_api_detection_stats():
    """Tests GET /api/detections/stats"""
    response = client.get("/api/detections/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "yolov8n.pt"
    assert data["device"] in ["cpu", "cuda", "cuda:0"]
    assert "car" in data["supported_classes"]
    assert "active_tracks_count" in data
    assert "total_detections_recorded" in data

def test_api_live_detections():
    """Tests GET /api/detections/live"""
    response = client.get("/api/detections/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "active_tracks" in data
    assert "recent_detections" in data
    assert "hardware" in data

def test_api_historical_detections_with_filters():
    """Tests GET /api/detections with query filters."""
    response = client.get("/api/detections?camera_id=CAM01&vehicle_class=truck")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["camera_id"] == "CAM01"
        assert data[0]["vehicle_class"] == "truck"

def test_api_camera_tracks():
    """Tests GET /api/detections/tracks and /api/detections/tracks/CAM01"""
    res1 = client.get("/api/detections/tracks")
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    res2 = client.get("/api/detections/tracks/CAM01")
    assert res2.status_code == 200
    assert isinstance(res2.json(), list)

def test_api_single_image_detect_endpoint():
    """Tests POST /api/detections/detect with real image file upload."""
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    file_bytes = io.BytesIO(buffer.tobytes())

    response = client.post(
        "/api/detections/detect",
        files={"file": ("test.jpg", file_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "inference_ms" in data
    assert "total_vehicles_detected" in data
    assert "detections" in data

def test_api_annotated_stream_endpoint():
    """Tests real-time AI annotated MJPEG stream generation."""
    import time
    # 1. Start CAM01
    start_res = client.post("/api/cameras/CAM01/start")
    assert start_res.status_code == 200
    time.sleep(0.3)

    # 2. Test Stream Generator directly with annotated=True
    gen = stream_manager.generate_mjpeg_stream("CAM01", annotated=True)
    first_chunk = next(gen)
    assert b"--frame" in first_chunk
    assert b"Content-Type: image/jpeg" in first_chunk

    # 3. Test Status endpoint
    status_res = client.get("/api/cameras/CAM01/status")
    assert status_res.status_code == 200
    assert status_res.json()["is_streaming"] is True

    # 4. Cleanup
    client.post("/api/cameras/CAM01/stop")



def test_invalid_video_source_handling():
    """Validates graceful error reporting when video source is invalid."""
    proc = VideoProcessor(camera_id="CAM_BAD", source_type="LOCAL_VIDEO", source_path="nonexistent_video.mp4")
    success = proc.start()
    assert success is False
    assert proc.status == "ERROR"
    assert "not found" in proc.error_message.lower()
    proc.release()
