import time
import logging
import threading
import cv2
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings

logger = logging.getLogger("cityai.vehicle_detector")

# COCO Class mapping for target vehicle types
COCO_VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# Distinct UI Palette for Vehicle Classes (BGR)
CLASS_COLORS = {
    "car": (255, 180, 0),        # Cyan / Electric Blue
    "truck": (0, 140, 255),      # Amber / Orange
    "bus": (200, 50, 220),       # Magenta / Purple
    "motorcycle": (50, 220, 50)  # Bright Green
}
DEFAULT_COLOR = (0, 220, 255)

class VehicleDetector:
    """
    Ultralytics YOLO Vehicle Detector Service.
    Detects vehicles (car, motorcycle, bus, truck) on video frames with CPU/CUDA hardware detection.
    Accurately records bounding boxes, center coordinates, confidence, and inference FPS.
    """
    def __init__(self):
        self.model = None
        self.device = "cpu"
        self.is_initialized = False
        self.last_inference_ms: float = 0.0
        self.total_inferences: int = 0
        self.total_inference_time: float = 0.0
        self._lock = threading.Lock()
        self._init_detector()

    def _init_detector(self):
        """Initializes the Ultralytics YOLO model on CPU or CUDA device."""
        try:
            from ultralytics import YOLO
            
            # Determine target device
            if torch.cuda.is_available() and settings.DEVICE == "cuda":
                self.device = "cuda:0"
            else:
                self.device = "cpu"

            model_path = str(settings.YOLO_MODEL_PATH)
            if not Path(model_path).exists():
                logger.info(f"YOLO model not found locally at {model_path}. Loading {settings.YOLO_MODEL_NAME}...")
                self.model = YOLO(settings.YOLO_MODEL_NAME)
            else:
                self.model = YOLO(model_path)

            self.model.to(self.device)
            self.is_initialized = True
            logger.info(f"Ultralytics YOLO vehicle detector initialized successfully on device: {self.device.upper()}")

        except Exception as e:
            logger.error(f"Failed to initialize Ultralytics YOLO detector: {e}")
            self.model = None
            self.is_initialized = False

    def detect(self, frame: np.ndarray, confidence_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Runs object detection on a BGR image frame and extracts vehicles.
        Returns a list of detected vehicle objects:
        [{'bbox': [x1, y1, x2, y2], 'center': [cx, cy], 'class': 'car', 'confidence': 0.92, 'crop': np.ndarray}]
        """
        if frame is None or frame.size == 0 or self.model is None:
            return []

        conf_thresh = confidence_threshold if confidence_threshold is not None else settings.VEHICLE_DETECTION_CONFIDENCE
        h, w = frame.shape[:2]
        detections: List[Dict[str, Any]] = []

        start_time = time.perf_counter()
        try:
            with self._lock:
                # Run YOLO inference in eval mode without gradient tracking
                results = self.model.predict(
                    source=frame,
                    conf=conf_thresh,
                    device=self.device,
                    verbose=False,
                    classes=list(COCO_VEHICLE_CLASSES.keys())
                )

            for r in results:
                boxes = r.boxes
                if boxes is None or len(boxes) == 0:
                    continue

                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    cls_name = COCO_VEHICLE_CLASSES.get(cls_id, r.names.get(cls_id, "vehicle"))
                    
                    if cls_name not in settings.SUPPORTED_VEHICLE_CLASSES:
                        continue

                    conf = float(box.conf[0].item())
                    coords = box.xyxy[0].tolist()
                    x1 = max(0.0, min(float(coords[0]), float(w)))
                    y1 = max(0.0, min(float(coords[1]), float(h)))
                    x2 = max(0.0, min(float(coords[2]), float(w)))
                    y2 = max(0.0, min(float(coords[3]), float(h)))

                    # Filter degenerate bounding boxes
                    if (x2 - x1) < 10 or (y2 - y1) < 10:
                        continue

                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0

                    # Safe crop
                    crop = frame[int(y1):int(y2), int(x1):int(x2)].copy()

                    detections.append({
                        "bbox": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                        "center": [round(cx, 1), round(cy, 1)],
                        "class": cls_name,
                        "confidence": round(conf, 3),
                        "crop": crop
                    })

            # Record inference latency metrics
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.last_inference_ms = elapsed_ms
            self.total_inferences += 1
            self.total_inference_time += elapsed_ms

        except Exception as e:
            logger.error(f"Error during YOLO vehicle detection inference: {e}")

        return detections

    def detect_from_bytes(self, image_bytes: bytes, confidence_threshold: Optional[float] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Decodes raw image bytes and runs vehicle detection."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return [], {"error": "Invalid image payload"}
        
        start_time = time.perf_counter()
        detections = self.detect(frame, confidence_threshold=confidence_threshold)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        
        # Breakdown of classes
        counts: Dict[str, int] = {}
        for d in detections:
            c = d["class"]
            counts[c] = counts.get(c, 0) + 1

        stats = {
            "inference_ms": round(elapsed_ms, 2),
            "total_detected": len(detections),
            "counts": counts,
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}"
        }
        return detections, stats

    def draw_hud_annotations(
        self,
        frame: np.ndarray,
        tracks: List[Any],
        raw_detections: Optional[List[Dict[str, Any]]] = None,
        camera_id: str = "CAM",
        fps: float = 0.0
    ) -> np.ndarray:
        """
        Draws professional command-center HUD annotations on the frame:
        - Bounding boxes colored by vehicle class
        - Camera-local Tracker ID & confidence banner
        - Motion trajectory polyline trails
        - Live FPS and camera telemetry watermark
        """
        if frame is None:
            return frame

        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Draw trajectory paths & bounding boxes for active tracks
        for track in tracks:
            t_dict = track.to_dict() if hasattr(track, "to_dict") else track
            v_class = t_dict.get("vehicle_class", "car")
            color = CLASS_COLORS.get(v_class, DEFAULT_COLOR)
            tracker_id = t_dict.get("tracker_id", "TRK-00")
            display_id = t_dict.get("display_id", tracker_id.split("-")[-1] if "-" in tracker_id else tracker_id)
            conf = t_dict.get("confidence", 0.0)
            bbox = t_dict.get("bbox") or t_dict.get("last_bbox", [0, 0, 0, 0])
            trajectories = t_dict.get("trajectory_points", [])

            # 1. Draw motion trajectory trail
            if len(trajectories) > 1:
                pts = [np.array([int(p["cx"]), int(p["cy"])], np.int32) for p in trajectories if "cx" in p and "cy" in p]
                if len(pts) > 1:
                    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated, [pts_arr], isClosed=False, color=color, thickness=2, lineType=cv2.LINE_AA)
                    # Draw small circle at current head
                    cv2.circle(annotated, (pts[-1][0], pts[-1][1]), 4, (255, 255, 255), -1)

            # 2. Draw Bounding Box
            if len(bbox) == 4:
                x1, y1, x2, y2 = [int(v) for v in bbox]
                # Main box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2, cv2.LINE_AA)

                # Corner accent lines for sci-fi / command center HUD feel
                corner_len = min(15, (x2 - x1) // 3, (y2 - y1) // 3)
                if corner_len > 3:
                    # Top-left
                    cv2.line(annotated, (x1, y1), (x1 + corner_len, y1), (255, 255, 255), 2)
                    cv2.line(annotated, (x1, y1), (x1, y1 + corner_len), (255, 255, 255), 2)
                    # Bottom-right
                    cv2.line(annotated, (x2, y2), (x2 - corner_len, y2), (255, 255, 255), 2)
                    cv2.line(annotated, (x2, y2), (x2, y2 - corner_len), (255, 255, 255), 2)

                # Multi-line tactical HUD label
                v_type_str = v_class.upper()
                track_str = f"Track: {display_id}"
                plate_text = t_dict.get("plate_text", "UNKNOWN")
                ocr_conf = float(t_dict.get("ocr_confidence", 0.0))

                if plate_text and plate_text != "UNKNOWN" and ocr_conf > 0.0:
                    lines_to_draw = [
                        v_type_str,
                        track_str,
                        f"Plate: {plate_text}",
                        f"OCR: {int(ocr_conf * 100)}%"
                    ]
                else:
                    lines_to_draw = [
                        v_type_str,
                        track_str,
                        "Plate: UNKNOWN"
                    ]

                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.38
                thickness = 1
                line_height = 14
                
                # Calculate badge dimensions
                max_line_w = 0
                for line in lines_to_draw:
                    (tw, th), _ = cv2.getTextSize(line, font, font_scale, thickness)
                    if tw > max_line_w:
                        max_line_w = tw

                badge_w = max_line_w + 10
                badge_h = (len(lines_to_draw) * line_height) + 6

                # Place badge above box if space permits, otherwise inside top
                badge_y1 = max(4, y1 - badge_h - 4) if (y1 - badge_h - 4) >= 0 else y1 + 4
                badge_x1 = max(4, min(x1, w - badge_w - 4))
                badge_x2 = badge_x1 + badge_w
                badge_y2 = badge_y1 + badge_h

                # Dark glassmorphism badge background with colored border
                cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), (18, 22, 30), cv2.FILLED)
                cv2.rectangle(annotated, (badge_x1, badge_y1), (badge_x2, badge_y2), color, 1, cv2.LINE_AA)

                # Render each line
                for l_idx, line in enumerate(lines_to_draw):
                    text_y = badge_y1 + 13 + (l_idx * line_height)
                    text_color = (255, 255, 255)
                    if "Plate:" in line and "UNKNOWN" not in line:
                        text_color = (0, 255, 255)  # Yellow for recognized plate
                    elif "OCR:" in line:
                        text_color = (0, 240, 160)  # Green for OCR confidence
                    elif "UNKNOWN" in line:
                        text_color = (180, 180, 190)  # Muted grey
                    
                    cv2.putText(
                        annotated,
                        line,
                        (badge_x1 + 5, text_y),
                        font,
                        font_scale,
                        text_color,
                        thickness,
                        cv2.LINE_AA
                    )

        # 3. Telemetry Watermark (Top Right)
        status_text = f"CAM: {camera_id} | FPS: {fps:.1f} | TRACKS: {len(tracks)} | YOLOv8n ({self.device.upper()})"
        cv2.putText(
            annotated,
            status_text,
            (w - 380, 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 255),
            1,
            cv2.LINE_AA
        )

        return annotated

    def get_stats(self) -> Dict[str, Any]:
        """Returns runtime performance statistics and model metadata."""
        avg_ms = (self.total_inference_time / self.total_inferences) if self.total_inferences > 0 else 0.0
        fps = (1000.0 / avg_ms) if avg_ms > 0 else 0.0

        return {
            "model_name": settings.YOLO_MODEL_NAME,
            "device": self.device,
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "supported_classes": settings.SUPPORTED_VEHICLE_CLASSES,
            "confidence_threshold": settings.VEHICLE_DETECTION_CONFIDENCE,
            "avg_inference_ms": round(avg_ms, 2),
            "processing_fps": round(fps, 1),
            "total_inferences": self.total_inferences
        }

# Global detector instance
vehicle_detector = VehicleDetector()
