"""SAM3 Model Manager - Singleton pattern for model initialization and caching."""

import os
import threading
from pathlib import Path
from typing import Optional

import torch
from sam3.model.sam3_image_processor import Sam3Processor
from sam3.model_builder import build_sam3_image_model

from app.core.config import settings


class SAM3ModelManager:
    """Singleton manager for SAM3 image model and processor."""

    _instance: Optional["SAM3ModelManager"] = None
    _lock = threading.Lock()
    _model: Optional[torch.nn.Module] = None
    _processor: Optional[Sam3Processor] = None
    _device: str = "cuda" if torch.cuda.is_available() else "cpu"
    _loaded: bool = False

    def __new__(cls) -> "SAM3ModelManager":
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the model manager."""
        if not self._loaded:
            # Lazy loading - model will be loaded on first use
            pass

    def get_model(self) -> torch.nn.Module:
        """Get or load the SAM3 image model."""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._load_model()
        return self._model

    def get_processor(self, confidence_threshold: float = 0.5) -> Sam3Processor:
        """Get or create the SAM3 processor with specified confidence threshold."""
        model = self.get_model()
        if self._processor is None or self._processor.confidence_threshold != confidence_threshold:
            with self._lock:
                if self._processor is None or self._processor.confidence_threshold != confidence_threshold:
                    self._processor = Sam3Processor(
                        model=model,
                        resolution=1008,
                        device=self._device,
                        confidence_threshold=confidence_threshold,
                    )
        return self._processor

    def _load_model(self) -> None:
        """Load the SAM3 image model."""
        print(f"Loading SAM3 image model on device: {self._device}")
        try:
            self._model = build_sam3_image_model(
                bpe_path=None,  # Will use default path
                device=self._device,
                eval_mode=True,
                checkpoint_path=None,  # Will load from HuggingFace
                load_from_HF=True,
                enable_segmentation=True,
                enable_inst_interactivity=False,
                compile=False,
            )
            self._model.eval()
            print("SAM3 image model loaded successfully")
            self._loaded = True

            # Warmup the model with a dummy image
            self._warmup_model()
        except Exception as e:
            print(f"Error loading SAM3 model: {e}")
            raise

    def _warmup_model(self) -> None:
        """Warmup the model with a dummy image to ensure it's ready."""
        try:
            from PIL import Image
            import numpy as np

            dummy_image = Image.fromarray(np.zeros((224, 224, 3), dtype=np.uint8))
            processor = self.get_processor()
            state = processor.set_image(dummy_image)
            print("SAM3 model warmed up successfully")
        except Exception as e:
            print(f"Warning: Model warmup failed: {e}")

    def is_ready(self) -> bool:
        """Check if the model is loaded and ready."""
        return self._loaded and self._model is not None

    def get_device(self) -> str:
        """Get the device the model is running on."""
        return self._device

    def reload(self) -> None:
        """Reload the model (useful for configuration changes)."""
        with self._lock:
            self._model = None
            self._processor = None
            self._loaded = False
            self.get_model()  # Trigger reload


# Global instance getter
def get_sam3_model_manager() -> SAM3ModelManager:
    """Get the singleton SAM3 model manager instance."""
    return SAM3ModelManager()

