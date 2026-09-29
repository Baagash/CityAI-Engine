import pytest
import numpy as np
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.database import SessionLocal, init_db
from app.models.reid import ReIDMatch
from app.services.vehicle_reid import reid_service, AppearanceFeatureExtractor
from app.config import settings

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()

# 1. Deterministic Embedding Shape & Extraction
def test_appearance_embedding_shape_and_type():
    extractor = AppearanceFeatureExtractor()
    sample_crop = np.random.randint(0, 255, (100, 150, 3), dtype=np.uint8)
    embedding = extractor.extract_embedding(sample_crop)
    
    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (512,)
    assert embedding.dtype == np.float32

# 2. L2 Normalization Test
def test_appearance_embedding_l2_normalization():
    extractor = AppearanceFeatureExtractor()
    sample_crop = np.full((120, 180, 3), 150, dtype=np.uint8)
    embedding = extractor.extract_embedding(sample_crop)
    
    norm = np.linalg.norm(embedding)
    assert np.isclose(norm, 1.0, atol=1e-5), f"Norm was {norm}, expected 1.0"

def test_empty_crop_embedding_returns_zero_vector():
    extractor = AppearanceFeatureExtractor()
    zero_emb = extractor.extract_embedding(None)
    assert zero_emb.shape == (512,)
    assert np.all(zero_emb == 0.0)

# 3. Cosine Similarity Calculations: Identical, Orthogonal, Inverted
def test_cosine_similarity_identical_vectors():
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    
    sim = reid_service.compute_cosine_similarity(vec, vec)
    assert np.isclose(sim, 1.0, atol=1e-5)

def test_cosine_similarity_orthogonal_vectors():
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b[1] = 1.0
    
    sim = reid_service.compute_cosine_similarity(vec_a, vec_b)
    assert np.isclose(sim, 0.0, atol=1e-5)

def test_cosine_similarity_opposite_vectors():
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b[0] = -1.0
    
    sim = reid_service.compute_cosine_similarity(vec_a, vec_b)
    assert np.isclose(sim, -1.0, atol=1e-5)

# 4. Spatiotemporal Transit Feasibility & Impossible Teleportation
def test_impossible_transit_teleportation():
    # CAM01 to CAM02 minimum transit time is 105s (at 120km/h cap)
    # Elapsed time of only 10s is physically impossible
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-001",
        tracker_b="CAM02-TRK-001",
        time_elapsed_sec=10.0,
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="car",
        type_b="car",
        color_a="WHITE",
        color_b="WHITE"
    )
    assert res["decision"] == "IMPOSSIBLE_TRANSIT"
    assert res["spatiotemporal_feasible"] is False
    assert res["transit_status"] == "IMPOSSIBLE_TRAVEL_SPEED"
    assert "physically impossible" in res["reason"]

def test_feasible_transit_window():
    # CAM01 to CAM02: 240s is well within plausible transit window
    st_score, st_feasible, st_status = reid_service.compute_spatiotemporal_consistency(
        "CAM01", "CAM02", time_elapsed_sec=240.0
    )
    assert st_feasible is True
    assert st_score >= 0.90
    assert st_status == "FEASIBLE_TRANSIT"

# 5. Conflicting Vehicle Attributes (Never Force Match)
def test_conflicting_vehicle_class_rejection():
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-010",
        tracker_b="CAM02-TRK-020",
        type_a="sedan",
        type_b="truck",
        color_a="WHITE",
        color_b="WHITE",
        time_elapsed_sec=300.0
    )
    assert res["decision"] == "NO_MATCH"
    assert "class mismatch" in res["reason"]
    assert res["vehicle_type_similarity"] == 0.0

def test_conflicting_vehicle_color_rejection():
    # Visually dissimilar crops
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0
    vec_b[1] = 1.0

    res = reid_service.match_observations(
        embedding_a=vec_a,
        embedding_b=vec_b,
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-011",
        tracker_b="CAM02-TRK-021",
        type_a="car",
        type_b="car",
        color_a="RED",
        color_b="BLUE",
        time_elapsed_sec=300.0
    )
    assert res["decision"] == "NO_MATCH"
    assert res["color_similarity"] == 0.0

# 6. Same Plate But Visually Different Vehicles (Anti-Spoofing / Cloned Plate Protection)
def test_same_plate_visually_inconsistent_not_matched():
    # Same plate number, but orthogonal visual appearance embeddings
    vec_a = np.zeros(512, dtype=np.float32)
    vec_b = np.zeros(512, dtype=np.float32)
    vec_a[0:100] = 1.0 / np.sqrt(100)
    vec_b[200:300] = 1.0 / np.sqrt(100)

    res = reid_service.match_observations(
        embedding_a=vec_a,
        embedding_b=vec_b,
        plate_a="TN38AB1234",
        plate_b="TN38AB1234",
        type_a="car",
        type_b="car",
        color_a="WHITE",
        color_b="BLACK",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=300.0
    )
    # The system must NOT declare a MATCH solely because plate strings match
    assert res["decision"] == "NO_MATCH"
    assert res["visual_similarity"] <= 0.10
    assert "cloned plate" in res["reason"] or "mismatch" in res["reason"]

# 7. Unknown Plate Re-ID (Visual + Attribute Matching)
def test_unknown_plate_reid_matching():
    # Same vehicle appearance vector, UNKNOWN plate
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    res = reid_service.match_observations(
        embedding_a=vec,
        embedding_b=vec,
        plate_a="UNKNOWN",
        plate_b="UNKNOWN",
        type_a="car",
        type_b="car",
        color_a="WHITE",
        color_b="WHITE",
        cam_a="CAM01",
        cam_b="CAM02",
        time_elapsed_sec=240.0
    )
    assert res["decision"] == "MATCH"
    assert res["visual_similarity"] >= 0.99
    assert res["plate_similarity"] == 0.0

# 8. Local Tracker ID Separation
def test_tracker_ids_remain_camera_local():
    res = reid_service.match_observations(
        cam_a="CAM01",
        cam_b="CAM02",
        tracker_a="CAM01-TRK-017",
        tracker_b="CAM02-TRK-004",
        time_elapsed_sec=250.0
    )
    assert res["candidate_a"]["tracker_id"] == "CAM01-TRK-017"
    assert res["candidate_b"]["tracker_id"] == "CAM02-TRK-004"
    assert res["candidate_a"]["tracker_id"] != res["candidate_b"]["tracker_id"]

# 9. Database Model Persistence for ReIDMatch
def test_reid_match_db_persistence():
    db = SessionLocal()
    try:
        match_id = f"REID-TEST-{int(datetime.now(timezone.utc).timestamp())}"
        rec = ReIDMatch(
            match_id=match_id,
            camera_a="CAM01",
            camera_b="CAM02",
            tracker_a="CAM01-TRK-001",
            tracker_b="CAM02-TRK-005",
            time_elapsed_sec=250.0,
            visual_similarity=0.88,
            vehicle_type_similarity=1.0,
            color_similarity=1.0,
            plate_similarity=1.0,
            spatiotemporal_feasible=True,
            composite_score=0.92,
            decision="MATCH",
            reason="High visual and spatiotemporal similarity"
        )
        db.add(rec)
        db.commit()

        queried = db.query(ReIDMatch).filter(ReIDMatch.match_id == match_id).first()
        assert queried is not None
        assert queried.decision == "MATCH"
        assert queried.visual_similarity == 0.88
        assert queried.tracker_a == "CAM01-TRK-001"
        assert queried.tracker_b == "CAM02-TRK-005"
        
        # Cleanup
        db.delete(queried)
        db.commit()
    finally:
        db.close()

# 10. REST API Endpoints: Compare, Matches, Stats
def test_api_reid_compare_endpoint():
    payload = {
        "camera_a": "CAM01",
        "camera_b": "CAM02",
        "tracker_a": "CAM01-TRK-017",
        "tracker_b": "CAM02-TRK-004",
        "plate_a": "TN38AB1234",
        "plate_b": "TN38AB1234",
        "type_a": "car",
        "type_b": "car",
        "color_a": "WHITE",
        "color_b": "WHITE",
        "time_elapsed_sec": 240.0,
        "save_result": True
    }
    res = client.post("/api/reid/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["decision"] in ["MATCH", "NO_MATCH", "UNCERTAIN", "IMPOSSIBLE_TRANSIT"]
    assert "visual_similarity" in data
    assert "composite_score" in data
    assert "reason" in data
    assert data["candidate_a"]["tracker_id"] == "CAM01-TRK-017"
    assert data["candidate_b"]["tracker_id"] == "CAM02-TRK-004"

def test_api_reid_matches_list():
    res = client.get("/api/reid/matches")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_api_reid_stats():
    res = client.get("/api/reid/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_comparisons" in data
    assert "matches_count" in data
    assert "no_matches_count" in data
    assert "uncertain_count" in data
    assert "impossible_transit_count" in data
    assert data["visual_threshold"] == settings.REID_VISUAL_SIMILARITY_THRESHOLD
