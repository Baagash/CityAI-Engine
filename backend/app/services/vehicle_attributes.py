import cv2
import numpy as np
from typing import Dict, Any, Tuple

COLOR_RANGES = {
    "RED": [
        ((0, 70, 50), (10, 255, 255)),
        ((170, 70, 50), (180, 255, 255))
    ],
    "BLUE": [
        ((95, 80, 40), (135, 255, 255))
    ],
    "YELLOW": [
        ((20, 100, 100), (35, 255, 255))
    ],
    "GREEN": [
        ((36, 60, 50), (85, 255, 255))
    ],
    "WHITE": [
        ((0, 0, 190), (180, 50, 255))
    ],
    "BLACK": [
        ((0, 0, 0), (180, 255, 60))
    ],
    "SILVER": [
        ((0, 0, 70), (180, 40, 185))
    ]
}

class VehicleAttributeService:
    def __init__(self):
        self.supported_types = ["car", "suv", "truck", "bus", "motorcycle", "auto-rickshaw"]

    def extract_color(self, image_crop: np.ndarray) -> Tuple[str, float]:
        """
        Extracts dominant color from vehicle image crop using HSV color quantization.
        Returns (color_name, confidence).
        """
        if image_crop is None or image_crop.size == 0:
            return "UNKNOWN", 0.0

        try:
            # Resize for fast processing and sample center 60% of crop to avoid background tarmac/sky
            h, w = image_crop.shape[:2]
            y1, y2 = int(h * 0.2), int(h * 0.8)
            x1, x2 = int(w * 0.2), int(w * 0.8)
            roi = image_crop[y1:y2, x1:x2] if (y2 > y1 and x2 > x1) else image_crop

            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            total_pixels = roi.shape[0] * roi.shape[1]
            if total_pixels == 0:
                return "UNKNOWN", 0.0

            color_scores = {}
            for color_name, ranges in COLOR_RANGES.items():
                mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
                for lower, upper in ranges:
                    lower_arr = np.array(lower, dtype=np.uint8)
                    upper_arr = np.array(upper, dtype=np.uint8)
                    sub_mask = cv2.inRange(hsv, lower_arr, upper_arr)
                    mask = cv2.bitwise_or(mask, sub_mask)
                matched_pixels = cv2.countNonZero(mask)
                color_scores[color_name] = matched_pixels / total_pixels

            # Find best match
            best_color = max(color_scores, key=color_scores.get)
            best_score = color_scores[best_color]

            if best_score < 0.15:
                # If low confidence or mixed reflection, check lightness
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                mean_brightness = np.mean(gray)
                if mean_brightness > 180:
                    return "WHITE", 0.65
                elif mean_brightness < 60:
                    return "BLACK", 0.65
                else:
                    return "SILVER", 0.55

            confidence = min(0.98, max(0.50, best_score * 2.2))
            return best_color, round(confidence, 2)
        except Exception:
            return "UNKNOWN", 0.0

    def classify_type_from_bbox(self, bbox: list, base_class: str = "car") -> str:
        """
        Refines vehicle class based on aspect ratio and bounding box geometry.
        """
        if base_class in ["bus", "truck", "motorcycle"]:
            return base_class

        x1, y1, x2, y2 = bbox
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        aspect_ratio = width / max(1.0, height)

        if aspect_ratio < 0.8:
            return "motorcycle"
        elif height > 220 or (height > 150 and aspect_ratio > 1.6):
            return "truck"
        elif height > 180:
            return "bus"
        elif aspect_ratio > 1.35 and height > 100:
            return "suv"
        return "sedan"

attribute_service = VehicleAttributeService()
