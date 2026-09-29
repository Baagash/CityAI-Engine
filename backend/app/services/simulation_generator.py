import cv2
import time
import math
import random
import uuid
import threading
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.services.weather_engine import weather_service
from app.services.tracker import MultiObjectTracker
from app.services.anpr import anpr_engine
from app.services.vehicle_attributes import attribute_service
from app.services.duplicate_plate import duplicate_plate_engine
from app.services.trajectory_engine import topology_engine
from app.services.traffic_analytics import traffic_analytics
from app.database import SessionLocal
from app.models.camera import Camera
from app.models.vehicle import Vehicle
from app.models.detection import Detection
from app.models.plate import Plate
from app.models.trajectory import Trajectory
from app.models.alert import Alert
from app.models.registry import DemoRegistryVehicle

# Vehicle definitions for simulator
VEHICLE_PROTOTYPES = [
    {"plate": "TN38AB1234", "type": "sedan", "color": "WHITE", "base_speed": 55.0},
    {"plate": "KA05MB9912", "type": "suv", "color": "BLACK", "base_speed": 62.0},
    {"plate": "DL01CA1024", "type": "sedan", "color": "SILVER", "base_speed": 48.0},
    {"plate": "MH12TR4500", "type": "truck", "color": "BLUE", "base_speed": 40.0},
    {"plate": "TN09Q8821", "type": "motorcycle", "color": "RED", "base_speed": 60.0},
    {"plate": "AP09BZ3344", "type": "bus", "color": "YELLOW", "base_speed": 42.0},
    {"plate": "TN22CX7711", "type": "suv", "color": "WHITE", "base_speed": 58.0},
    {"plate": "KL07DD5566", "type": "sedan", "color": "BLUE", "base_speed": 50.0},
]

COLOR_RGB = {
    "WHITE": (240, 240, 245),
    "BLACK": (35, 35, 40),
    "SILVER": (180, 185, 190),
    "RED": (40, 40, 220),
    "BLUE": (210, 110, 40),
    "YELLOW": (30, 210, 230),
    "GREEN": (50, 180, 60),
    "UNKNOWN": (120, 120, 120)
}

class SimVehicle:
    def __init__(self, plate: str, v_type: str, color: str, lane: int, y_pos: float, speed: float, camera_id: str):
        self.plate = plate
        self.v_type = v_type
        self.color = color
        self.lane = lane  # 0, 1, 2
        self.y_pos = y_pos  # 0.0 to 1.0 (top to bottom)
        self.speed = speed
        self.camera_id = camera_id
        self.id_num = random.randint(10, 99)
        self.width = 75 if v_type in ["sedan", "suv"] else (110 if v_type in ["truck", "bus"] else 40)
        self.height = 110 if v_type in ["sedan", "suv"] else (160 if v_type in ["truck", "bus"] else 60)

class TrafficSimulator:
    def __init__(self):
        self.is_running = False
        self._thread = None
        self.camera_ids = ["CAM01", "CAM02", "CAM03", "CAM04"]
        self.camera_sim_vehicles: Dict[str, List[SimVehicle]] = {cid: [] for cid in self.camera_ids}
        self.trackers: Dict[str, MultiObjectTracker] = {cid: MultiObjectTracker(cid) for cid in self.camera_ids}
        self.latest_frames: Dict[str, np.ndarray] = {}
        self.active_scenarios: List[str] = []
        self._frame_count = 0
        self._lock = threading.Lock()
        self._init_demo_vehicles()

    def _init_demo_vehicles(self):
        for cid in self.camera_ids:
            vehicles = []
            for i in range(random.randint(2, 4)):
                proto = random.choice(VEHICLE_PROTOTYPES)
                v = SimVehicle(
                    plate=proto["plate"],
                    v_type=proto["type"],
                    color=proto["color"],
                    lane=i % 3,
                    y_pos=random.uniform(0.1, 0.8),
                    speed=proto["base_speed"] + random.uniform(-5, 5),
                    camera_id=cid
                )
                vehicles.append(v)
            self.camera_sim_vehicles[cid] = vehicles

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            print("[Simulator] Multi-Camera Traffic Simulation Engine started.")

    def stop(self):
        self.is_running = False

    def trigger_scenario(self, scenario_type: str, weather: Optional[str] = None) -> Dict[str, Any]:
        """
        Triggers explicit evaluation scenarios:
        1. CLONED_PLATE: Plate 'TN38AB1234' on White Sedan at CAM01 and Black SUV at CAM04.
        2. IMPOSSIBLE_SPEED: Plate 'KA05MB9912' arrives at CAM04 just 10s after CAM01.
        3. STOLEN_VEHICLE: Spawns 'DL01CA1024' (Registered as STOLEN).
        4. CONGESTION: Causes massive slowdown and vehicle cluster on CAM03.
        5. NORMAL_TRAFFIC: Resets to standard baseline flow.
        """
        if weather:
            weather_service.set_weather(weather)

        with self._lock:
            if scenario_type == "CLONED_PLATE":
                # Inject White Sedan at CAM01
                self.camera_sim_vehicles["CAM01"].append(
                    SimVehicle("TN38AB1234", "sedan", "WHITE", 1, 0.3, 52.0, "CAM01")
                )
                # Inject conflicting Black SUV with SAME plate at CAM04
                self.camera_sim_vehicles["CAM04"].append(
                    SimVehicle("TN38AB1234", "suv", "BLACK", 2, 0.4, 65.0, "CAM04")
                )
                msg = "Triggered POSSIBLE CLONED PLATE scenario: Plate 'TN38AB1234' active simultaneously on CAM01 (White Sedan) & CAM04 (Black SUV)."

            elif scenario_type == "IMPOSSIBLE_SPEED":
                # Spawn vehicle at CAM01 then immediately at CAM04
                self.camera_sim_vehicles["CAM01"].append(
                    SimVehicle("KA05MB9912", "suv", "BLACK", 0, 0.8, 80.0, "CAM01")
                )
                self.camera_sim_vehicles["CAM04"].append(
                    SimVehicle("KA05MB9912", "suv", "BLACK", 1, 0.2, 160.0, "CAM04")
                )
                msg = "Triggered IMPOSSIBLE TRAVEL scenario: Vehicle 'KA05MB9912' transiting CAM01->CAM04 (18km) in seconds."

            elif scenario_type == "CONGESTION":
                # Add 8 slow vehicles to CAM03
                self.camera_sim_vehicles["CAM03"].clear()
                for i in range(7):
                    proto = random.choice(VEHICLE_PROTOTYPES)
                    self.camera_sim_vehicles["CAM03"].append(
                        SimVehicle(proto["plate"], proto["v_type"], proto["color"], i % 3, 0.1 + (i * 0.12), 12.0, "CAM03")
                    )
                msg = "Triggered TRAFFIC CONGESTION scenario on CAM03 (IT Expressway Tollway)."

            elif scenario_type == "STOLEN_VEHICLE":
                self.camera_sim_vehicles["CAM02"].append(
                    SimVehicle("DL01CA1024", "sedan", "SILVER", 1, 0.2, 45.0, "CAM02")
                )
                msg = "Triggered STOLEN VEHICLE SIGHTING scenario: Plate 'DL01CA1024' spawned at CAM02."

            else:
                self._init_demo_vehicles()
                msg = "Reset to NORMAL traffic simulation flow."

        return {"status": "SUCCESS", "scenario": scenario_type, "message": msg, "weather": weather_service.current_weather}

    def _run_loop(self):
        while self.is_running:
            start_t = time.time()
            self._frame_count += 1

            for cid in self.camera_ids:
                frame, detections_data = self._generate_camera_frame(cid)
                with self._lock:
                    self.latest_frames[cid] = frame

                # Every 15 frames (~1.5s), run AI pipeline and update database
                if self._frame_count % 15 == 0:
                    self._process_ai_pipeline(cid, detections_data)

            elapsed = time.time() - start_t
            sleep_time = max(0.02, 0.10 - elapsed)
            time.sleep(sleep_time)

    def _generate_camera_frame(self, camera_id: str) -> tuple[np.ndarray, List[Dict[str, Any]]]:
        # 640x360 CCTV Resolution
        h, w = 360, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)

        # Weather context
        weather = weather_service.current_weather
        is_night = weather == "NIGHT"
        is_rain = weather == "RAIN"
        is_fog = weather == "FOG"

        # 1. Road tarmac & lanes
        tarmac_color = (35, 35, 40) if not is_night else (18, 18, 22)
        frame[:] = tarmac_color

        # Road boundaries & lane markings
        lane_x = [160, 270, 380, 490]
        # Road shoulder
        cv2.rectangle(frame, (0, 0), (140, h), (30, 45, 30) if not is_night else (12, 18, 12), -1)
        cv2.rectangle(frame, (510, 0), (w, h), (30, 45, 30) if not is_night else (12, 18, 12), -1)

        # Dashed lane dividers
        dash_offset = int((self._frame_count * 6) % 40)
        for x in [270, 380]:
            for y in range(-40 + dash_offset, h + 40, 40):
                cv2.line(frame, (x, y), (x, y + 20), (200, 200, 200) if not is_night else (120, 120, 120), 2)

        # 2. Update and draw vehicles
        detections_data = []
        vehicles = self.camera_sim_vehicles.get(camera_id, [])

        for v in list(vehicles):
            # Advance vehicle position down the road
            v.y_pos += (v.speed / 2800.0)
            if v.y_pos > 1.15:
                # Wrap around or replace
                v.y_pos = -0.15
                proto = random.choice(VEHICLE_PROTOTYPES)
                v.plate = proto["plate"]
                v.v_type = proto["type"]
                v.color = proto["color"]
                v.speed = proto["base_speed"] + random.uniform(-5, 5)

            # Calculate box position
            lane_center_x = lane_x[v.lane] + 55
            top_y = int(v.y_pos * h)
            bottom_y = top_y + v.height
            left_x = lane_center_x - (v.width // 2)
            right_x = lane_center_x + (v.width // 2)

            if top_y < h and bottom_y > 0:
                # Draw vehicle body
                body_color = COLOR_RGB.get(v.color, (180, 180, 180))
                if is_night:
                    # Darken body color slightly
                    body_color = tuple(int(c * 0.6) for c in body_color)

                cv2.rectangle(frame, (left_x, top_y), (right_x, bottom_y), body_color, -1)
                # Windshield & Roof
                cv2.rectangle(frame, (left_x + 8, top_y + 15), (right_x - 8, top_y + 40), (20, 25, 30), -1)
                # Rear window
                cv2.rectangle(frame, (left_x + 8, bottom_y - 25), (right_x - 8, bottom_y - 12), (20, 25, 30), -1)

                # Headlights / Taillights
                if is_night:
                    # Taillight red glow
                    cv2.circle(frame, (left_x + 10, bottom_y - 4), 6, (0, 0, 255), -1)
                    cv2.circle(frame, (right_x - 10, bottom_y - 4), 6, (0, 0, 255), -1)
                    # Headlight beam forward
                    cv2.circle(frame, (left_x + 10, top_y + 4), 5, (200, 255, 255), -1)
                    cv2.circle(frame, (right_x - 10, top_y + 4), 5, (200, 255, 255), -1)

                # Plate rectangle on rear
                plate_y1 = bottom_y - 10
                plate_y2 = bottom_y - 2
                plate_x1 = lane_center_x - 22
                plate_x2 = lane_center_x + 22
                cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x2, plate_y2), (255, 255, 255), -1)
                cv2.rectangle(frame, (plate_x1, plate_y1), (plate_x2, plate_y2), (0, 0, 0), 1)

                # AI Bounding Box HUD
                bbox_color = (0, 242, 254)  # Cyan
                cv2.rectangle(frame, (left_x - 4, top_y - 4), (right_x + 4, bottom_y + 4), bbox_color, 2)
                
                # HUD Tag: Tracker ID + Class + Speed
                tag_text = f"{camera_id}-V{v.id_num} | {v.v_type.upper()} | {v.speed:.0f}km/h"
                cv2.rectangle(frame, (left_x - 4, top_y - 22), (left_x + len(tag_text) * 8 + 6, top_y - 4), (15, 23, 42), -1)
                cv2.putText(frame, tag_text, (left_x, top_y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 242, 254), 1)

                # ANPR Plate banner above box
                plate_tag = f"ANPR: {v.plate}"
                cv2.rectangle(frame, (left_x - 4, bottom_y + 6), (left_x + len(plate_tag) * 8 + 4, bottom_y + 22), (16, 185, 129), -1)
                cv2.putText(frame, plate_tag, (left_x, bottom_y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 0, 0), 1)

                detections_data.append({
                    "bbox": [left_x, top_y, right_x, bottom_y],
                    "class": v.v_type,
                    "confidence": 0.94,
                    "color": v.color,
                    "color_confidence": 0.90,
                    "speed_estimate": v.speed,
                    "plate_text": v.plate,
                    "sim_id": v.id_num
                })

        # 3. Apply Weather Post-Processing Overlays
        if is_rain:
            # Rain streaks
            for _ in range(35):
                rx = random.randint(0, w)
                ry = random.randint(0, h)
                cv2.line(frame, (rx, ry), (rx - 4, ry + 12), (190, 205, 220), 1)
        elif is_fog:
            # Fog haze overlay
            fog_overlay = np.full((h, w, 3), 190, dtype=np.uint8)
            frame = cv2.addWeighted(frame, 0.65, fog_overlay, 0.35, 0)

        # 4. Top CCTV HUD Overlay (Camera ID, Timestamp, Weather, Live FPS)
        cv2.rectangle(frame, (0, 0), (w, 32), (15, 23, 42), -1)
        cv2.circle(frame, (16, 16), 5, (0, 255, 0), -1)  # Live indicator
        cctv_title = f"LIVE CCTV: {camera_id} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ENV: {weather}"
        cv2.putText(frame, cctv_title, (30, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
        cv2.putText(frame, "AI ACTIVE", (w - 85, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 242, 254), 1)

        return frame, detections_data

    def _process_ai_pipeline(self, camera_id: str, detections: List[Dict[str, Any]]):
        """Processes detections through tracking, ANPR, Re-ID, trajectory, and duplicate plate correlation."""
        if not detections:
            return

        db = SessionLocal()
        try:
            # Update telemetry for traffic analytics
            avg_speed = sum(d.get("speed_estimate", 50.0) for d in detections) / max(1, len(detections))
            traffic_analytics.record_camera_telemetry(camera_id, len(detections), avg_speed)

            # Query registered vehicles cache
            all_registered = {r.registration_number: r for r in db.query(DemoRegistryVehicle).all()}

            for det in detections:
                plate_text = det.get("plate_text")
                v_type = det.get("class", "sedan")
                color = det.get("color", "WHITE")
                speed = det.get("speed_estimate", 50.0)
                sim_id = det.get("sim_id", 1)
                tracker_id = f"{camera_id}-V{sim_id}"

                # Calculate OCR confidence with weather penalty
                base_ocr_conf = 0.96
                adj_ocr, adj_color, _ = weather_service.adjust_confidence(base_ocr_conf, 0.90)

                # Fetch or create Global Vehicle identity (VEH-XXXXXX)
                global_vehicle = db.query(Vehicle).filter(Vehicle.primary_plate == plate_text).first()
                if not global_vehicle:
                    global_id = f"VEH-{random.randint(100000, 999999)}"
                    global_vehicle = Vehicle(
                        global_id=global_id,
                        primary_plate=plate_text,
                        vehicle_type=v_type,
                        color=color,
                        confidence=adj_ocr,
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        total_sightings=1
                    )
                    db.add(global_vehicle)
                    db.commit()
                    db.refresh(global_vehicle)
                else:
                    global_vehicle.last_seen = datetime.utcnow()
                    global_vehicle.total_sightings += 1

                # Save Detection record
                detection_rec = Detection(
                    detection_id=f"DET-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}",
                    camera_id=camera_id,
                    vehicle_id=global_vehicle.id,
                    tracker_id=tracker_id,
                    frame_number=self._frame_count,
                    timestamp=datetime.utcnow(),
                    vehicle_class=v_type,
                    confidence=0.92,
                    bbox_x1=det["bbox"][0],
                    bbox_y1=det["bbox"][1],
                    bbox_x2=det["bbox"][2],
                    bbox_y2=det["bbox"][3],
                    color=color,
                    color_confidence=adj_color,
                    speed_estimate=speed,
                    direction_heading="Southbound"
                )
                db.add(detection_rec)
                db.commit()
                db.refresh(detection_rec)

                # Save Plate record
                plate_rec = Plate(
                    detection_id=detection_rec.id,
                    camera_id=camera_id,
                    plate_text=plate_text,
                    raw_text=plate_text,
                    ocr_confidence=adj_ocr,
                    validation_status="VALID" if adj_ocr >= 0.75 else "LOW_CONFIDENCE",
                    timestamp=datetime.utcnow()
                )
                db.add(plate_rec)

                # Camera metadata for trajectory
                cam_meta = topology_engine.get_camera(camera_id)
                lat = cam_meta["lat"] if cam_meta else 13.0827
                lon = cam_meta["lon"] if cam_meta else 80.2707

                # Save Trajectory point
                traj_rec = Trajectory(
                    vehicle_id=global_vehicle.id,
                    camera_id=camera_id,
                    timestamp=datetime.utcnow(),
                    latitude=lat,
                    longitude=lon,
                    speed_kmh=speed,
                    route_confidence=1.0
                )
                db.add(traj_rec)
                db.commit()

                # RUN DUPLICATE / CLONED PLATE & IMPOSSIBLE TRAVEL CORRELATION ENGINE
                # Fetch recent sightings of this plate across other cameras
                recent_sightings = db.query(Detection).join(Plate).filter(
                    Plate.plate_text == plate_text,
                    Detection.id != detection_rec.id
                ).order_by(Detection.timestamp.desc()).limit(5).all()

                hist_obs = []
                for s in recent_sightings:
                    hist_obs.append({
                        "camera_id": s.camera_id,
                        "timestamp": s.timestamp,
                        "vehicle_type": s.vehicle_class,
                        "color": s.color,
                        "plate_text": plate_text,
                        "ocr_confidence": s.plate.ocr_confidence if s.plate else 0.9
                    })

                new_obs = {
                    "camera_id": camera_id,
                    "timestamp": datetime.utcnow(),
                    "vehicle_type": v_type,
                    "color": color,
                    "plate_text": plate_text,
                    "confidence": 0.92,
                    "ocr_confidence": adj_ocr
                }

                reg_info = None
                if plate_text in all_registered:
                    reg_obj = all_registered[plate_text]
                    reg_info = {
                        "registration_number": reg_obj.registration_number,
                        "vehicle_type": reg_obj.vehicle_type,
                        "registered_color": reg_obj.registered_color,
                        "make_model": reg_obj.make_model,
                        "owner_name": reg_obj.owner_name,
                        "status": reg_obj.status
                    }

                alert_dict = duplicate_plate_engine.analyze_sighting(new_obs, hist_obs, reg_info)
                if alert_dict:
                    # Check if similar alert created recently to avoid flooding
                    existing_alert = db.query(Alert).filter(
                        Alert.plate_text == plate_text,
                        Alert.alert_type == alert_dict["alert_type"],
                        Alert.status == "REQUIRES_VERIFICATION"
                    ).first()

                    if not existing_alert:
                        new_alert = Alert(
                            alert_id=f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}-{uuid.uuid4().hex[:6]}",
                            alert_type=alert_dict["alert_type"],
                            severity=alert_dict["severity"],
                            status="REQUIRES_VERIFICATION",
                            plate_text=plate_text,
                            vehicle_id=global_vehicle.id,
                            source_camera_id=alert_dict.get("source_camera_id"),
                            target_camera_id=alert_dict.get("target_camera_id"),
                            title=alert_dict["title"],
                            description=alert_dict["description"],
                            evidence_score=alert_dict["evidence_score"],
                            details_json=alert_dict.get("details_json"),
                            timestamp=datetime.utcnow()
                        )
                        db.add(new_alert)
                        db.commit()

        except Exception as e:
            db.rollback()
            print(f"[Simulator Pipeline Error]: {e}")
        finally:
            db.close()

    def get_latest_frame_jpeg(self, camera_id: str) -> Optional[bytes]:
        with self._lock:
            frame = self.latest_frames.get(camera_id)
            if frame is None:
                # Return placeholder frame
                frame = np.zeros((360, 640, 3), dtype=np.uint8)
                cv2.putText(frame, f"INITIALIZING {camera_id}...", (160, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 242, 254), 2)
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                return buffer.tobytes()
        return None

traffic_simulator = TrafficSimulator()
