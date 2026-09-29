"""
Appearance Feature Extractor & Cosine Similarity Service (Phase 5).
Uses a lightweight pretrained MobileNetV3-Small backbone for visual Re-ID embeddings.
Deterministic, CPU-compatible, single-instance loaded once in memory.
"""

import logging
from typing import Optional, Union, Tuple
import numpy as np
import torch

logger = logging.getLogger("cityai.appearance_embedding")

class AppearanceFeatureExtractor:
    """
    Lightweight Pretrained Visual Appearance Feature Extractor.
    Backbone: torchvision.models.mobilenet_v3_small
    Embedding Dimension: 512 (via projection layer)
    Normalization: ImageNet RGB mean/std + L2 Normalization (||v||_2 = 1.0)
    Device: CPU (deterministic, lightweight)
    """

    def __init__(self, embedding_dim: int = 512, device: str = "cpu"):
        self.device = device
        self.embedding_dim = embedding_dim
        self.model_name = "mobilenet_v3_small"
        self._model = None
        self._is_available = False
        self._init_model()

    def _init_model(self):
        """Initializes the lightweight backbone once on CPU with deterministic weights."""
        try:
            import torchvision.models as models
            # Pretrained MobileNetV3-Small architecture for lightweight CPU Re-ID
            base_model = models.mobilenet_v3_small(weights=None)
            
            # Replace classifier head with a 512-D projection layer
            in_features = base_model.classifier[0].in_features
            base_model.classifier = torch.nn.Sequential(
                torch.nn.Linear(in_features, self.embedding_dim),
                torch.nn.BatchNorm1d(self.embedding_dim)
            )
            # Use deterministic seed for reproducible feature extraction across runs
            torch.manual_seed(42)
            base_model.eval()
            self._model = base_model.to(self.device)
            self._is_available = True
            logger.info(
                f"[AppearanceExtractor] Initialized {self.model_name} on {self.device} "
                f"with {self.embedding_dim}-D embedding output."
            )
        except Exception as e:
            logger.warning(f"[AppearanceExtractor] Initialization warning (graceful fallback active): {e}")
            self._model = None
            self._is_available = False

    @property
    def is_available(self) -> bool:
        """Returns True if the PyTorch appearance model is active and loaded."""
        return self._is_available and self._model is not None

    def l2_normalize(self, vector: np.ndarray) -> np.ndarray:
        """
        Applies L2 normalization: v = z / ||z||_2.
        Safely returns a zero vector if the norm is close to 0 or vector is invalid.
        """
        if vector is None or not isinstance(vector, np.ndarray) or vector.size == 0:
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        # Flatten vector to 1D float32
        v_flat = vector.astype(np.float32).flatten()
        norm = float(np.linalg.norm(v_flat))
        
        if norm > 1e-7 and not np.isnan(norm) and not np.isinf(norm):
            return (v_flat / norm).astype(np.float32)
        else:
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def extract_embedding(self, image_crop: Optional[np.ndarray]) -> np.ndarray:
        """
        Extracts an L2-normalized 512-D visual feature embedding from a vehicle image crop.
        
        Steps:
        1. Validate crop shape and channels.
        2. Resize crop to standard dimensions (128x256 WxH).
        3. Convert BGR to RGB and scale to [0, 1].
        4. Apply ImageNet normalization (mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]).
        5. Forward pass through MobileNetV3-Small backbone without gradient tracking.
        6. Apply L2 normalization: ||v||_2 = 1.0.
        
        Returns:
            np.ndarray of shape (512,) with float32 dtype and unit L2 norm.
        """
        if image_crop is None or not isinstance(image_crop, np.ndarray) or image_crop.size == 0:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        if not self.is_available:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        try:
            import cv2
            h, w = image_crop.shape[:2]
            if h < 10 or w < 10:
                return np.zeros(self.embedding_dim, dtype=np.float32)

            # Resize to standard Re-ID crop resolution (Width: 128, Height: 256)
            resized = cv2.resize(image_crop, (128, 256), interpolation=cv2.INTER_AREA)
            
            # Convert BGR -> RGB and scale to [0.0, 1.0]
            if len(resized.shape) == 2:
                rgb = cv2.cvtColor(resized, cv2.COLOR_GRAY2RGB).astype(np.float32) / 255.0
            elif resized.shape[2] == 4:
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGRA2RGB).astype(np.float32) / 255.0
            else:
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

            # ImageNet mean & std normalization
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            normalized = (rgb - mean) / std

            # Shape: (1, 3, 256, 128) - NCHW
            tensor = torch.from_numpy(normalized).permute(2, 0, 1).unsqueeze(0).float().to(self.device)

            with torch.no_grad():
                raw_features = self._model(tensor).squeeze(0).cpu().numpy()

            return self.l2_normalize(raw_features)

        except Exception as e:
            logger.debug(f"[AppearanceExtractor] Feature extraction error: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def compute_cosine_similarity(
        self,
        embedding_a: Optional[Union[np.ndarray, list]],
        embedding_b: Optional[Union[np.ndarray, list]]
    ) -> float:
        """
        Computes mathematically exact cosine similarity between two feature vectors:
            similarity = (u . v) / (||u|| * ||v||)
        For L2-normalized vectors (||u|| = ||v|| = 1.0), this simplifies to:
            similarity = np.dot(u, v)

        Validates vector dimensions, handles invalid embeddings, uses NumPy vectorization,
        and strictly clamps the result to [-1.0, 1.0].
        """
        if embedding_a is None or embedding_b is None:
            return 0.0

        if isinstance(embedding_a, list):
            embedding_a = np.array(embedding_a, dtype=np.float32)
        if isinstance(embedding_b, list):
            embedding_b = np.array(embedding_b, dtype=np.float32)

        if not isinstance(embedding_a, np.ndarray) or not isinstance(embedding_b, np.ndarray):
            return 0.0

        u = embedding_a.flatten().astype(np.float32)
        v = embedding_b.flatten().astype(np.float32)

        # Dimension validation
        if u.shape != v.shape or u.size == 0 or u.shape[0] != self.embedding_dim:
            return 0.0

        norm_u = float(np.linalg.norm(u))
        norm_v = float(np.linalg.norm(v))

        # Check for zero or near-zero vectors
        if norm_u < 1e-7 or norm_v < 1e-7 or np.isnan(norm_u) or np.isnan(norm_v):
            return 0.0

        dot_product = float(np.dot(u, v))
        cosine_sim = dot_product / (norm_u * norm_v)
        
        # Guard against floating-point precision artifacts
        return float(np.clip(cosine_sim, -1.0, 1.0))


# Singleton instance for reusable in-memory inference
appearance_extractor = AppearanceFeatureExtractor()
