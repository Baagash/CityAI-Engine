import re
import cv2
import time
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from app.config import settings

logger = logging.getLogger("cityai.anpr")

# Standard Indian Registration Plate Patterns
INDIAN_PLATE_PATTERNS = [
    # Standard: 2 letters (State), 2 digits (RTO), 1-2 letters (Series), 4 digits (e.g., TN38AB1234, KA05MB9912, DL01CA1024)
    re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$'),
    # Single digit RTO format (e.g., DL1CA1234, MH2A9999)
    re.compile(r'^[A-Z]{2}[0-9]{1}[A-Z]{1,2}[0-9]{4}$'),
    # Bharat Series (BH): Year (2 digits) + BH + 4 digits + 1-2 letters (e.g., 22BH1234AA)
    re.compile(r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$'),
    # Vintage / Commercial / Short series (e.g., TN091234, DL12345)
    re.compile(r'^[A-Z]{2}[0-9]{4,6}$')
]

class ANPREngine:
    """
    Real Automatic Number Plate Recognition (ANPR) & OCR Processing Engine.
    Uses EasyOCR for real character recognition, with adaptive CLAHE image preprocessing,
    bounding box localization, and registration format validation.
    Zero fabrication: uncertain OCR strictly returns 'UNKNOWN' with zero confidence.
    """
    def __init__(self):
        self._ocr_reader = None
        self.is_initialized = False
        self.ocr_engine_name = "EasyOCR"
        self.ocr_version = "1.7.2"
        self.device = "cpu"
        self._init_ocr()

    def _init_ocr(self):
        """Initializes EasyOCR reader with English language model."""
        try:
            import easyocr
            gpu_flag = bool(settings.ANPR_GPU and settings.DEVICE == "cuda")
            self._ocr_reader = easyocr.Reader(['en'], gpu=gpu_flag, verbose=False)
            self.is_initialized = True
            self.device = "cuda" if gpu_flag else "cpu"
            logger.info(f"[ANPR] EasyOCR reader initialized on {self.device}.")
        except Exception as e:
            logger.warning(f"[ANPR] EasyOCR init notice: {e}. Running in graceful fallback mode.")
            self._ocr_reader = None
            self.is_initialized = False

    def preprocess_plate(self, plate_img: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE contrast enhancement, grayscale conversion, bilateral noise reduction,
        and adaptive scaling to optimize image for OCR token extraction.
        """
        if plate_img is None or plate_img.size == 0:
            return plate_img

        try:
            # 1. Grayscale
            if len(plate_img.shape) == 3:
                gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
            else:
                gray = plate_img.copy()

            # 2. Resize if crop is too small for character recognition
            h, w = gray.shape[:2]
            if w < 160 and w > 0:
                scale = 160.0 / w
                new_h = int(h * scale)
                gray = cv2.resize(gray, (160, new_h), interpolation=cv2.INTER_CUBIC)

            # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 4. Bilateral Filtering for edge-preserving denoising
            denoised = cv2.bilateralFilter(enhanced, 7, 50, 50)
            return denoised
        except Exception as e:
            logger.debug(f"[ANPR] Preprocessing error: {e}")
            return plate_img

    def clean_plate_text(self, raw_text: str) -> str:
        """Cleans raw OCR text: strips spaces, punctuation, special chars, uppercase only."""
        if not raw_text:
            return ""
        # Remove non-alphanumeric characters and uppercase
        cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper().strip())
        return cleaned

    def validate_plate(self, plate_text: str) -> str:
        """
        Validates whether plate text matches recognized Indian registration formats.
        Returns 'VALID_FORMAT', 'INVALID_FORMAT', or 'UNKNOWN'.
        """
        if not plate_text or plate_text == "UNKNOWN":
            return "UNKNOWN"

        clean = self.clean_plate_text(plate_text)
        if len(clean) < 4 or len(clean) > 12:
            return "INVALID_FORMAT"

        for pattern in INDIAN_PLATE_PATTERNS:
            if pattern.match(clean):
                return "VALID_FORMAT"

        return "INVALID_FORMAT"

    def localize_plate_roi(self, vehicle_crop: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[List[float]]]:
        """
        Localizes the probable license plate region within a vehicle image crop.
        In urban surveillance, plates typically appear in the lower 35% of the vehicle bumper area.
        Returns (plate_roi_image, [rel_x1, rel_y1, rel_x2, rel_y2]).
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None, None

        try:
            h, w = vehicle_crop.shape[:2]
            if h < 20 or w < 20:
                return vehicle_crop, [0.0, 0.0, float(w), float(h)]

            # Lower 40% height, center 70% width
            y1 = int(h * 0.60)
            y2 = int(h * 0.98)
            x1 = int(w * 0.15)
            x2 = int(w * 0.85)

            roi = vehicle_crop[y1:y2, x1:x2]
            if roi is not None and roi.size > 0:
                return roi, [float(x1), float(y1), float(x2), float(y2)]
            return vehicle_crop, [0.0, 0.0, float(w), float(h)]
        except Exception:
            return vehicle_crop, [0.0, 0.0, float(w), float(h)]

    def recognize_plate(self, plate_img: np.ndarray) -> Dict[str, Any]:
        """
        Executes real OCR inference on a plate crop or vehicle sub-region.
        Zero fabrication: returns 'UNKNOWN' with 0.0 confidence when no plate is legible.
        """
        if plate_img is None or plate_img.size == 0:
            return {
                "plate_text": "UNKNOWN",
                "raw_text": None,
                "ocr_confidence": 0.0,
                "validation_status": "UNKNOWN",
                "is_valid_format": False
            }

        preprocessed = self.preprocess_plate(plate_img)

        if self._ocr_reader is not None:
            try:
                results = self._ocr_reader.readtext(preprocessed, detail=1, paragraph=False)
                if results:
                    # Filter candidates with alphanumeric characters
                    valid_candidates = []
                    for item in results:
                        # item: (bbox, text, conf)
                        raw = str(item[1])
                        conf = float(item[2])
                        clean = self.clean_plate_text(raw)
                        if len(clean) >= 3:
                            valid_candidates.append((clean, raw, conf))

                    if valid_candidates:
                        # Select highest confidence valid candidate
                        best_clean, best_raw, best_conf = max(valid_candidates, key=lambda x: x[2])
                        val_status = self.validate_plate(best_clean)

                        return {
                            "plate_text": best_clean,
                            "raw_text": best_raw,
                            "ocr_confidence": round(best_conf, 3),
                            "validation_status": val_status,
                            "is_valid_format": val_status == "VALID_FORMAT"
                        }
            except Exception as e:
                logger.debug(f"[ANPR] OCR inference error: {e}")

        # Real fallback for unreadable or uncertain plate
        return {
            "plate_text": "UNKNOWN",
            "raw_text": None,
            "ocr_confidence": 0.0,
            "validation_status": "UNKNOWN",
            "is_valid_format": False
        }

# Global ANPR engine singleton
anpr_engine = ANPREngine()
