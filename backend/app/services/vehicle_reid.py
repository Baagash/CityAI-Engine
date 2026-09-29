"""
Vehicle Re-Identification (Re-ID) Engine (Phase 5).
Combines visual appearance embeddings, license plate similarity, vehicle type/color attributes,
and camera network spatiotemporal graph topology.

Produces 3-state decisions:
- MATCH
- REVIEW_REQUIRED
- REJECT

Reason codes:
- MATCHED
- LOW_CONFIDENCE
- ATTRIBUTE_CONFLICT
- STRONG_APPEARANCE_CONFLICT
- IMPOSSIBLE_TRAVEL_SPEED
- NO_PLAUSIBLE_CANDIDATE
- INVALID_EMBEDDING
- PLATE_MISMATCH
"""

import difflib
import time
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple, Optional, List, Union
import numpy as np

from app.config import settings
from app.services.trajectory_engine import topology_engine
from app.services.appearance_embedding import appearance_extractor, AppearanceFeatureExtractor
from app.models.vehicle import Vehicle
from app.models.trajectory import Trajectory
from app.models.reid import ReIDMatch
from app.models.registry import DemoRegistryVehicle

logger = logging.getLogger("cityai.reid")


class VehicleReIDService:
    """
    Advanced Multi-Camera Vehicle Re-Identification Engine.
    Correlates observations across different cameras using visual appearance embeddings,
    vehicle type/color attributes, license plate strings, and spatiotemporal network feasibility.
    """

    def __init__(self):
        self.feature_extractor = appearance_extractor
        
        # Configurable weights for multi-modal evidence fusion (Step 7)
        self.weight_visual = settings.REID_WEIGHT_VISUAL              # 0.40
        self.weight_plate = settings.REID_WEIGHT_PLATE                # 0.30
        self.weight_attributes = settings.REID_WEIGHT_ATTRIBUTES      # 0.15
        self.weight_spatiotemporal = settings.REID_WEIGHT_SPATIOTEMPORAL  # 0.15
        
        # Configurable thresholds
        self.visual_similarity_threshold = settings.REID_VISUAL_SIMILARITY_THRESHOLD  # 0.75
        self.composite_match_threshold = settings.REID_COMPOSITE_MATCH_THRESHOLD      # 0.80

    def compute_cosine_similarity(
        self,
        embedding_a: Optional[Union[np.ndarray, list]],
        embedding_b: Optional[Union[np.ndarray, list]]
    ) -> float:
        """
        Computes mathematically exact cosine similarity in [-1.0, 1.0].
        Delegates to the vectorized appearance extractor.
        """
        return self.feature_extractor.compute_cosine_similarity(embedding_a, embedding_b)

    def compute_plate_similarity(self, plate_a: Optional[str], plate_b: Optional[str]) -> float:
        """
        Computes normalized string similarity for license plates in [0.0, 1.0].
        Treats UNKNOWN, empty, or unreadable plates safely as 0.0.
        """
        if not plate_a or not plate_b:
            return 0.0
        
        p_a = plate_a.strip().upper().replace(" ", "").replace("-", "")
        p_b = plate_b.strip().upper().replace(" ", "").replace("-", "")
        
        if p_a == "UNKNOWN" or p_b == "UNKNOWN" or not p_a or not p_b:
            return 0.0
        
        if p_a == p_b:
            return 1.0
        
        matcher = difflib.SequenceMatcher(None, p_a, p_b)
        return float(round(matcher.ratio(), 4))

    def compute_type_match(self, type_a: Optional[str], type_b: Optional[str]) -> float:
        """
        Computes vehicle class consistency in [0.0, 1.0].
        Returns 0.0 for incompatible types (e.g. car vs truck, motorcycle vs bus).
        """
        if not type_a or not type_b or type_a.upper() == "UNKNOWN" or type_b.upper() == "UNKNOWN":
            return 0.50
        
        t_a = type_a.strip().lower()
        t_b = type_b.strip().lower()
        
        if t_a == t_b:
            return 1.0
        
        # Compatible car/light vehicle categories
        light_vehicles = {"sedan", "hatchback", "car", "suv"}
        if t_a in light_vehicles and t_b in light_vehicles:
            return 0.75
        
        # Heavy transport categories
        heavy_vehicles = {"truck", "bus"}
        if t_a in heavy_vehicles and t_b in heavy_vehicles:
            return 0.50
        
        # Severe conflict (e.g. sedan vs bus, motorcycle vs truck)
        return 0.0

    def compute_color_similarity(self, color_a: Optional[str], color_b: Optional[str]) -> float:
        """
        Computes vehicle color compatibility in [0.0, 1.0].
        """
        if not color_a or not color_b or color_a.upper() == "UNKNOWN" or color_b.upper() == "UNKNOWN":
            return 0.50
        
        c_a = color_a.strip().upper()
        c_b = color_b.strip().upper()
        
        if c_a == c_b:
            return 1.0
        
        # Adjacent shades
        if {c_a, c_b}.issubset({"WHITE", "SILVER"}):
            return 0.75
        if {c_a, c_b}.issubset({"BLACK", "GREY", "DARK GREY", "SILVER"}):
            return 0.70
        if {c_a, c_b}.issubset({"BLUE", "NAVY", "DARK BLUE"}):
            return 0.80
        if {c_a, c_b}.issubset({"RED", "MAROON", "ORANGE"}):
            return 0.70
            
        return 0.0

    def compute_spatiotemporal_consistency(
        self,
        cam_a: str,
        cam_b: str,
        time_elapsed_sec: float
    ) -> Tuple[float, bool, str]:
        """
        Computes spatiotemporal transit feasibility across camera network graph.
        Returns:
            (spatiotemporal_score [0.0, 1.0], is_feasible [bool], transit_status [str])
        """
        if cam_a == cam_b:
            if time_elapsed_sec < 5:
                return 1.0, True, "CONTINUOUS_SAME_CAMERA"
            return 0.85, True, "REVISIT_SAME_CAMERA"

        route = topology_engine.get_distance_and_transit(cam_a, cam_b)
        if not route:
            # Unmapped path in camera graph - default to neutral feasibility
            return 0.50, True, "UNMAPPED_GRAPH_PATH"

        min_time = route.get("min_time_sec", 60.0)
        max_time = route.get("max_time_sec", 1800.0)

        # Spatiotemporal veto: physically impossible travel time (teleportation anomaly)
        if time_elapsed_sec < (min_time * 0.5):
            return 0.0, False, "IMPOSSIBLE_TRAVEL_SPEED"

        # Feasible transit window
        if min_time <= time_elapsed_sec <= max_time:
            return 1.0, True, "FEASIBLE_TRANSIT"
        elif (min_time * 0.5) <= time_elapsed_sec < min_time:
            return 0.70, True, "FAST_TRANSIT"
        else:
            return 0.60, True, "DELAYED_TRANSIT"

    def match_observations(
        self,
        crop_a: Optional[np.ndarray] = None,
        crop_b: Optional[np.ndarray] = None,
        embedding_a: Optional[Union[np.ndarray, list]] = None,
        embedding_b: Optional[Union[np.ndarray, list]] = None,
        plate_a: Optional[str] = None,
        plate_b: Optional[str] = None,
        type_a: str = "UNKNOWN",
        type_b: str = "UNKNOWN",
        color_a: str = "UNKNOWN",
        color_b: str = "UNKNOWN",
        cam_a: str = "CAM01",
        cam_b: str = "CAM02",
        tracker_a: str = "CAM01-TRK-001",
        tracker_b: str = "CAM02-TRK-001",
        time_elapsed_sec: float = 120.0
    ) -> Dict[str, Any]:
        """
        Performs pairwise Vehicle Re-Identification comparison between two observations.
        Produces explainable score breakdown and 3-state decision (MATCH, REVIEW_REQUIRED, REJECT).
        """
        # 1. Extract visual appearance embeddings if not provided
        if embedding_a is None and crop_a is not None:
            embedding_a = self.feature_extractor.extract_embedding(crop_a)
        if embedding_b is None and crop_b is not None:
            embedding_b = self.feature_extractor.extract_embedding(crop_b)

        # Convert lists to np.ndarray if necessary
        if isinstance(embedding_a, list):
            embedding_a = np.array(embedding_a, dtype=np.float32)
        if isinstance(embedding_b, list):
            embedding_b = np.array(embedding_b, dtype=np.float32)

        has_valid_emb_a = (embedding_a is not None and isinstance(embedding_a, np.ndarray) and np.linalg.norm(embedding_a) > 0.1)
        has_valid_emb_b = (embedding_b is not None and isinstance(embedding_b, np.ndarray) and np.linalg.norm(embedding_b) > 0.1)

        # 2. Compute individual similarity components
        visual_sim = self.compute_cosine_similarity(embedding_a, embedding_b) if (has_valid_emb_a and has_valid_emb_b) else 0.0
        plate_sim = self.compute_plate_similarity(plate_a, plate_b)
        type_sim = self.compute_type_match(type_a, type_b)
        color_sim = self.compute_color_similarity(color_a, color_b)
        attr_sim = round((type_sim + color_sim) / 2.0, 4)

        # 3. Spatiotemporal feasibility check
        st_score, st_feasible, st_status = self.compute_spatiotemporal_consistency(cam_a, cam_b, time_elapsed_sec)

        # 4. Multi-modal composite score calculation
        # Scaled visual similarity to [0.0, 1.0]
        vis_score_norm = max(0.0, visual_sim)

        # Re-weight if plate is unavailable (Unknown Plate Fallback - Step 11)
        if plate_sim == 0.0 and (not plate_a or not plate_b or plate_a == "UNKNOWN" or plate_b == "UNKNOWN"):
            # Unknown plate fallback: redistribute plate weight to appearance and attributes
            w_vis = self.weight_visual + (self.weight_plate * 0.6)
            w_attr = self.weight_attributes + (self.weight_plate * 0.4)
            w_st = self.weight_spatiotemporal
            composite_score = (w_vis * vis_score_norm) + (w_attr * attr_sim) + (w_st * st_score)
        else:
            composite_score = (
                (self.weight_visual * vis_score_norm) +
                (self.weight_plate * plate_sim) +
                (self.weight_attributes * attr_sim) +
                (self.weight_spatiotemporal * st_score)
            )

        composite_score = float(np.clip(round(composite_score, 4), 0.0, 1.0))

        # 5. Three-State Decision Logic with Reason Codes (Step 8, Step 9, Step 10, Step 12)
        # Reason codes: MATCHED, LOW_CONFIDENCE, ATTRIBUTE_CONFLICT, STRONG_APPEARANCE_CONFLICT,
        # IMPOSSIBLE_TRAVEL_SPEED, NO_PLAUSIBLE_CANDIDATE, INVALID_EMBEDDING, PLATE_MISMATCH

        # Rule 1: Spatiotemporal Veto (Physically Impossible Travel Time)
        if not st_feasible or st_status == "IMPOSSIBLE_TRAVEL_SPEED":
            decision = "REJECT"
            reason_code = "IMPOSSIBLE_TRAVEL_SPEED"
            reason_text = (
                f"Transit time {round(time_elapsed_sec, 1)}s between {cam_a} and {cam_b} "
                f"is physically impossible (teleportation anomaly)."
            )

        # Rule 2: Strong Appearance Conflict / Incompatible Vehicle Class
        elif type_sim == 0.0:
            decision = "REJECT"
            reason_code = "STRONG_APPEARANCE_CONFLICT"
            reason_text = f"Incompatible vehicle classes ({type_a} vs {type_b})."

        # Rule 3: Visual Appearance Mismatch despite Identical Plate (Anti-Spoofing / Cloned Plate)
        elif plate_sim >= 0.90 and visual_sim < 0.30 and has_valid_emb_a and has_valid_emb_b:
            decision = "REVIEW_REQUIRED"
            reason_code = "STRONG_APPEARANCE_CONFLICT"
            reason_text = (
                f"Visual appearance mismatch ({round(visual_sim, 3)}) despite matching plate number. "
                "Manual human verification required."
            )

        # Rule 4: Attribute Conflict (Color or Model Mismatch with matching plate)
        elif plate_sim >= 0.90 and (color_sim == 0.0 or attr_sim < 0.50):
            decision = "REVIEW_REQUIRED"
            reason_code = "ATTRIBUTE_CONFLICT"
            reason_text = (
                f"License plate matches but vehicle attributes conflict "
                f"(Color: {color_a} vs {color_b}, Type: {type_a} vs {type_b})."
            )

        # Rule 5: Confirmed Match (Strong visual + attribute or high composite score)
        elif (
            (visual_sim >= self.visual_similarity_threshold and attr_sim >= 0.70 and st_feasible) or
            (composite_score >= self.composite_match_threshold and visual_sim >= 0.60 and st_feasible) or
            (plate_sim >= 0.90 and visual_sim >= 0.50 and st_feasible and attr_sim >= 0.60) or
            (plate_sim >= 0.90 and not has_valid_emb_a and not has_valid_emb_b and attr_sim >= 0.70 and st_feasible)
        ):
            decision = "MATCH"
            reason_code = "MATCHED"
            reason_text = (
                f"Consistent multi-modal correspondence (Composite: {round(composite_score, 3)}, "
                f"Visual: {round(visual_sim, 3)}, Attributes: {round(attr_sim, 2)})."
            )

        # Rule 6: Unknown Plate Fallback Match (High Visual + Feasible Transit)
        elif plate_sim == 0.0 and visual_sim >= self.visual_similarity_threshold and attr_sim >= 0.70 and st_feasible:
            decision = "MATCH"
            reason_code = "MATCHED"
            reason_text = (
                f"Confirmed visual Re-ID match for unknown plate (Visual Cosine: {round(visual_sim, 3)}, "
                f"Transit: {st_status})."
            )

        # Rule 7: Uncertain / Inconclusive Evidence (Requires Human Review)
        elif composite_score >= 0.50 or (visual_sim >= 0.50 and st_feasible):
            decision = "REVIEW_REQUIRED"
            reason_code = "LOW_CONFIDENCE"
            reason_text = (
                f"Inconclusive composite evidence (Composite: {round(composite_score, 3)}, "
                f"Visual: {round(visual_sim, 3)}). Manual review required."
            )

        # Rule 8: Rejected
        else:
            decision = "REJECT"
            reason_code = "LOW_CONFIDENCE" if plate_sim == 0.0 else "PLATE_MISMATCH"
            reason_text = f"Insufficient similarity signals (Composite score: {round(composite_score, 3)})."

        return {
            "decision": decision,
            "reason_code": reason_code,
            "reason": reason_text,
            "composite_score": composite_score,
            "breakdown": {
                "appearance_similarity": round(visual_sim, 4),
                "plate_similarity": round(plate_sim, 3),
                "attribute_similarity": round(attr_sim, 3),
                "trajectory_score": round(st_score, 3),
                "composite_score": composite_score
            },
            "visual_similarity": round(visual_sim, 4),
            "plate_similarity": round(plate_sim, 3),
            "vehicle_type_similarity": round(type_sim, 3),
            "color_similarity": round(color_sim, 3),
            "attribute_similarity": round(attr_sim, 3),
            "spatiotemporal_score": round(st_score, 3),
            "spatiotemporal_feasible": st_feasible,
            "transit_status": st_status,
            "candidate_a": {
                "camera_id": cam_a,
                "tracker_id": tracker_a,
                "plate_text": plate_a or "UNKNOWN",
                "vehicle_type": type_a,
                "vehicle_color": color_a
            },
            "candidate_b": {
                "camera_id": cam_b,
                "tracker_id": tracker_b,
                "plate_text": plate_b or "UNKNOWN",
                "vehicle_type": type_b,
                "vehicle_color": color_b
            },
            "time_elapsed_sec": round(time_elapsed_sec, 2)
        }

    def match_vehicles(
        self,
        plate_a: str,
        type_a: str,
        color_a: str,
        cam_a: str,
        plate_b: str,
        type_b: str,
        color_b: str,
        cam_b: str,
        time_elapsed_sec: float
    ) -> Dict[str, Any]:
        """Backwards compatibility helper matching attribute and spatiotemporal signals."""
        res = self.match_observations(
            plate_a=plate_a,
            plate_b=plate_b,
            type_a=type_a,
            type_b=type_b,
            color_a=color_a,
            color_b=color_b,
            cam_a=cam_a,
            cam_b=cam_b,
            time_elapsed_sec=time_elapsed_sec
        )
        legacy_score = (
            (0.40 * res["plate_similarity"]) +
            (0.20 * res["vehicle_type_similarity"]) +
            (0.20 * res["color_similarity"]) +
            (0.10 * res["spatiotemporal_score"]) +
            (0.10 * res["spatiotemporal_score"])
        )
        legacy_score = round(legacy_score, 2)

        classification = "HIGH CONFIDENCE MATCH" if legacy_score >= 0.85 else (
            "PROBABLE MATCH" if legacy_score >= 0.65 else "UNCERTAIN MATCH"
        )
        return {
            "overall_match_confidence": legacy_score,
            "classification": classification,
            "plate_similarity": res["plate_similarity"],
            "type_match": res["vehicle_type_similarity"],
            "colour_similarity": res["color_similarity"],
            "temporal_consistency": res["spatiotemporal_score"],
            "route_consistency": res["spatiotemporal_score"],
            "transit_status": res["transit_status"],
            "decision": res["decision"],
            "reason": res["reason"],
            "reason_code": res["reason_code"]
        }

    def find_reid_candidates(
        self,
        db,
        camera_id: str,
        observed_type: str = "car",
        observed_color: str = "UNKNOWN",
        observed_plate: Optional[str] = None,
        observed_embedding: Optional[np.ndarray] = None,
        timestamp: Optional[datetime] = None,
        max_search_window_sec: float = 3600.0
    ) -> List[Dict[str, Any]]:
        """
        Filters and evaluates plausible candidate vehicles using inexpensive constraints
        before running expensive appearance vector comparisons (Step 15).
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            
        time_cutoff = timestamp - timedelta(seconds=max_search_window_sec)

        # Inexpensive constraint 1: Recent sightings within time window
        # Inexpensive constraint 2: Primary plate or recent camera presence
        query = db.query(Vehicle)
        
        # If plate is known, prioritize matching plate records
        if observed_plate and observed_plate != "UNKNOWN":
            candidates = query.filter(
                (Vehicle.primary_plate == observed_plate) |
                (Vehicle.last_seen >= time_cutoff)
            ).order_by(Vehicle.last_seen.desc()).limit(30).all()
        else:
            candidates = query.filter(
                Vehicle.last_seen >= time_cutoff
            ).order_by(Vehicle.last_seen.desc()).limit(30).all()

        scored_candidates = []
        for cand in candidates:
            # Inexpensive constraint 3: Vehicle Class Compatibility
            type_sim = self.compute_type_match(observed_type, cand.vehicle_type)
            if type_sim == 0.0:
                continue

            # Calculate time elapsed between previous sighting and current observation
            cand_time = cand.last_seen or cand.first_seen
            if cand_time and cand_time.tzinfo is None:
                cand_time = cand_time.replace(tzinfo=timezone.utc)
            
            curr_time = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
            time_elapsed_sec = max(1.0, (curr_time - cand_time).total_seconds()) if cand_time else 120.0

            cand_cam = cand.last_camera_id or "CAM01"

            # Parse candidate's stored appearance embedding
            cand_emb = None
            if cand.appearance_embedding:
                try:
                    cand_emb = np.array(json.loads(cand.appearance_embedding), dtype=np.float32)
                except Exception:
                    cand_emb = None

            # Evaluate Re-ID match
            match_res = self.match_observations(
                embedding_a=cand_emb,
                embedding_b=observed_embedding,
                plate_a=cand.primary_plate,
                plate_b=observed_plate,
                type_a=cand.vehicle_type,
                type_b=observed_type,
                color_a=cand.color,
                color_b=observed_color,
                cam_a=cand_cam,
                cam_b=camera_id,
                time_elapsed_sec=time_elapsed_sec
            )

            scored_candidates.append({
                "vehicle": cand,
                "global_id": cand.global_id,
                "match_result": match_res,
                "composite_score": match_res["composite_score"],
                "decision": match_res["decision"],
                "reason_code": match_res["reason_code"]
            })

        # Sort candidates by composite score descending
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)
        return scored_candidates

    def associate_track_to_global_vehicle(
        self,
        db,
        camera_id: str,
        tracker_id: str,
        image_crop: Optional[np.ndarray] = None,
        embedding: Optional[np.ndarray] = None,
        plate_text: Optional[str] = "UNKNOWN",
        vehicle_type: str = "car",
        vehicle_color: str = "UNKNOWN",
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Links a camera-local tracker ID to a Global Vehicle ID (Step 2, Step 14).
        If a plausible global profile exists and matches, merges track into existing entity.
        If no plausible global profile exists, creates a new Global Vehicle entity.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # 1. Extract visual embedding if not already available
        if embedding is None and image_crop is not None:
            embedding = self.feature_extractor.extract_embedding(image_crop)

        # 2. Check for DMV Registration Attribute Conflicts (Step 12)
        reg_record = None
        has_reg_conflict = False
        if plate_text and plate_text != "UNKNOWN":
            reg_record = db.query(DemoRegistryVehicle).filter(
                DemoRegistryVehicle.registration_number == plate_text
            ).first()
            if reg_record:
                reg_color = reg_record.registered_color.upper()
                reg_type = reg_record.vehicle_type.lower()
                obs_color = vehicle_color.upper() if vehicle_color else "UNKNOWN"
                obs_type = vehicle_type.lower() if vehicle_type else "car"

                # Check if color or vehicle type sharply conflicts with official registry
                if obs_color != "UNKNOWN" and reg_color != "UNKNOWN" and self.compute_color_similarity(obs_color, reg_color) == 0.0:
                    has_reg_conflict = True
                if self.compute_type_match(obs_type, reg_type) == 0.0:
                    has_reg_conflict = True

        # 3. Find candidate matches across previous camera sightings
        candidates = self.find_reid_candidates(
            db=db,
            camera_id=camera_id,
            observed_type=vehicle_type,
            observed_color=vehicle_color,
            observed_plate=plate_text,
            observed_embedding=embedding,
            timestamp=timestamp
        )

        best_candidate = candidates[0] if candidates else None

        # 4. Association Logic
        if best_candidate and best_candidate["decision"] == "MATCH" and not has_reg_conflict:
            # Merge with existing Global Vehicle profile
            matched_vehicle = best_candidate["vehicle"]
            matched_vehicle.last_seen = timestamp
            matched_vehicle.last_camera_id = camera_id
            matched_vehicle.last_seen_timestamp = timestamp
            matched_vehicle.total_sightings = (matched_vehicle.total_sightings or 1) + 1
            
            # Update running visual embedding (moving average) if new valid embedding is available
            if embedding is not None and np.linalg.norm(embedding) > 0.1:
                if matched_vehicle.appearance_embedding:
                    try:
                        old_emb = np.array(json.loads(matched_vehicle.appearance_embedding), dtype=np.float32)
                        merged_emb = self.feature_extractor.l2_normalize(0.7 * old_emb + 0.3 * embedding)
                        matched_vehicle.appearance_embedding = json.dumps(merged_emb.tolist())
                    except Exception:
                        matched_vehicle.appearance_embedding = json.dumps(embedding.tolist())
                else:
                    matched_vehicle.appearance_embedding = json.dumps(embedding.tolist())

            matched_vehicle.confidence = max(matched_vehicle.confidence, best_candidate["composite_score"])
            matched_vehicle.reid_decision = "MATCH"
            matched_vehicle.reid_reason = "MATCHED"

            # Add Trajectory Waypoint
            cam_meta = topology_engine.get_camera(camera_id)
            lat = cam_meta["lat"] if cam_meta else 13.0827
            lon = cam_meta["lon"] if cam_meta else 80.2707
            
            traj = Trajectory(
                vehicle_id=matched_vehicle.id,
                camera_id=camera_id,
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                speed_kmh=50.0,
                route_confidence=best_candidate["composite_score"]
            )
            db.add(traj)
            db.commit()
            db.refresh(matched_vehicle)

            logger.info(
                f"[ReID] Merged local tracker {tracker_id} ({camera_id}) -> "
                f"Global Vehicle {matched_vehicle.global_id} (Score: {best_candidate['composite_score']})"
            )

            return {
                "global_vehicle_id": matched_vehicle.global_id,
                "vehicle_id": matched_vehicle.id,
                "is_new_vehicle": False,
                "decision": "MATCH",
                "reason_code": "MATCHED",
                "match_result": best_candidate["match_result"]
            }

        elif has_reg_conflict:
            # Registration Attribute Conflict (Step 12)
            # Find or create vehicle record with REVIEW_REQUIRED status
            logger.warning(
                f"[ReID] Registration attribute conflict detected for plate {plate_text}: "
                f"Observed ({vehicle_color} {vehicle_type}) vs Registered."
            )
            # Look up vehicle or create one with REVIEW_REQUIRED
            existing = db.query(Vehicle).filter(Vehicle.primary_plate == plate_text).first()
            if not existing:
                count = db.query(Vehicle).count() + 1
                global_id = f"VEH-{count:06d}"
                emb_json = json.dumps(embedding.tolist()) if (embedding is not None and np.linalg.norm(embedding) > 0.1) else None
                existing = Vehicle(
                    global_id=global_id,
                    primary_plate=plate_text,
                    vehicle_type=vehicle_type,
                    color=vehicle_color,
                    confidence=0.60,
                    first_seen=timestamp,
                    last_seen=timestamp,
                    total_sightings=1,
                    is_flagged=True,
                    notes="Flagged: Observed attributes conflict with DMV registration data.",
                    appearance_embedding=emb_json,
                    last_camera_id=camera_id,
                    last_seen_timestamp=timestamp,
                    reid_decision="REVIEW_REQUIRED",
                    reid_reason="ATTRIBUTE_CONFLICT"
                )
                db.add(existing)
            else:
                existing.is_flagged = True
                existing.reid_decision = "REVIEW_REQUIRED"
                existing.reid_reason = "ATTRIBUTE_CONFLICT"
                existing.last_seen = timestamp
                existing.last_camera_id = camera_id
                existing.total_sightings = (existing.total_sightings or 1) + 1

            db.commit()
            db.refresh(existing)

            return {
                "global_vehicle_id": existing.global_id,
                "vehicle_id": existing.id,
                "is_new_vehicle": False,
                "decision": "REVIEW_REQUIRED",
                "reason_code": "ATTRIBUTE_CONFLICT",
                "match_result": {
                    "decision": "REVIEW_REQUIRED",
                    "reason_code": "ATTRIBUTE_CONFLICT",
                    "reason": "Observed attributes conflict with official registration data."
                }
            }

        else:
            # No matching candidate profile -> Create a new Global Vehicle entity (Step 2)
            count = db.query(Vehicle).count() + 1
            global_id = f"VEH-{count:06d}"
            
            emb_json = json.dumps(embedding.tolist()) if (embedding is not None and np.linalg.norm(embedding) > 0.1) else None
            
            new_vehicle = Vehicle(
                global_id=global_id,
                primary_plate=plate_text if plate_text and plate_text != "UNKNOWN" else None,
                vehicle_type=vehicle_type,
                color=vehicle_color,
                confidence=0.85,
                first_seen=timestamp,
                last_seen=timestamp,
                total_sightings=1,
                is_flagged=False,
                notes=None,
                appearance_embedding=emb_json,
                last_camera_id=camera_id,
                last_seen_timestamp=timestamp,
                reid_decision="MATCH",
                reid_reason="INITIAL_CREATION"
            )
            db.add(new_vehicle)
            db.commit()
            db.refresh(new_vehicle)

            # Record initial trajectory waypoint
            cam_meta = topology_engine.get_camera(camera_id)
            lat = cam_meta["lat"] if cam_meta else 13.0827
            lon = cam_meta["lon"] if cam_meta else 80.2707
            
            traj = Trajectory(
                vehicle_id=new_vehicle.id,
                camera_id=camera_id,
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                speed_kmh=50.0,
                route_confidence=1.0
            )
            db.add(traj)
            db.commit()

            logger.info(
                f"[ReID] Created new Global Vehicle ID {global_id} for local tracker {tracker_id} on {camera_id}"
            )

            return {
                "global_vehicle_id": global_id,
                "vehicle_id": new_vehicle.id,
                "is_new_vehicle": True,
                "decision": "MATCH",
                "reason_code": "NO_PLAUSIBLE_CANDIDATE",
                "match_result": {
                    "decision": "MATCH",
                    "reason_code": "NO_PLAUSIBLE_CANDIDATE",
                    "reason": "New global vehicle profile created."
                }
            }


reid_service = VehicleReIDService()
