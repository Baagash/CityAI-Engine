import os
import cv2
import json
import uuid
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from app.config import settings

class EvidenceEngine:
    def __init__(self):
        self.snapshots_dir = settings.SNAPSHOT_DIR
        self.evidence_dir = settings.EVIDENCE_DIR

    def save_snapshot(self, frame: np.ndarray, prefix: str = "snap") -> str:
        """Saves a frame crop to snapshots directory and returns relative URI."""
        if frame is None or frame.size == 0:
            return ""
        filename = f"{prefix}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
        full_path = self.snapshots_dir / filename
        cv2.imwrite(str(full_path), frame)
        return f"/snapshots/{filename}"

    def create_side_by_side_evidence(
        self,
        img_a_path: Optional[str],
        img_b_path: Optional[str],
        title: str,
        obs_a: Dict[str, Any],
        obs_b: Dict[str, Any]
    ) -> str:
        """
        Creates a side-by-side evidence comparison image combining two camera observations.
        """
        canvas = np.zeros((480, 800, 3), dtype=np.uint8)
        canvas[:] = (24, 28, 36)  # Dark slate background

        # Header
        cv2.rectangle(canvas, (0, 0), (800, 50), (15, 23, 42), -1)
        cv2.putText(canvas, f"CITYAI INTELLIGENCE EVIDENCE: {title}", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 242, 254), 2)

        # Left Panel (Observation A)
        cv2.rectangle(canvas, (20, 60), (390, 420), (30, 41, 59), -1)
        cv2.rectangle(canvas, (20, 60), (390, 420), (51, 65, 85), 2)
        cv2.putText(canvas, f"OBSERVATION A - {obs_a.get('camera_id', 'CAM01')}", (35, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (148, 163, 184), 1)
        cv2.putText(canvas, f"Type: {obs_a.get('vehicle_type', 'Sedan').upper()}", (35, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(canvas, f"Color: {obs_a.get('color', 'WHITE')}", (35, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(canvas, f"OCR Plate: {obs_a.get('plate_text', 'TN38AB1234')}", (35, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (52, 211, 153), 2)
        cv2.putText(canvas, f"Time: {str(obs_a.get('timestamp', ''))[:19]}", (35, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1)

        # Right Panel (Observation B)
        cv2.rectangle(canvas, (410, 60), (780, 420), (30, 41, 59), -1)
        cv2.rectangle(canvas, (410, 60), (780, 420), (239, 68, 68), 2)
        cv2.putText(canvas, f"OBSERVATION B - {obs_b.get('camera_id', 'CAM04')}", (425, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (248, 113, 113), 1)
        cv2.putText(canvas, f"Type: {obs_b.get('vehicle_type', 'SUV').upper()}", (425, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(canvas, f"Color: {obs_b.get('color', 'BLACK')}", (425, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
        cv2.putText(canvas, f"OCR Plate: {obs_b.get('plate_text', 'TN38AB1234')}", (425, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (52, 211, 153), 2)
        cv2.putText(canvas, f"Time: {str(obs_b.get('timestamp', ''))[:19]}", (425, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1)

        # Bottom Warning Footer
        cv2.rectangle(canvas, (0, 435), (800, 480), (15, 23, 42), -1)
        cv2.putText(canvas, "HUMAN-IN-THE-LOOP INTELLIGENCE ONLY - REQUIRES OFFICIAL VERIFICATION", (110, 462), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (251, 191, 36), 1)

        evidence_filename = f"evd_compare_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
        out_path = self.evidence_dir / evidence_filename
        cv2.imwrite(str(out_path), canvas)
        return f"/evidence/{evidence_filename}"

evidence_engine = EvidenceEngine()
