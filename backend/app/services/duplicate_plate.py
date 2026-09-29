import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from app.services.trajectory_engine import topology_engine
from app.services.vehicle_reid import reid_service

class DuplicatePlateEngine:
    """
    Central Intelligence Service: Correlates plate string with physical vehicle attributes,
    camera topology, and timestamps to detect cloned/duplicate plates.
    """

    def analyze_sighting(
        self,
        new_obs: Dict[str, Any],
        historical_obs: List[Dict[str, Any]],
        registered_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyzes a new vehicle sighting against previous sightings of the same plate.
        Returns an Alert dictionary if an anomaly or cloned plate signature is detected, else None.
        """
        plate_text = new_obs.get("plate_text")
        if not plate_text or plate_text in ["UNKNOWN", ""]:
            return None

        # Sort historical observations by timestamp descending
        valid_history = [h for h in historical_obs if h.get("plate_text") == plate_text]
        if not valid_history:
            # First time sighting — check against demo registry if provided
            if registered_info:
                return self._check_registry_discrepancy(new_obs, registered_info)
            return None

        last_obs = valid_history[0]

        # 1. Calculate time difference
        t_new = new_obs.get("timestamp")
        t_old = last_obs.get("timestamp")
        if isinstance(t_new, str):
            t_new = datetime.fromisoformat(t_new)
        if isinstance(t_old, str):
            t_old = datetime.fromisoformat(t_old)

        time_delta_sec = max(1.0, abs((t_new - t_old).total_seconds()))

        # 2. Check Attribute Discrepancy (Vehicle Type & Color)
        color_new = (new_obs.get("color") or "UNKNOWN").upper()
        color_old = (last_obs.get("color") or "UNKNOWN").upper()
        type_new = (new_obs.get("vehicle_type") or "UNKNOWN").lower()
        type_old = (last_obs.get("vehicle_type") or "UNKNOWN").lower()

        type_match_score = reid_service.compute_type_match(type_new, type_old)
        color_match_score = reid_service.compute_color_similarity(color_new, color_old)

        # 3. Check Spatiotemporal Feasibility
        cam_new = new_obs.get("camera_id")
        cam_old = last_obs.get("camera_id")
        
        dist_km, speed_kmh, is_impossible, speed_explanation = topology_engine.calculate_inter_camera_speed(
            cam_old, cam_new, time_delta_sec
        )

        has_attribute_conflict = (color_match_score < 0.50 and color_new != "UNKNOWN" and color_old != "UNKNOWN") or \
                                 (type_match_score < 0.50 and type_new != "UNKNOWN" and type_old != "UNKNOWN")

        # CASE 1: CONFLICTING VEHICLE ATTRIBUTES WITH SAME PLATE
        if has_attribute_conflict:
            severity = "CRITICAL"
            title = f"POSSIBLE DUPLICATE / CLONED PLATE: {plate_text}"
            desc = (
                f"Registration plate '{plate_text}' detected on conflicting vehicle appearances: "
                f"Observed at {cam_new} as '{color_new} {type_new.upper()}' (Confidence: {new_obs.get('confidence', 0.9):.2f}) "
                f"versus previously observed at {cam_old} as '{color_old} {type_old.upper()}' "
                f"(Time difference: {time_delta_sec:.0f}s). Requires human visual verification."
            )
            
            details = {
                "plate_text": plate_text,
                "anomaly_type": "VISUAL_ATTRIBUTE_MISMATCH",
                "new_observation": {
                    "camera_id": cam_new,
                    "timestamp": t_new.isoformat() if hasattr(t_new, 'isoformat') else str(t_new),
                    "vehicle_type": type_new,
                    "color": color_new,
                    "ocr_confidence": new_obs.get("ocr_confidence", 0.9),
                    "snapshot_path": new_obs.get("snapshot_path")
                },
                "previous_observation": {
                    "camera_id": cam_old,
                    "timestamp": t_old.isoformat() if hasattr(t_old, 'isoformat') else str(t_old),
                    "vehicle_type": type_old,
                    "color": color_old,
                    "ocr_confidence": last_obs.get("ocr_confidence", 0.9),
                    "snapshot_path": last_obs.get("snapshot_path")
                },
                "discrepancy_scores": {
                    "type_match_score": type_match_score,
                    "color_match_score": color_match_score,
                    "estimated_transit_speed_kmh": speed_kmh
                },
                "recommendation": "Inspect camera snapshot crops side-by-side to confirm plate duplication or OCR misread."
            }

            return {
                "alert_type": "POSSIBLE_DUPLICATE_PLATE",
                "severity": severity,
                "status": "REQUIRES_VERIFICATION",
                "plate_text": plate_text,
                "source_camera_id": cam_old,
                "target_camera_id": cam_new,
                "title": title,
                "description": desc,
                "evidence_score": round(1.0 - ((type_match_score + color_match_score) / 2.0), 2),
                "details_json": json.dumps(details, default=str)
            }

        # CASE 2: IMPOSSIBLE SPATIOTEMPORAL TRAVEL (TELEPORTATION OR HYPER-SPEED)
        if is_impossible and cam_new != cam_old:
            severity = "CRITICAL"
            title = f"IMPOSSIBLE / UNUSUAL TRAVEL: {plate_text}"
            desc = (
                f"Plate '{plate_text}' recorded at {cam_old} and then {cam_new} within {time_delta_sec:.0f} seconds "
                f"(Required estimated speed: {speed_kmh:.1f} km/h over {dist_km:.1f} km). {speed_explanation} "
                f"Potential duplicate plate operating concurrently."
            )
            
            details = {
                "plate_text": plate_text,
                "anomaly_type": "IMPOSSIBLE_TRAVEL_SPEED",
                "source_camera": cam_old,
                "target_camera": cam_new,
                "distance_km": dist_km,
                "time_delta_sec": round(time_delta_sec, 1),
                "inferred_speed_kmh": speed_kmh,
                "new_observation": new_obs,
                "previous_observation": last_obs,
                "recommendation": "Review tollway checkpoints and camera timestamps for simultaneous duplicate vehicles."
            }

            return {
                "alert_type": "IMPOSSIBLE_TRAVEL",
                "severity": severity,
                "status": "REQUIRES_VERIFICATION",
                "plate_text": plate_text,
                "source_camera_id": cam_old,
                "target_camera_id": cam_new,
                "title": title,
                "description": desc,
                "evidence_score": 0.95,
                "details_json": json.dumps(details, default=str)
            }

        return None

    def _check_registry_discrepancy(
        self,
        obs: Dict[str, Any],
        reg: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Checks if observed vehicle mismatches official DMV registry record."""
        plate_text = obs.get("plate_text")
        obs_color = (obs.get("color") or "UNKNOWN").upper()
        reg_color = (reg.get("registered_color") or "UNKNOWN").upper()
        obs_type = (obs.get("vehicle_type") or "UNKNOWN").lower()
        reg_type = (reg.get("vehicle_type") or "UNKNOWN").lower()

        # Check stolen/wanted flag
        if reg.get("status") == "STOLEN":
            return {
                "alert_type": "REGISTRY_MISMATCH",
                "severity": "CRITICAL",
                "status": "REQUIRES_VERIFICATION",
                "plate_text": plate_text,
                "source_camera_id": obs.get("camera_id"),
                "title": f"POTENTIAL VIOLATION: STOLEN VEHICLE SIGHTING ({plate_text})",
                "description": (
                    f"Plate '{plate_text}' registered as STOLEN in Demo Vehicle Registry sighted at "
                    f"camera {obs.get('camera_id')}. Owner: {reg.get('owner_name')}. Immediate verification recommended."
                ),
                "evidence_score": 0.99,
                "details_json": json.dumps({"registry_data": reg, "observation": obs}, default=str)
            }

        # Check major attribute mismatch against registry
        c_sim = reid_service.compute_color_similarity(obs_color, reg_color)
        t_sim = reid_service.compute_type_match(obs_type, reg_type)

        if (c_sim < 0.5 and obs_color != "UNKNOWN") or (t_sim < 0.5 and obs_type != "UNKNOWN"):
            return {
                "alert_type": "REGISTRY_MISMATCH",
                "severity": "WARNING",
                "status": "REQUIRES_VERIFICATION",
                "plate_text": plate_text,
                "source_camera_id": obs.get("camera_id"),
                "title": f"REGISTRY MISMATCH: {plate_text}",
                "description": (
                    f"Vehicle sighted at {obs.get('camera_id')} ({obs_color} {obs_type.upper()}) mismatches "
                    f"registered DMV profile ({reg_color} {reg_type.upper()}, Model: {reg.get('make_model')})."
                ),
                "evidence_score": 0.85,
                "details_json": json.dumps({"registry_data": reg, "observation": obs}, default=str)
            }

        return None

duplicate_plate_engine = DuplicatePlateEngine()
