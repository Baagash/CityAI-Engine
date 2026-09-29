import cv2
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger("cityai.video_generator")

def generate_demo_traffic_video(output_path: Path, duration_seconds: int = 8, fps: int = 25, width: int = 640, height: int = 360) -> bool:
    """
    Generates a realistic traffic video clip for testing and local zero-dependency demonstrations.
    Composites real vehicle photographic elements onto multi-lane urban roadways so that
    Ultralytics YOLO accurately detects vehicle classes and ByteTrack tracks them consistently.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Write to atomic temporary file first
        temp_path = output_path.with_suffix(".tmp.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(str(temp_path), fourcc, fps, (width, height))

        total_frames = duration_seconds * fps

        # Load real vehicle texture from Ultralytics assets if available
        vehicle_crop = None
        try:
            from ultralytics.utils import ASSETS
            asset_bus = ASSETS / 'bus.jpg'
            if asset_bus.exists():
                bus_img = cv2.imread(str(asset_bus))
                if bus_img is not None:
                    # Crop bus body
                    vehicle_crop = bus_img[231:756, 23:805]
        except Exception as e:
            logger.debug(f"Could not load asset crop: {e}")

        # Vehicle simulation states
        v_width, v_height = 140, 80
        if vehicle_crop is not None:
            v_resized = cv2.resize(vehicle_crop, (v_width, v_height))
        else:
            v_resized = None

        # Two vehicles moving in opposite lanes
        v1_x, v1_y, v1_speed = 30.0, 130, 3.5
        v2_x, v2_y, v2_speed = 450.0, 220, -3.0

        for frame_idx in range(total_frames):
            # 1. Dark tactical asphalt canvas
            frame = np.full((height, width, 3), 28, dtype=np.uint8)

            # 2. Road surface
            cv2.rectangle(frame, (0, 100), (width, 320), (55, 62, 75), -1)
            cv2.line(frame, (0, 100), (width, 100), (90, 100, 120), 2)
            cv2.line(frame, (0, 320), (width, 320), (90, 100, 120), 2)

            # 3. Center dividing lane markings
            dash_len = 30
            gap_len = 25
            cycle = dash_len + gap_len
            for lane_x in range(-cycle, width + cycle, cycle):
                offset = (lane_x + (frame_idx * 3)) % (width + cycle) - cycle
                cv2.line(frame, (int(offset), 210), (int(offset + dash_len), 210), (220, 220, 220), 2)

            # 4. Animate and overlay Vehicle 1 (Eastbound Lane)
            v1_x = (v1_x + v1_speed) % (width + v_width)
            actual_v1_x = int(v1_x - v_width / 2)
            if 0 <= actual_v1_x < width - v_width and 0 <= v1_y < height - v_height:
                if v_resized is not None:
                    frame[v1_y:v1_y + v_height, actual_v1_x:actual_v1_x + v_width] = v_resized
                else:
                    cv2.rectangle(frame, (actual_v1_x, v1_y), (actual_v1_x + v_width, v1_y + v_height), (0, 165, 255), -1)

            # 5. Animate and overlay Vehicle 2 (Westbound Lane)
            v2_x = (v2_x + v2_speed)
            if v2_x < -v_width:
                v2_x = width + v_width
            actual_v2_x = int(v2_x - v_width / 2)
            if 0 <= actual_v2_x < width - v_width and 0 <= v2_y < height - v_height:
                if v_resized is not None:
                    flipped_v = cv2.flip(v_resized, 1)
                    frame[v2_y:v2_y + v_height, actual_v2_x:actual_v2_x + v_width] = flipped_v
                else:
                    cv2.rectangle(frame, (actual_v2_x, v2_y), (actual_v2_x + v_width, v2_y + v_height), (220, 180, 0), -1)

            # 6. Overlay telemetry timestamp watermark
            cv2.putText(frame, f"CITYAI CCTV NODE :: FRAME #{frame_idx:04d}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 242, 254), 1, cv2.LINE_AA)
            cv2.putText(frame, f"FPS: {fps} | RES: {width}x{height}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 175, 200), 1, cv2.LINE_AA)

            writer.write(frame)

        writer.release()

        # Verify integrity before replacing destination file
        test_cap = cv2.VideoCapture(str(temp_path))
        if not test_cap or not test_cap.isOpened():
            test_cap.release()
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Integrity check failed for generated video: {temp_path}")
            return False

        verified_frames = test_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        test_cap.release()

        if verified_frames <= 0:
            if temp_path.exists():
                temp_path.unlink()
            logger.error(f"Generated video has 0 frames: {temp_path}")
            return False

        # Atomic file replacement
        import os
        os.replace(str(temp_path), str(output_path))
        logger.info(f"Verified and atomically saved demo video at: {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate demo video: {e}")
        return False

