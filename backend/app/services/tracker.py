import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("cityai.tracker")

def calculate_iou(bbox1: List[float], bbox2: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two bounding boxes [x1, y1, x2, y2]."""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    intersection_w = max(0.0, x2 - x1)
    intersection_h = max(0.0, y2 - y1)
    intersection_area = intersection_w * intersection_h

    area1 = max(0.0, (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1]))
    area2 = max(0.0, (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1]))
    union_area = area1 + area2 - intersection_area

    if union_area <= 0.0:
        return 0.0
    return intersection_area / union_area

class TrackedVehicle:
    """
    State Container for an Object Tracked within a Specific Camera Viewport.
    Maintains motion history, bounding box trajectory, and temporal lifetime.
    """
    def __init__(self, track_id: int, camera_id: str, detection: Dict[str, Any], frame_number: int, timestamp: Optional[datetime] = None):
        self.track_id = track_id
        self.camera_id = camera_id
        self.local_tracker_id = f"{camera_id}-TRK-{track_id:03d}"
        self.display_id = str(track_id)
        self.vehicle_class = detection.get("class", "car")
        self.confidence = detection.get("confidence", 0.85)
        self.bbox = detection.get("bbox", [0, 0, 0, 0])
        self.center = detection.get("center", [0, 0])
        
        self.first_seen = timestamp or datetime.now(timezone.utc)
        self.last_seen = self.first_seen
        self.total_frames = 1
        self.misses = 0
        self.status = "ACTIVE"  # ACTIVE, LOST, COMPLETED
        
        # Spatial trajectory history within this camera
        self.trajectory_points: List[Dict[str, Any]] = [{
            "frame": frame_number,
            "cx": self.center[0],
            "cy": self.center[1],
            "bbox": self.bbox,
            "timestamp": self.first_seen.isoformat()
        }]

        # Phase 4: ANPR & Vehicle Attribute State
        self.plate_text: str = "UNKNOWN"
        self.raw_text: Optional[str] = None
        self.ocr_confidence: float = 0.0
        self.validation_status: str = "UNKNOWN"
        self.plate_bbox: Optional[List[float]] = None
        self.plate_crop_path: Optional[str] = None
        self.vehicle_color: str = "UNKNOWN"
        self.color_confidence: float = 0.0
        self.last_anpr_frame: int = 0

        # Phase 5: Re-ID Appearance Embedding & Global Vehicle Association
        self.global_vehicle_id: Optional[str] = None
        self.embedding: Optional[Any] = None
        self.has_extracted_embedding: bool = False
        self.reid_decision: str = "PENDING"
        self.reid_reason: str = "UNPROCESSED"
        self.best_crop: Optional[Any] = None
        self.best_crop_confidence: float = 0.0

    def update_anpr_and_attributes(
        self,
        plate_text: str,
        ocr_confidence: float,
        validation_status: str,
        vehicle_color: str,
        color_confidence: float,
        raw_text: Optional[str] = None,
        plate_bbox: Optional[List[float]] = None,
        plate_crop_path: Optional[str] = None,
        frame_number: int = 0
    ):
        """Updates plate recognition and color attributes, retaining highest-confidence observations."""
        self.last_anpr_frame = frame_number
        if vehicle_color and vehicle_color != "UNKNOWN" and color_confidence >= self.color_confidence:
            self.vehicle_color = vehicle_color
            self.color_confidence = color_confidence

        if plate_text and plate_text != "UNKNOWN":
            # Retain higher confidence plate observation
            if ocr_confidence >= self.ocr_confidence or self.plate_text == "UNKNOWN":
                self.plate_text = plate_text
                self.raw_text = raw_text
                self.ocr_confidence = ocr_confidence
                self.validation_status = validation_status
                if plate_bbox:
                    self.plate_bbox = plate_bbox
                if plate_crop_path:
                    self.plate_crop_path = plate_crop_path

    def update(self, detection: Dict[str, Any], frame_number: int, timestamp: Optional[datetime] = None):
        """Updates track with newly matched detection."""
        self.bbox = detection.get("bbox", self.bbox)
        self.center = detection.get("center", self.center)
        # Moving average of confidence
        self.confidence = (self.confidence * 0.7) + (detection.get("confidence", self.confidence) * 0.3)
        self.last_seen = timestamp or datetime.now(timezone.utc)
        self.total_frames += 1
        self.misses = 0
        self.status = "ACTIVE"
        
        self.trajectory_points.append({
            "frame": frame_number,
            "cx": self.center[0],
            "cy": self.center[1],
            "bbox": self.bbox,
            "timestamp": self.last_seen.isoformat()
        })
        # Keep recent 50 trajectory points in memory
        if len(self.trajectory_points) > 50:
            self.trajectory_points.pop(0)

    def mark_missed(self):
        """Increments miss counter when track is not detected in a frame."""
        self.misses += 1
        if self.misses > 5:
            self.status = "LOST"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tracker_id": self.local_tracker_id,
            "global_vehicle_id": self.global_vehicle_id,
            "display_id": self.display_id,
            "camera_id": self.camera_id,
            "vehicle_class": self.vehicle_class,
            "confidence": round(self.confidence, 3),
            "bbox": self.bbox,
            "center": self.center,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_frames": self.total_frames,
            "status": self.status,
            "trajectory_points": self.trajectory_points,
            "plate_text": self.plate_text,
            "raw_text": self.raw_text,
            "ocr_confidence": round(self.ocr_confidence, 3),
            "validation_status": self.validation_status,
            "plate_bbox": self.plate_bbox,
            "plate_crop_path": self.plate_crop_path,
            "vehicle_color": self.vehicle_color,
            "color_confidence": round(self.color_confidence, 3),
            "reid_decision": self.reid_decision,
            "reid_reason": self.reid_reason,
            "has_embedding": self.embedding is not None
        }

class CameraObjectTracker:
    """
    Per-Camera Multi-Object Tracker (MOT).
    Employs IoU association with spatial distance gating to track vehicles across frame sequences.
    Strictly keeps tracker IDs local to this camera.
    """
    def __init__(self, camera_id: str, iou_threshold: float = 0.30, max_age: int = 25):
        self.camera_id = camera_id
        self.iou_threshold = iou_threshold
        self.max_age = max_age
        self.next_track_id = 1
        self.tracks: Dict[int, TrackedVehicle] = {}
        self.completed_tracks_count = 0

    def update(self, detections: List[Dict[str, Any]], frame_number: int, timestamp: Optional[datetime] = None) -> List[TrackedVehicle]:
        """
        Associates frame detections with active tracks and spawns new tracks.
        Returns the list of currently active tracked vehicles.
        """
        active_track_ids = list(self.tracks.keys())
        unmatched_detections = list(range(len(detections)))
        unmatched_tracks = set(active_track_ids)

        if len(active_track_ids) > 0 and len(detections) > 0:
            # 1. Compute Cost / IoU Matrix
            iou_matches = []
            for d_idx, det in enumerate(detections):
                det_bbox = det["bbox"]
                det_class = det["class"]

                for t_id in active_track_ids:
                    track = self.tracks[t_id]
                    # Class matching preference
                    if track.vehicle_class != det_class:
                        continue

                    iou = calculate_iou(det_bbox, track.bbox)
                    if iou >= self.iou_threshold:
                        iou_matches.append((iou, d_idx, t_id))

            # Sort matches by highest IoU first (Greedy bipartite matching)
            iou_matches.sort(key=lambda x: x[0], reverse=True)
            
            matched_det_indices = set()
            matched_track_ids = set()

            for iou, d_idx, t_id in iou_matches:
                if d_idx not in matched_det_indices and t_id not in matched_track_ids:
                    self.tracks[t_id].update(detections[d_idx], frame_number, timestamp)
                    matched_det_indices.add(d_idx)
                    matched_track_ids.add(t_id)

            unmatched_detections = [i for i in range(len(detections)) if i not in matched_det_indices]
            unmatched_tracks = set(active_track_ids) - matched_track_ids

        # 2. Update missed tracks
        for t_id in unmatched_tracks:
            self.tracks[t_id].mark_missed()
            if self.tracks[t_id].misses > self.max_age:
                self.tracks[t_id].status = "COMPLETED"
                del self.tracks[t_id]
                self.completed_tracks_count += 1

        # 3. Create new tracks for unmatched detections
        for d_idx in unmatched_detections:
            det = detections[d_idx]
            new_track = TrackedVehicle(
                track_id=self.next_track_id,
                camera_id=self.camera_id,
                detection=det,
                frame_number=frame_number,
                timestamp=timestamp
            )
            self.tracks[self.next_track_id] = new_track
            self.next_track_id += 1

        return list(self.tracks.values())

    def get_active_tracks(self) -> List[Dict[str, Any]]:
        """Returns active tracks for this camera as dictionaries."""
        return [t.to_dict() for t in self.tracks.values() if t.status in ["ACTIVE", "LOST"]]

    def reset(self):
        """Clears all tracks for this camera."""
        self.tracks.clear()
        self.next_track_id = 1
        self.completed_tracks_count = 0
