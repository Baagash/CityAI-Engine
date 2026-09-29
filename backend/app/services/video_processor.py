import cv2
import time
import uuid
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Generator, Tuple, List
from datetime import datetime, timezone

from app.config import settings
from app.services.vehicle_detector import vehicle_detector
from app.services.tracker import CameraObjectTracker
from app.services.anpr import anpr_engine
from app.services.vehicle_attributes import attribute_service
from app.services.appearance_embedding import appearance_extractor
from app.services.vehicle_reid import reid_service
from app.database import SessionLocal
from app.models.detection import DetectionRecord, CameraTrack
from app.models.plate import PlateRecord

logger = logging.getLogger("cityai.video_processor")

class VideoProcessor:
    """
    OpenCV Video Ingestion and Real-Time Multi-Object Tracking Pipeline.
    Manages LOCAL_VIDEO, WEBCAM, and RTSP stream sources with thread-safe capture,
    Ultralytics YOLO vehicle detection, per-camera multi-object tracking, and HUD annotation.
    """
    def __init__(self, camera_id: str, source_type: str, source_path: Optional[str] = None):
        self.camera_id = camera_id
        self.source_type = source_type.upper()  # LOCAL_VIDEO, WEBCAM, RTSP
        self.source_path = source_path
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self._stop_event = threading.Event()
        self.status = "STOPPED"  # ONLINE, OFFLINE, STARTING, STOPPED, ERROR
        self.error_message: Optional[str] = None
        
        # Stream telemetry
        self.fps: float = 25.0
        self.width: int = 0
        self.height: int = 0
        self.total_frames: int = 0
        self.current_frame_number: int = 0
        self.last_frame_time: float = 0.0
        self.processing_fps: float = 0.0
        self.last_inference_ms: float = 0.0
        
        # JPEG Frame buffers
        self.last_frame_bytes: Optional[bytes] = None
        self.last_annotated_frame_bytes: Optional[bytes] = None
        
        # Detection & Tracking State
        self.tracker = CameraObjectTracker(
            camera_id=self.camera_id,
            iou_threshold=settings.TRACKER_IOU_THRESHOLD,
            max_age=settings.TRACKER_MAX_AGE
        )
        self.current_detections: List[Dict[str, Any]] = []
        self.current_tracks: List[Dict[str, Any]] = []
        self.total_detections_count: int = 0
        
        # Synchronization
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._db_save_counter = 0

    def open(self) -> bool:
        """Opens the video capture source using OpenCV."""
        self.status = "STARTING"
        self.error_message = None

        try:
            if self.source_type == "WEBCAM":
                device_index = 0
                if self.source_path and self.source_path.isdigit():
                    device_index = int(self.source_path)
                self.cap = cv2.VideoCapture(device_index)
            elif self.source_type in ["LOCAL_VIDEO", "RTSP"]:
                if not self.source_path:
                    self.status = "ERROR"
                    self.error_message = f"No source path provided for {self.source_type}"
                    logger.error(f"[{self.camera_id}] {self.error_message}")
                    return False
                
                # Check file existence if local video
                if self.source_type == "LOCAL_VIDEO":
                    resolved_path = Path(self.source_path)
                    if not resolved_path.exists():
                        self.status = "ERROR"
                        self.error_message = f"Video file not found at: {self.source_path}"
                        logger.error(f"[{self.camera_id}] {self.error_message}")
                        return False

                self.cap = cv2.VideoCapture(str(self.source_path))
            else:
                self.status = "ERROR"
                self.error_message = f"Unsupported source type: {self.source_type}"
                return False

            if not self.cap or not self.cap.isOpened():
                self.status = "ERROR"
                self.error_message = f"OpenCV VideoCapture failed to open source: {self.source_path}"
                logger.error(f"[{self.camera_id}] {self.error_message}")
                return False

            # Extract source properties
            detected_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.fps = detected_fps if detected_fps > 0 and detected_fps <= 120 else 25.0
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 360
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            self.current_frame_number = 0
            self.status = "ONLINE"
            self.is_running = True
            self._stop_event.clear()

            logger.info(f"[{self.camera_id}] Video source opened: {self.width}x{self.height} @ {self.fps} FPS")
            return True

        except Exception as e:
            self.status = "ERROR"
            self.error_message = str(e)
            logger.error(f"[{self.camera_id}] Error opening source: {e}")
            return False

    def start(self) -> bool:
        """Starts the background frame reading loop."""
        with self._lock:
            if self.is_running and self._thread and self._thread.is_alive():
                return True
            
            if not self.open():
                return False
            
            self._thread = threading.Thread(target=self._capture_loop, daemon=True, name=f"cam-{self.camera_id}")
            self._thread.start()
            return True

    def _capture_loop(self):
        """Continuously reads frames, runs detection & tracking, and updates JPEG buffers."""
        frame_interval = 1.0 / max(self.fps, 1.0)
        fps_calc_time = time.time()
        frames_processed_since_calc = 0
        consecutive_read_errors = 0
        max_consecutive_errors = 5
        
        while not self._stop_event.is_set() and self.is_running:
            start_time = time.time()
            frame = None

            with self._lock:
                if not self.is_running or not self.cap or not self.cap.isOpened():
                    break
                ret, frame = self.cap.read()

            if not ret or frame is None:
                consecutive_read_errors += 1
                # End of stream handling
                if self.source_type == "LOCAL_VIDEO":
                    with self._lock:
                        if self.cap and self.cap.isOpened():
                            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = self.cap.read()
                        
                        # If seeking to 0 failed or did not yield a valid frame, cleanly reopen source
                        if (not ret or frame is None) and self.source_path:
                            try:
                                if self.cap:
                                    self.cap.release()
                                self.cap = cv2.VideoCapture(str(self.source_path))
                                if self.cap and self.cap.isOpened():
                                    ret, frame = self.cap.read()
                            except Exception as reopen_err:
                                logger.debug(f"[{self.camera_id}] Error reopening capture: {reopen_err}")

                    if not ret or frame is None:
                        if consecutive_read_errors >= max_consecutive_errors:
                            self.status = "ERROR"
                            self.error_message = f"Failed to read from video stream after {consecutive_read_errors} attempts"
                            logger.error(f"[{self.camera_id}] {self.error_message}")
                            break
                        time.sleep(0.1 * min(consecutive_read_errors, 5))
                        continue
                    else:
                        consecutive_read_errors = 0
                else:
                    if consecutive_read_errors >= max_consecutive_errors:
                        self.status = "OFFLINE"
                        self.error_message = "Video stream ended or unreachable"
                        logger.warning(f"[{self.camera_id}] {self.error_message}")
                        break
                    time.sleep(0.2)
                    continue
            else:
                consecutive_read_errors = 0

            self.current_frame_number += 1
            self.last_frame_time = time.time()
            now_dt = datetime.now(timezone.utc)

            # 1. Vehicle Detection & Tracking Loop
            if settings.ENABLE_DETECTION and vehicle_detector.is_initialized:
                should_detect = (self.current_frame_number % max(1, settings.FRAME_SKIP)) == 0
                if should_detect:
                    det_start = time.perf_counter()
                    detections = vehicle_detector.detect(
                        frame,
                        confidence_threshold=settings.VEHICLE_DETECTION_CONFIDENCE
                    )
                    self.last_inference_ms = (time.perf_counter() - det_start) * 1000.0
                    self.current_detections = detections
                    self.total_detections_count += len(detections)
                    
                    # Update local tracker
                    self.tracker.update(detections, self.current_frame_number, now_dt)

                    # Phase 4: Run ANPR & Vehicle Attribute Extraction on active tracks
                    if settings.ENABLE_ANPR and len(self.tracker.tracks) > 0:
                        h_f, w_f = frame.shape[:2]
                        for track_id, track_obj in self.tracker.tracks.items():
                            if track_obj.status == "ACTIVE":
                                frames_since_ocr = self.current_frame_number - track_obj.last_anpr_frame
                                if frames_since_ocr >= settings.ANPR_OCR_FRAME_INTERVAL or track_obj.last_anpr_frame == 0:
                                    bbox = track_obj.bbox
                                    x1 = max(0, int(bbox[0]))
                                    y1 = max(0, int(bbox[1]))
                                    x2 = min(w_f, int(bbox[2]))
                                    y2 = min(h_f, int(bbox[3]))

                                    if x2 > x1 + 15 and y2 > y1 + 15:
                                        v_crop = frame[y1:y2, x1:x2]
                                        dom_color, color_conf = attribute_service.extract_color(v_crop)
                                        plate_roi, rel_bbox = anpr_engine.localize_plate_roi(v_crop)
                                        ocr_res = anpr_engine.recognize_plate(plate_roi if plate_roi is not None else v_crop)

                                        track_obj.update_anpr_and_attributes(
                                            plate_text=ocr_res["plate_text"],
                                            ocr_confidence=ocr_res["ocr_confidence"],
                                            validation_status=ocr_res["validation_status"],
                                            vehicle_color=dom_color,
                                            color_confidence=color_conf,
                                            raw_text=ocr_res.get("raw_text"),
                                            plate_bbox=rel_bbox,
                                            frame_number=self.current_frame_number
                                        )

                    # Phase 5: Re-ID Visual Appearance Embedding & Global Vehicle Association
                    if settings.ENABLE_REID and len(self.tracker.tracks) > 0:
                        h_f, w_f = frame.shape[:2]
                        for track_id, track_obj in self.tracker.tracks.items():
                            if track_obj.status == "ACTIVE" and track_obj.total_frames >= settings.REID_MIN_STABLE_FRAMES:
                                if not track_obj.has_extracted_embedding:
                                    bbox = track_obj.bbox
                                    x1 = max(0, int(bbox[0]))
                                    y1 = max(0, int(bbox[1]))
                                    x2 = min(w_f, int(bbox[2]))
                                    y2 = min(h_f, int(bbox[3]))
                                    if x2 > x1 + 20 and y2 > y1 + 20:
                                        v_crop = frame[y1:y2, x1:x2].copy()
                                        track_obj.best_crop = v_crop
                                        track_obj.best_crop_confidence = track_obj.confidence
                                        emb = appearance_extractor.extract_embedding(v_crop)
                                        track_obj.embedding = emb
                                        track_obj.has_extracted_embedding = True

                                        def _reid_assoc_task(t_obj, cam_id, trk_id, crop_c, emb_c, p_text, v_type, v_color, ts):
                                            db_reid = SessionLocal()
                                            try:
                                                res = reid_service.associate_track_to_global_vehicle(
                                                    db=db_reid,
                                                    camera_id=cam_id,
                                                    tracker_id=trk_id,
                                                    image_crop=crop_c,
                                                    embedding=emb_c,
                                                    plate_text=p_text,
                                                    vehicle_type=v_type,
                                                    vehicle_color=v_color,
                                                    timestamp=ts
                                                )
                                                t_obj.global_vehicle_id = res.get("global_vehicle_id")
                                                t_obj.reid_decision = res.get("decision", "MATCH")
                                                t_obj.reid_reason = res.get("reason_code", "MATCHED")
                                            except Exception as e:
                                                logger.warning(f"[{cam_id}] Re-ID background association error: {e}")
                                            finally:
                                                db_reid.close()

                                        threading.Thread(
                                            target=_reid_assoc_task,
                                            args=(
                                                track_obj,
                                                self.camera_id,
                                                track_obj.local_tracker_id,
                                                v_crop,
                                                emb,
                                                track_obj.plate_text,
                                                track_obj.vehicle_class,
                                                track_obj.vehicle_color,
                                                now_dt
                                            ),
                                            daemon=True
                                        ).start()

                    self.current_tracks = self.tracker.get_active_tracks()

                    # Save detection and plate observation samples to SQLite DB periodically
                    self._db_save_counter += 1
                    if self._db_save_counter % 10 == 0 and len(detections) > 0:
                        self._persist_detections_sample(detections, now_dt)

            # 2. Encode Raw Frame to JPEG
            raw_success, raw_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            
            # 3. Render Annotated Frame with HUD
            annotated_frame = vehicle_detector.draw_hud_annotations(
                frame=frame,
                tracks=self.current_tracks,
                raw_detections=self.current_detections,
                camera_id=self.camera_id,
                fps=self.processing_fps
            )
            ann_success, ann_buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 78])

            with self._lock:
                if raw_success:
                    self.last_frame_bytes = raw_buffer.tobytes()
                if ann_success:
                    self.last_annotated_frame_bytes = ann_buffer.tobytes()

            # Calculate FPS
            frames_processed_since_calc += 1
            if time.time() - fps_calc_time >= 1.0:
                self.processing_fps = frames_processed_since_calc / (time.time() - fps_calc_time)
                frames_processed_since_calc = 0
                fps_calc_time = time.time()

            # Pace loop to match native video FPS
            elapsed = time.time() - start_time
            sleep_duration = max(0.001, frame_interval - elapsed)
            time.sleep(sleep_duration)

        self._cleanup_resources()

    def _persist_detections_sample(self, detections: List[Dict[str, Any]], timestamp: datetime):
        """Asynchronously persists a sample of detected vehicles to the SQLite database."""
        def _db_worker():
            db = SessionLocal()
            try:
                # Map active tracker IDs to global IDs
                active_gids = {}
                for t in self.current_tracks:
                    t_id = t.get("tracker_id")
                    g_id = t.get("global_vehicle_id")
                    if t_id and g_id:
                        active_gids[t_id] = g_id

                records = []
                for idx, det in enumerate(detections[:4]):  # persist up to 4 per sample
                    det_id = f"DET-{self.camera_id}-{uuid.uuid4().hex[:8].upper()}"
                    bbox = det["bbox"]
                    center = det["center"]
                    
                    matched_trk = None
                    matched_gid = None
                    if idx < len(self.current_tracks):
                        matched_trk = self.current_tracks[idx].get("tracker_id")
                        matched_gid = self.current_tracks[idx].get("global_vehicle_id")

                    rec = DetectionRecord(
                        detection_id=det_id,
                        camera_id=self.camera_id,
                        tracker_id=matched_trk or f"{self.camera_id}-TRK-LCL",
                        global_vehicle_id=matched_gid,
                        frame_number=self.current_frame_number,
                        timestamp=timestamp,
                        vehicle_class=det["class"],
                        confidence=det["confidence"],
                        bbox_x1=bbox[0],
                        bbox_y1=bbox[1],
                        bbox_x2=bbox[2],
                        bbox_y2=bbox[3],
                        center_x=center[0],
                        center_y=center[1],
                        frame_width=self.width,
                        frame_height=self.height
                    )
                    records.append(rec)
                if records:
                    db.add_all(records)

                # Persist plate observation samples if present
                plate_records = []
                for t in self.current_tracks:
                    t_plate = t.get("plate_text", "UNKNOWN")
                    if t_plate and t_plate != "UNKNOWN":
                        obs_id = f"PLT-{self.camera_id}-{uuid.uuid4().hex[:8].upper()}"
                        p_rec = PlateRecord(
                            observation_id=obs_id,
                            camera_id=self.camera_id,
                            tracker_id=t.get("tracker_id", f"{self.camera_id}-TRK-00"),
                            global_vehicle_id=t.get("global_vehicle_id"),
                            frame_number=self.current_frame_number,
                            timestamp=timestamp,
                            plate_text=t_plate,
                            raw_text=t.get("raw_text"),
                            ocr_confidence=t.get("ocr_confidence", 0.0),
                            detection_confidence=t.get("confidence", 0.0),
                            validation_status=t.get("validation_status", "UNKNOWN"),
                            vehicle_type=t.get("vehicle_class", "car"),
                            vehicle_color=t.get("vehicle_color", "UNKNOWN"),
                            color_confidence=t.get("color_confidence", 0.0)
                        )
                        plate_records.append(p_rec)

                if plate_records:
                    db.add_all(plate_records)

                db.commit()
            except Exception as e:
                logger.warning(f"[{self.camera_id}] Error saving detection records to DB: {e}")
            finally:
                db.close()

        threading.Thread(target=_db_worker, daemon=True).start()

    def get_latest_frame_bytes(self, annotated: bool = False) -> Optional[bytes]:
        """Returns the most recent JPEG frame bytes (raw or AI-annotated)."""
        with self._lock:
            if annotated and self.last_annotated_frame_bytes:
                return self.last_annotated_frame_bytes
            return self.last_frame_bytes

    def get_frame_info(self) -> Dict[str, Any]:
        """Returns current operational telemetry and AI detection metrics."""
        return {
            "camera_id": self.camera_id,
            "status": self.status,
            "is_streaming": self.is_running,
            "fps": round(self.fps, 1),
            "processing_fps": round(self.processing_fps, 1),
            "inference_ms": round(self.last_inference_ms, 1),
            "resolution": f"{self.width}x{self.height}" if self.width and self.height else "N/A",
            "width": self.width,
            "height": self.height,
            "frame_number": self.current_frame_number,
            "timestamp": datetime.now(timezone.utc).isoformat() if self.is_running else None,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "active_tracks_count": len(self.current_tracks),
            "active_tracks": self.current_tracks,
            "current_detections_count": len(self.current_detections),
            "total_detections_count": self.total_detections_count,
            "error": self.error_message
        }

    def _cleanup_resources(self):
        """Releases the VideoCapture resource safely."""
        with self._lock:
            if self.status not in ["ERROR", "OFFLINE"]:
                self.status = "STOPPED"
            if self.cap:
                try:
                    self.cap.release()
                except Exception as e:
                    logger.warning(f"[{self.camera_id}] Error releasing capture: {e}")
                self.cap = None
        logger.info(f"[{self.camera_id}] VideoCapture released cleanly.")

    def release(self):
        """Stops the capture thread cleanly and releases VideoCapture without racing."""
        self.is_running = False
        self._stop_event.set()
        
        # Wait for capture loop to exit before freeing memory
        if self._thread and self._thread.is_alive() and threading.current_thread() != self._thread:
            self._thread.join(timeout=1.0)

        self._cleanup_resources()


class CameraStreamManager:
    """
    Singleton Stream Manager for Ingestion, AI Detection & Tracking, and MJPEG streaming.
    """
    def __init__(self):
        self._processors: Dict[str, VideoProcessor] = {}
        self._lock = threading.Lock()

    def start_camera(self, camera_id: str, source_type: str, source_path: Optional[str] = None) -> Tuple[bool, str]:
        """Starts video ingestion and AI tracking for a camera."""
        with self._lock:
            if camera_id in self._processors and self._processors[camera_id].is_running:
                return True, "Camera stream is already running."
            
            processor = VideoProcessor(camera_id, source_type, source_path)
            success = processor.start()
            self._processors[camera_id] = processor
            
            if success:
                return True, "Camera stream started successfully with real AI tracking."
            else:
                return False, processor.error_message or "Failed to start camera video stream."

    def stop_camera(self, camera_id: str) -> Tuple[bool, str]:
        """Stops video ingestion and cleanly releases resources."""
        processor = None
        with self._lock:
            if camera_id in self._processors:
                processor = self._processors[camera_id]
                del self._processors[camera_id]

        if processor:
            processor.release()
            return True, "Camera stream stopped."
        return True, "Camera was not running."

    def get_camera_status(self, camera_id: str, fallback_source_type: str = "LOCAL_VIDEO", fallback_path: Optional[str] = None) -> Dict[str, Any]:
        """Returns live or offline telemetry for a camera."""
        with self._lock:
            if camera_id in self._processors:
                return self._processors[camera_id].get_frame_info()
            return {
                "camera_id": camera_id,
                "status": "STOPPED",
                "is_streaming": False,
                "fps": 0.0,
                "processing_fps": 0.0,
                "inference_ms": 0.0,
                "resolution": "N/A",
                "width": 0,
                "height": 0,
                "frame_number": 0,
                "timestamp": None,
                "source_type": fallback_source_type,
                "source_path": fallback_path,
                "active_tracks_count": 0,
                "active_tracks": [],
                "current_detections_count": 0,
                "total_detections_count": 0,
                "error": None
            }

    def is_camera_running(self, camera_id: str) -> bool:
        """Returns True if the camera is currently active."""
        with self._lock:
            return camera_id in self._processors and self._processors[camera_id].is_running

    def get_active_streams_count(self) -> int:
        """Returns the number of active video streams."""
        with self._lock:
            return sum(1 for p in self._processors.values() if p.is_running)

    def get_all_active_tracks(self) -> List[Dict[str, Any]]:
        """Aggregates all active vehicle tracks across all running cameras."""
        all_tracks: List[Dict[str, Any]] = []
        with self._lock:
            processors = list(self._processors.values())
        for p in processors:
            all_tracks.extend(p.current_tracks)
        return all_tracks

    def get_camera_active_tracks(self, camera_id: str) -> List[Dict[str, Any]]:
        """Returns active tracks for a specific camera."""
        with self._lock:
            if camera_id in self._processors:
                return self._processors[camera_id].current_tracks
        return []

    def get_all_latest_detections(self) -> List[Dict[str, Any]]:
        """Aggregates latest detections across all active cameras."""
        all_dets: List[Dict[str, Any]] = []
        with self._lock:
            processors = list(self._processors.values())
        for p in processors:
            for d in p.current_detections:
                all_dets.append({
                    "camera_id": p.camera_id,
                    "frame_number": p.current_frame_number,
                    "vehicle_class": d.get("class", "car"),
                    "confidence": d.get("confidence", 0.0),
                    "bbox": d.get("bbox", []),
                    "center": d.get("center", [])
                })
        return all_dets

    def generate_mjpeg_stream(self, camera_id: str, annotated: bool = False) -> Generator[bytes, None, None]:
        """
        Yields multipart MJPEG frame chunks for HTTP streaming response.
        Supports both raw camera stream and real AI HUD annotated stream.
        """
        inactive_ticks = 0
        max_inactive_ticks = 25  # ~5 seconds of grace period for camera startup

        while True:
            processor = None
            with self._lock:
                if camera_id in self._processors:
                    p = self._processors[camera_id]
                    if p.is_running:
                        processor = p
                    elif p.status == "ERROR":
                        # If camera processor encountered a fatal error, exit stream gracefully
                        break

            if not processor or not processor.is_running:
                inactive_ticks += 1
                if inactive_ticks > max_inactive_ticks:
                    break
                time.sleep(0.2)
                continue

            inactive_ticks = 0
            frame_bytes = processor.get_latest_frame_bytes(annotated=annotated)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(1.0 / max(processor.fps, 10.0))

# Global Stream Manager instance
stream_manager = CameraStreamManager()
