import io
import cv2
import numpy as np
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.database import SessionLocal, init_db
from app.models.plate import PlateRecord
from app.services.anpr import anpr_engine, ANPREngine
from app.services.vehicle_attributes import attribute_service, VehicleAttributeService
from app.services.tracker import TrackedVehicle, CameraObjectTracker
from app.services.vehicle_detector import vehicle_detector

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Initializes DB schema before running Phase 4 tests."""
    init_db()

# 1. ANPR Engine Initialization & Metadata Tests
def test_anpr_engine_initialization():
    assert anpr_engine is not None
    assert anpr_engine.ocr_engine_name == "EasyOCR"
    assert anpr_engine.ocr_version is not None
    assert anpr_engine.device in ["cpu", "cuda"]

# 2. Preprocessing Tests
def test_preprocess_plate_transformations():
    # Synthetic small test image
    sample_img = np.full((30, 80, 3), 120, dtype=np.uint8)
    processed = anpr_engine.preprocess_plate(sample_img)
    
    assert processed is not None
    assert len(processed.shape) == 2  # Grayscale
    assert processed.shape[1] >= 160  # Scaled for OCR resolution
    assert processed.dtype == np.uint8

def test_preprocess_plate_empty_handling():
    empty = np.array([])
    assert anpr_engine.preprocess_plate(empty).size == 0
    assert anpr_engine.preprocess_plate(None) is None

# 3. Clean Text Tests
def test_clean_plate_text():
    assert anpr_engine.clean_plate_text("TN 38 AB 1234") == "TN38AB1234"
    assert anpr_engine.clean_plate_text("dl-01-ca-1024") == "DL01CA1024"
    assert anpr_engine.clean_plate_text("ka.05.mb.9912") == "KA05MB9912"
    assert anpr_engine.clean_plate_text("") == ""
    assert anpr_engine.clean_plate_text(None) == ""

# 4. Indian Plate Validation Regex Tests
def test_plate_validation_indian_formats():
    # Valid Standard Formats
    assert anpr_engine.validate_plate("TN38AB1234") == "VALID_FORMAT"
    assert anpr_engine.validate_plate("KA05MB9912") == "VALID_FORMAT"
    assert anpr_engine.validate_plate("DL01CA1024") == "VALID_FORMAT"
    assert anpr_engine.validate_plate("MH12DE1433") == "VALID_FORMAT"
    assert anpr_engine.validate_plate("DL1CA1234") == "VALID_FORMAT"
    
    # Valid Bharat Series
    assert anpr_engine.validate_plate("22BH1234AA") == "VALID_FORMAT"
    
    # Valid Short / Commercial Series
    assert anpr_engine.validate_plate("TN091234") == "VALID_FORMAT"

    # Invalid Formats
    assert anpr_engine.validate_plate("INVALIDTEXT123") == "INVALID_FORMAT"
    assert anpr_engine.validate_plate("1234567") == "INVALID_FORMAT"
    assert anpr_engine.validate_plate("ABCDE") == "INVALID_FORMAT"
    assert anpr_engine.validate_plate("XYZ99") == "INVALID_FORMAT"

    # Unknown / Empty
    assert anpr_engine.validate_plate("") == "UNKNOWN"
    assert anpr_engine.validate_plate("UNKNOWN") == "UNKNOWN"
    assert anpr_engine.validate_plate(None) == "UNKNOWN"

# 5. Zero Fabrication & Uncertain Image OCR Handling
def test_uncertain_blank_image_returns_unknown():
    # Pure noise/blank image should NOT fabricate a registration string
    noise_img = np.random.randint(0, 255, (50, 150, 3), dtype=np.uint8)
    result = anpr_engine.recognize_plate(noise_img)
    
    assert isinstance(result, dict)
    assert "plate_text" in result
    assert "ocr_confidence" in result
    assert "validation_status" in result
    assert result["plate_text"] in ["UNKNOWN", ""] or result["ocr_confidence"] < 0.50

def test_empty_image_returns_unknown():
    result = anpr_engine.recognize_plate(None)
    assert result["plate_text"] == "UNKNOWN"
    assert result["ocr_confidence"] == 0.0
    assert result["validation_status"] == "UNKNOWN"
    assert result["is_valid_format"] is False

# 6. Real EasyOCR on Synthetic High-Contrast Plate Banner
def test_real_plate_ocr_synthetic_plate():
    if not anpr_engine.is_initialized:
        pytest.skip("EasyOCR reader not initialized in this environment")

    # Generate synthetic license plate banner with crisp black text on white background
    plate_canvas = np.full((100, 320, 3), 255, dtype=np.uint8)
    # Border
    cv2.rectangle(plate_canvas, (6, 6), (314, 94), (0, 0, 0), 4)
    # Clear text
    cv2.putText(
        plate_canvas,
        "TN38AB1234",
        (22, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.4,
        (0, 0, 0),
        3,
        cv2.LINE_AA
    )

    result = anpr_engine.recognize_plate(plate_canvas)
    assert result is not None
    assert result["plate_text"] != ""
    assert result["ocr_confidence"] > 0.0
    # EasyOCR should read letters/numbers from high-res synthetic plate
    assert "TN" in result["plate_text"] or "38" in result["plate_text"] or "1234" in result["plate_text"]

# 7. Vehicle Attributes: HSV Color Extraction
def test_vehicle_color_extraction_pure_colors():
    # Pure Red patch
    red_patch = np.zeros((100, 100, 3), dtype=np.uint8)
    red_patch[:, :] = (0, 0, 220)  # BGR Red
    color, conf = attribute_service.extract_color(red_patch)
    assert color == "RED"
    assert conf > 0.5

    # Pure Blue patch
    blue_patch = np.zeros((100, 100, 3), dtype=np.uint8)
    blue_patch[:, :] = (220, 0, 0)  # BGR Blue
    color, conf = attribute_service.extract_color(blue_patch)
    assert color == "BLUE"
    assert conf > 0.5

    # Pure White patch
    white_patch = np.full((100, 100, 3), 250, dtype=np.uint8)
    color, conf = attribute_service.extract_color(white_patch)
    assert color in ["WHITE", "SILVER"]
    assert conf > 0.5

    # Pure Black patch
    black_patch = np.full((100, 100, 3), 10, dtype=np.uint8)
    color, conf = attribute_service.extract_color(black_patch)
    assert color == "BLACK"
    assert conf > 0.5

def test_vehicle_color_extraction_empty():
    color, conf = attribute_service.extract_color(None)
    assert color == "UNKNOWN"
    assert conf == 0.0

# 8. TrackedVehicle ANPR State Integration
def test_tracked_vehicle_anpr_state():
    det = {"class": "car", "confidence": 0.88, "bbox": [50.0, 50.0, 200.0, 150.0], "center": [125.0, 100.0]}
    track = TrackedVehicle(track_id=17, camera_id="CAM01", detection=det, frame_number=1)

    assert track.local_tracker_id == "CAM01-TRK-017"
    assert track.plate_text == "UNKNOWN"
    assert track.vehicle_color == "UNKNOWN"

    track.update_anpr_and_attributes(
        plate_text="TN38AB1234",
        ocr_confidence=0.92,
        validation_status="VALID_FORMAT",
        vehicle_color="WHITE",
        color_confidence=0.85,
        raw_text="TN 38 AB 1234",
        frame_number=5
    )

    assert track.plate_text == "TN38AB1234"
    assert track.ocr_confidence == 0.92
    assert track.validation_status == "VALID_FORMAT"
    assert track.vehicle_color == "WHITE"

    d = track.to_dict()
    assert d["plate_text"] == "TN38AB1234"
    assert d["vehicle_color"] == "WHITE"
    assert d["ocr_confidence"] == 0.92

# 9. Database Model Persistence
def test_plate_record_persistence():
    db = SessionLocal()
    try:
        obs_id = f"PLT-TEST-{int(datetime.now(timezone.utc).timestamp())}"
        rec = PlateRecord(
            observation_id=obs_id,
            camera_id="CAM01",
            tracker_id="CAM01-TRK-042",
            frame_number=100,
            plate_text="KA05MB9912",
            raw_text="KA 05 MB 9912",
            ocr_confidence=0.94,
            detection_confidence=0.89,
            validation_status="VALID_FORMAT",
            vehicle_type="car",
            vehicle_color="BLUE",
            color_confidence=0.88
        )
        db.add(rec)
        db.commit()

        queried = db.query(PlateRecord).filter(PlateRecord.observation_id == obs_id).first()
        assert queried is not None
        assert queried.plate_text == "KA05MB9912"
        assert queried.vehicle_color == "BLUE"
        assert queried.validation_status == "VALID_FORMAT"
        
        # Cleanup
        db.delete(queried)
        db.commit()
    finally:
        db.close()

# 10. HUD Overlay Rendering with Plate and Unknown
def test_hud_annotations_plate_formatting():
    frame = np.full((360, 640, 3), 30, dtype=np.uint8)
    
    # Track with known plate
    det1 = {"class": "car", "confidence": 0.90, "bbox": [100.0, 100.0, 250.0, 220.0], "center": [175.0, 160.0]}
    t1 = TrackedVehicle(track_id=1, camera_id="CAM01", detection=det1, frame_number=1)
    t1.update_anpr_and_attributes(
        plate_text="TN38AB1234",
        ocr_confidence=0.96,
        validation_status="VALID_FORMAT",
        vehicle_color="WHITE",
        color_confidence=0.88
    )

    # Track with unknown plate
    det2 = {"class": "bus", "confidence": 0.85, "bbox": [350.0, 120.0, 550.0, 300.0], "center": [450.0, 210.0]}
    t2 = TrackedVehicle(track_id=2, camera_id="CAM01", detection=det2, frame_number=1)

    annotated = vehicle_detector.draw_hud_annotations(
        frame=frame,
        tracks=[t1, t2],
        camera_id="CAM01",
        fps=25.0
    )

    assert annotated is not None
    assert annotated.shape == (360, 640, 3)
    # Frame should have modified pixels from bounding boxes and text
    assert not np.array_equal(frame, annotated)

# 11. REST API Endpoint Tests
def test_api_list_plates():
    res = client.get("/api/plates")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_search_plates():
    res = client.get("/api/plates/search?q=TN")
    assert res.status_code == 200
    data = res.json()
    assert "query" in data
    assert "total_matches" in data
    assert "matches" in data

def test_api_tracker_plates():
    res = client.get("/api/plates/tracker/CAM01-TRK-999")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_plate_stats():
    res = client.get("/api/plates/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["anpr_enabled"] is True
    assert data["ocr_engine"] == "EasyOCR"
    assert "supported_formats" in data
    assert len(data["supported_formats"]) > 0

def test_api_single_image_recognize():
    # Create test image bytes
    test_img = np.full((120, 300, 3), 255, dtype=np.uint8)
    cv2.putText(test_img, "DL01CA1024", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    _, encoded = cv2.imencode(".jpg", test_img)
    
    res = client.post(
        "/api/plates/recognize",
        files={"file": ("test_plate.jpg", io.BytesIO(encoded.tobytes()), "image/jpeg")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "plate_text" in data
    assert "ocr_confidence" in data
    assert "validation_status" in data
    assert "vehicle_attributes" in data

def test_api_system_health_phase4():
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert "subsystems" in data
    assert "anpr_engine" in data["subsystems"]
    assert data["subsystems"]["anpr_engine"]["phase"] == 4
    assert data["subsystems"]["anpr_engine"]["status"] in ["READY", "CPU_FALLBACK"]

def test_api_vehicles_plates_endpoint():
    # Test vehicles/{id}/plates lookup
    res = client.get("/api/vehicles/1/plates")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res_v1 = client.get("/api/v1/vehicles/CAM01-TRK-001/plates")
    assert res_v1.status_code == 200
    assert isinstance(res_v1.json(), list)

def test_missing_model_fallback_safety():
    # If OCR engine is in fallback or reader is None
    dummy_engine = ANPREngine()
    dummy_engine._ocr_reader = None
    res = dummy_engine.recognize_plate(np.zeros((50, 100, 3), dtype=np.uint8))
    assert res["plate_text"] == "UNKNOWN"
    assert res["ocr_confidence"] == 0.0
    assert res["validation_status"] == "UNKNOWN"
    assert res["is_valid_format"] is False

