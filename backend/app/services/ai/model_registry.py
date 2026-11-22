import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class IRoadDamageDetector(ABC):
    """Abstract interface for local Road Damage Computer Vision (YOLO) models."""

    @abstractmethod
    def load(self, weights_path: str, device: str = "cpu") -> bool:
        """Loads model weights lazily onto specified device."""
        pass

    @abstractmethod
    def detect(self, image_path: str, confidence_threshold: float = 0.35) -> Dict[str, Any]:
        """Runs road damage inference and returns detected classes, confidence, and bounding boxes."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if model weights are loaded and ready for inference."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Releases model weights and frees GPU/CPU memory."""
        pass


class IVoiceTranscriber(ABC):
    """Abstract interface for local Speech Recognition (faster-whisper) models."""

    @abstractmethod
    def load(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8") -> bool:
        """Loads Whisper speech model lazily onto specified compute device."""
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribes audio file into text with language identification."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Returns True if model is initialized and ready for transcription."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Frees model from RAM/VRAM."""
        pass


class MockRoadDamageDetector(IRoadDamageDetector):
    """Stub implementation for Phase 4A foundation prior to Phase 4B YOLO integration."""

    def __init__(self):
        self._loaded = False
        self._weights_path: Optional[str] = None

    def load(self, weights_path: str, device: str = "cpu") -> bool:
        logger.info(f"[ModelRegistry] Stub YOLO road damage detector registered with weights path '{weights_path}' on device '{device}'.")
        self._weights_path = weights_path
        self._loaded = True
        return True

    def detect(self, image_path: str, confidence_threshold: float = 0.35) -> Dict[str, Any]:
        return {
            "status": "STUB_PHASE_4A",
            "image_path": image_path,
            "detections": [],
            "pothole_detected": False,
            "crack_detected": False,
            "message": "Local YOLO inference will be activated in Phase 4B.",
        }

    def is_ready(self) -> bool:
        return self._loaded

    def unload(self) -> None:
        self._loaded = False
        self._weights_path = None


class MockVoiceTranscriber(IVoiceTranscriber):
    """Stub implementation for Phase 4A foundation prior to Phase 4C faster-whisper integration."""

    def __init__(self):
        self._loaded = False

    def load(self, model_size: str = "small", device: str = "cpu", compute_type: str = "int8") -> bool:
        logger.info(f"[ModelRegistry] Stub speech recognition engine registered (size='{model_size}', device='{device}', compute='{compute_type}').")
        self._loaded = True
        return True

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        return {
            "status": "STUB_PHASE_4A",
            "audio_path": audio_path,
            "text": "",
            "language": language or "en",
            "message": "Local faster-whisper inference will be activated in Phase 4C.",
        }

    def is_ready(self) -> bool:
        return self._loaded

    def unload(self) -> None:
        self._loaded = False


class ModelRegistry:
    """
    Central coordinator for local AI models.
    Designed specifically for 4GB VRAM (GTX 1650) and 7.68GB RAM hardware constraints:
    enforces lazy loading, sequential execution, and manual memory reclamation.
    """

    _cv_detector: Optional[IRoadDamageDetector] = None
    _stt_transcriber: IVoiceTranscriber = MockVoiceTranscriber()

    @classmethod
    def get_cv_detector(cls) -> IRoadDamageDetector:
        if cls._cv_detector is None:
            from app.services.ai.road_damage_detector import RoadDamageDetector
            cls._cv_detector = RoadDamageDetector()
        return cls._cv_detector

    @classmethod
    def set_cv_detector(cls, detector: IRoadDamageDetector) -> None:
        cls._cv_detector = detector

    @classmethod
    def get_stt_transcriber(cls) -> IVoiceTranscriber:
        return cls._stt_transcriber

    @classmethod
    def set_stt_transcriber(cls, transcriber: IVoiceTranscriber) -> None:
        cls._stt_transcriber = transcriber

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        detector = cls.get_cv_detector()
        weights_path = getattr(detector, "weights_path", "models/weights/road_damage_yolov8.onnx")
        import os
        return {
            "cv_detector_ready": detector.is_ready(),
            "cv_detector_device": getattr(detector, "device", "cpu"),
            "cv_weights_path": weights_path,
            "cv_weights_exist": os.path.isfile(weights_path),
            "stt_transcriber_ready": cls._stt_transcriber.is_ready(),
            "target_hardware": {
                "gpu": "NVIDIA GeForce GTX 1650 (4GB VRAM)",
                "system_ram": "7.68GB",
                "recommended_cv_device": "cuda:0",
                "recommended_stt_device": "cpu",
                "stt_quantization": "int8",
            },
        }
