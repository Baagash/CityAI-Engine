"""
Phase 5 Comprehensive Test Suite:
Advanced Multi-Camera Vehicle Re-Identification & Trajectory Intelligence.

Tests 20 core requirements:
1. Feature extractor initialization
2. Embedding generation
3. Embedding dimension
4. L2 normalization
5. Cosine similarity
6. Invalid embedding handling
7. Plate similarity
8. Vehicle attribute matching
9. Valid camera transition
10. Impossible travel detection
11. Appearance conflict
12. Unknown plate fallback
13. Composite score & explainable breakdown
14. MATCH decision
15. REVIEW_REQUIRED decision
16. REJECT decision
17. Local tracker ID vs global ID
18. API tests
19. Database persistence
20. Cross-camera Re-ID association workflow
"""

import pytest
import json
import uuid
import numpy as np
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal, init_db
from app.config import settings
from app.models.vehicle import Vehicle
from app.models.detection import DetectionRecord
from app.models.plate import PlateRecord
from app.models.reid import ReIDMatch
from app.models.trajectory import Trajectory
from app.models.registry import DemoRegistryVehicle
from app.services.appearance_embedding import appearance_extractor, AppearanceFeatureExtractor
from app.services.vehicle_reid import reid_service
from app.services.trajectory_engine import topology_engine

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    # Seed a demo registry entry for attribute conflict testing
    db = SessionLocal()
    try:
        reg = db.query(DemoRegistryVehicle).filter(DemoRegistryVehicle.registration_number == "TN38AB1234").first()
        if not reg:
            reg = DemoRegistryVehicle(
                registration_number="TN38AB1234",
                vehicle_type="sedan",
                make_model="Honda City",
                registered_color="BLUE",
                owner_name="R. Sundaram",
                status="ACTIVE"
            )
            db.add(reg)
            db.commit()
    finally:
        db.close()


# 1. Feature Extractor Initialization
def test_feature_extractor_initialization():
    extractor = AppearanceFeatureExtractor()
    assert extractor.embedding_dim == 512
    assert extractor.device == "cpu"
    assert extractor.model_name == "mobilenet_v3_small"
    assert extractor.is_available is True


# 2. Embedding Generation
def test_embedding_generation():
    extractor = AppearanceFeatureExtractor()
    synthetic_crop = np.random.randint(50, 200, (120, 160, 3), dtype=np.uint8)
    embedding = extractor.extract_embedding(synthetic_crop)
    
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.dtype == np.float32
    assert embedding.shape == (512,)


# 3. Embedding Dimension
def test_embedding_dimension():
    extractor = AppearanceFeatureExtractor()
    assert extractor.embedding_dim == 512
    dummy_crop = np.zeros((100, 100, 3), dtype=np.uint8)
    emb = extractor.extract_embedding(dummy_crop)
    assert emb.shape == (512,)


# 4. L2 Normalization (norm(v) ≈ 1.0)
def test_l2_normalization():
    extractor = AppearanceFeatureExtractor()
    sample_crop = np.full((150, 200, 3), 180, dtype=np.uint8)
    embedding = extractor.extract_embedding(sample_crop)
    
    norm = np.linalg.norm(embedding)
    assert np.isclose(norm, 1.0, atol=1e-5), f"Expected unit norm ~1.0, got {norm}"


# 5. Cosine Similarity (Identical, Orthogonal, Inverted)
def test_cosine_similarity():
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    # Identical vectors -> 1.0
    sim_identical = reid_service.compute_cosine_similarity(vec, vec)
    assert np.isclose(sim_identical, 1.0, atol=1e-5)

    # Orthogonal vectors -> 0.0
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b[1] = 1.0
    sim_ortho = reid_service.compute_cosine_similarity(vec_a, vec_b)
    assert np.isclose(sim_ortho, 0.0, atol=1e-5)

    # Inverted vectors -> -1.0
    vec_inv = -vec
    sim_inv = reid_service.compute_cosine_similarity(vec, vec_inv)
    assert np.isclose(sim_inv, -1.0, atol=1e-5)


# 6. Invalid Embedding Handling
def test_invalid_embedding_handling():
    extractor = AppearanceFeatureExtractor()
    # None crop -> zero vector
    zero_emb = extractor.extract_embedding(None)
    assert zero_emb.shape == (512,)
    assert np.all(zero_emb == 0.0)

    # Invalid dimension comparison
    wrong_dim = np.zeros(256, dtype=np.float32)
    right_dim = np.zeros(512, dtype=np.float32)
    assert reid_service.compute_cosine_similarity(wrong_dim, right_dim) == 0.0

    # Zero vector cosine similarity
    assert reid_service.compute_cosine_similarity(zero_emb, zero_emb) == 0.0


# 7. Plate Similarity
def test_plate_similarity():
    assert reid_service.compute_plate_similarity("TN38AB1234", "TN38AB1234") == 1.0
    assert reid_service.compute_plate_similarity("TN 38 AB 1234", "TN38AB1234") == 1.0
    assert reid_service.compute_plate_similarity("TN38AB1234", "TN38AB1235") > 0.85
    assert reid_service.compute_plate_similarity("UNKNOWN", "TN38AB1234") == 0.0
    assert reid_service.compute_plate_similarity(None, "TN38AB1234") == 0.0


# 8. Vehicle Attribute Matching (Type & Colour)
def test_vehicle_attribute_matching():
    # Identical
    assert reid_service.compute_type_match("sedan", "sedan") == 1.0
    assert reid_service.compute_color_similarity("WHITE", "WHITE") == 1.0

    # Compatible types
    assert reid_service.compute_type_match("sedan", "suv") == 0.75
    assert reid_service.compute_color_similarity("WHITE", "SILVER") == 0.75

    # Incompatible
    assert reid_service.compute_type_match("sedan", "bus") == 0.0
    assert reid_service.compute_type_match("motorcycle", "truck") == 0.0
    assert reid_service.compute_color_similarity("RED", "BLUE") == 0.0


# 9. Valid Camera Transition
def test_valid_camera_transition():
    # CAM01 to CAM02 (3.5 km, expected min transit 105s, 240s is typical)
    st_score, st_feasible, st_status = reid_service.compute_spatiotemporal_consistency(
        "CAM01", "CAM02", time_elapsed_sec=240.0
    )
    assert st_feasible is True
    assert st_score >= 0.85
    assert st_status == "FEASIBLE_TRANSIT"


# 10. Impossible Travel Detection (Teleportation Anomaly)
def test_impossible_travel_detection():
    # CAM01 to CAM02 in 10s implies 1260 km/h (Physically impossible roadway speed)
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-001",
        tracker_b="CAM02-TRK-001",
        time_elapsed_sec=10.0,
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="sedan",
        type_b="sedan",
        color_a="WHITE",
        color_b="WHITE"
    )
    assert res["decision"] == "REJECT"
    assert res["reason_code"] == "IMPOSSIBLE_TRAVEL_SPEED"
    assert res["spatiotemporal_feasible"] is False
    assert res["transit_status"] == "IMPOSSIBLE_TRAVEL_SPEED"


# 11. Appearance Conflict
def test_appearance_conflict():
    # Matching plate string but conflicting vehicle class
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-010",
        tracker_b="CAM02-TRK-020",
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="sedan",
        type_b="truck",
        color_a="WHITE",
        color_b="WHITE",
        time_elapsed_sec=240.0
    )
    assert res["decision"] == "REJECT"
    assert res["reason_code"] == "STRONG_APPEARANCE_CONFLICT"


# 12. Unknown Plate Fallback
def test_unknown_plate_fallback():
    # UNKNOWN plate string but identical visual appearance vectors and valid transit
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    res = reid_service.match_observations(
        embedding_a=vec,
        embedding_b=vec,
        plate_a="UNKNOWN",
        plate_b="UNKNOWN",
        type_a="sedan",
        type_b="sedan",
        color_a="WHITE",
        color_b="WHITE",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=240.0
    )
    assert res["decision"] == "MATCH"
    assert res["reason_code"] == "MATCHED"
    assert res["visual_similarity"] >= 0.99
    assert res["plate_similarity"] == 0.0


# 13. Composite Score & Explainable Breakdown
def test_composite_score_breakdown():
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    res = reid_service.match_observations(
        embedding_a=vec,
        embedding_b=vec,
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="sedan",
        type_b="sedan",
        color_a="WHITE",
        color_b="WHITE",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=240.0
    )
    assert "breakdown" in res
    breakdown = res["breakdown"]
    assert "appearance_similarity" in breakdown
    assert "plate_similarity" in breakdown
    assert "attribute_similarity" in breakdown
    assert "trajectory_score" in breakdown
    assert "composite_score" in breakdown
    assert breakdown["composite_score"] >= 0.80


# 14. MATCH Decision
def test_match_decision():
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    res = reid_service.match_observations(
        embedding_a=vec,
        embedding_b=vec,
        plate_a="TN38AB9999",
        plate_b="TN38AB9999",
        type_a="suv",
        type_b="suv",
        color_a="BLACK",
        color_b="BLACK",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=200.0
    )
    assert res["decision"] == "MATCH"
    assert res["reason_code"] == "MATCHED"


# 15. REVIEW_REQUIRED Decision
def test_review_required_decision():
    # Same plate number but conflicting color (White observed vs Blue)
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b[1] = 1.0

    res = reid_service.match_observations(
        embedding_a=vec_a,
        embedding_b=vec_b,
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="sedan",
        type_b="sedan",
        color_a="WHITE",
        color_b="BLUE",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=240.0
    )
    assert res["decision"] == "REVIEW_REQUIRED"
    assert res["reason_code"] in ["ATTRIBUTE_CONFLICT", "STRONG_APPEARANCE_CONFLICT"]


# 16. REJECT Decision
def test_reject_decision():
    res = reid_service.match_observations(
        plate_a="TN38AB1234",
        plate_b="KA01XY9999",
        type_a="sedan",
        type_b="truck",
        color_a="WHITE",
        color_b="RED",
        cam_a="CAM01",
        cam_b="CAM04",
        time_elapsed_sec=5.0
    )
    assert res["decision"] == "REJECT"


# 17. Local Tracker ID vs Global ID Separation
def test_local_tracker_id_vs_global_id():
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-017",
        tracker_b="CAM02-TRK-009",
        time_elapsed_sec=240.0
    )
    assert res["candidate_a"]["tracker_id"] == "CAM01-TRK-017"
    assert res["candidate_b"]["tracker_id"] == "CAM02-TRK-009"
    assert res["candidate_a"]["tracker_id"] != res["candidate_b"]["tracker_id"]


# 18. API Tests: Search, Detail, Match, Trajectories
def test_reid_api_endpoints():
    # 1. POST /api/vehicles/reid/match (Step 17)
    match_payload = {
        "camera_a": "CAM01",
        "camera_b": "CAM02",
        "tracker_a": "CAM01-TRK-017",
        "tracker_b": "CAM02-TRK-009",
        "plate_a": "TN38AB1234",
        "plate_b": "TN38AB1234",
        "vehicle_type_a": "sedan",
        "vehicle_type_b": "sedan",
        "color_a": "WHITE",
        "color_b": "WHITE",
        "time_elapsed_sec": 240.0
    }
    match_res = client.post("/api/vehicles/reid/match", json=match_payload)
    assert match_res.status_code == 200
    data = match_res.json()
    assert "appearance_similarity" in data
    assert "plate_similarity" in data
    assert "composite_score" in data
    assert "decision" in data
    assert "reason" in data
    assert "breakdown" in data

    # 2. GET /api/vehicles
    search_res = client.get("/api/vehicles?vehicle_type=sedan")
    assert search_res.status_code == 200
    assert isinstance(search_res.json(), list)

    # 3. GET /api/reid/stats
    stats_res = client.get("/api/reid/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "total_comparisons" in stats_data


# 19. Database Persistence for Vehicle, DetectionRecord, PlateRecord
def test_database_persistence():
    db = SessionLocal()
    try:
        test_gid = f"VEH-TEST-{uuid.uuid4().hex[:6].upper()}"
        v = Vehicle(
            global_id=test_gid,
            primary_plate="TN38TEST01",
            vehicle_type="sedan",
            color="WHITE",
            confidence=0.92,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc),
            total_sightings=1,
            last_camera_id="CAM01",
            last_seen_timestamp=datetime.now(timezone.utc),
            reid_decision="MATCH",
            reid_reason="INITIAL_CREATION",
            appearance_embedding=json.dumps([0.1] * 512)
        )
        db.add(v)
        db.commit()
        db.refresh(v)

        # Detection Record with global_vehicle_id
        det = DetectionRecord(
            detection_id=f"DET-TEST-{uuid.uuid4().hex[:8]}",
            camera_id="CAM01",
            tracker_id="CAM01-TRK-TEST",
            global_vehicle_id=test_gid,
            vehicle_id=v.id,
            frame_number=10,
            vehicle_class="sedan",
            confidence=0.90,
            bbox_x1=10, bbox_y1=10, bbox_x2=100, bbox_y2=100,
            center_x=55, center_y=55
        )
        db.add(det)

        # Plate Record with global_vehicle_id
        plt = PlateRecord(
            observation_id=f"PLT-TEST-{uuid.uuid4().hex[:8]}",
            camera_id="CAM01",
            tracker_id="CAM01-TRK-TEST",
            global_vehicle_id=test_gid,
            plate_text="TN38TEST01",
            ocr_confidence=0.95,
            validation_status="VALID_FORMAT",
            vehicle_type="sedan",
            vehicle_color="WHITE"
        )
        db.add(plt)
        db.commit()

        # Query and verify
        queried_v = db.query(Vehicle).filter(Vehicle.global_id == test_gid).first()
        assert queried_v is not None
        assert queried_v.primary_plate == "TN38TEST01"
        assert queried_v.last_camera_id == "CAM01"
        assert queried_v.reid_decision == "MATCH"

        queried_det = db.query(DetectionRecord).filter(DetectionRecord.global_vehicle_id == test_gid).first()
        assert queried_det is not None
        assert queried_det.tracker_id == "CAM01-TRK-TEST"

        queried_plt = db.query(PlateRecord).filter(PlateRecord.global_vehicle_id == test_gid).first()
        assert queried_plt is not None
        assert queried_plt.plate_text == "TN38TEST01"

        # Trajectory endpoint test for this vehicle
        traj_res = client.get(f"/api/vehicles/{test_gid}/trajectories")
        assert traj_res.status_code == 200

        # Cleanup
        db.delete(det)
        db.delete(plt)
        db.delete(queried_v)
        db.commit()
    finally:
        db.close()


# 20. Cross-Camera Re-ID Association Workflow (Step 22)
def test_cross_camera_reid_association_workflow():
    """
    Simulates:
    CAM01: Vehicle detected -> Local TRK-017 -> Creates VEH-XXXXXX
    CAM02: Plate unreadable (UNKNOWN) -> Visual Re-ID matches existing VEH-XXXXXX!
    """
    db = SessionLocal()
    try:
        vec = np.random.randn(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        # 1. CAM01 Observation (Initial sighting)
        t1 = datetime.now(timezone.utc) - timedelta(minutes=5)
        assoc1 = reid_service.associate_track_to_global_vehicle(
            db=db,
            camera_id="CAM01",
            tracker_id="CAM01-TRK-017",
            embedding=vec,
            plate_text="TN38FLOW01",
            vehicle_type="sedan",
            vehicle_color="WHITE",
            timestamp=t1
        )
        global_id_1 = assoc1["global_vehicle_id"]
        assert global_id_1.startswith("VEH-")
        assert assoc1["is_new_vehicle"] is True

        # 2. CAM02 Observation (Plate is UNKNOWN, same visual appearance, 4 mins later)
        t2 = datetime.now(timezone.utc) - timedelta(minutes=1)
        assoc2 = reid_service.associate_track_to_global_vehicle(
            db=db,
            camera_id="CAM02",
            tracker_id="CAM02-TRK-009",
            embedding=vec,
            plate_text="UNKNOWN",  # Unreadable plate fallback
            vehicle_type="sedan",
            vehicle_color="WHITE",
            timestamp=t2
        )
        global_id_2 = assoc2["global_vehicle_id"]

        # Expected: Successfully re-identified and merged into the existing Global Vehicle ID!
        assert global_id_1 == global_id_2
        assert assoc2["is_new_vehicle"] is False
        assert assoc2["decision"] == "MATCH"

        # Verify sightings incremented
        v_updated = db.query(Vehicle).filter(Vehicle.global_id == global_id_1).first()
        assert v_updated.total_sightings >= 2
        assert v_updated.last_camera_id == "CAM02"

        # Cleanup
        db.query(Trajectory).filter(Trajectory.vehicle_id == v_updated.id).delete()
        db.delete(v_updated)
        db.commit()
    finally:
        db.close()
