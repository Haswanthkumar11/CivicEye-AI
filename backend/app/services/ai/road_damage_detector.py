import os
import gc
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import cv2

from app.core.config import settings
from app.services.ai.model_registry import IRoadDamageDetector
from app.services.ai.detection_schemas import (
    RoadDamageDetection,
    RoadDamageAnalysisResult,
)
from app.services.ai.image_preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)

# Standard Road Damage Dataset (RDD2020 / RDD2022) Class Definitions
# Reference: Sekilab & IEEE Global Road Damage Detection Challenge
RDD_CLASSES = {
    0: {"id": "D00", "name": "Longitudinal Crack", "category": "crack", "base_severity": 50.0},
    1: {"id": "D10", "name": "Transverse Crack", "category": "crack", "base_severity": 50.0},
    2: {"id": "D20", "name": "Alligator Crack", "category": "crack", "base_severity": 70.0},
    3: {"id": "D40", "name": "Pothole", "category": "pothole", "base_severity": 85.0},
    4: {"id": "D99", "name": "Other Road Damage", "category": "damage", "base_severity": 45.0},
}

CLASS_NAME_ALIASES = {
    "d00": 0, "longitudinal crack": 0, "longitudinal_crack": 0,
    "d10": 1, "transverse crack": 1, "transverse_crack": 1,
    "d20": 2, "alligator crack": 2, "alligator_crack": 2,
    "d40": 3, "pothole": 3, "potholes": 3,
    "d99": 4, "other": 4, "other road damage": 4,
}


class RoadDamageDetector(IRoadDamageDetector):
    """
    Local Computer Vision Road Damage Detector implementing IRoadDamageDetector.
    Uses ONNX Runtime (MIT License) with OpenCV letterboxing and NMS.
    Designed for NVIDIA GeForce GTX 1650 (4GB VRAM) and 7.68GB RAM constraints:
    enforces lazy loading, single-instance caching, CPU fallback, and explicit memory reclamation.
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
    ):
        self._weights_path = weights_path or getattr(settings, "YOLO_MODEL_PATH", "models/weights/road_damage_yolov8.onnx")
        self._requested_device = (device or getattr(settings, "YOLO_DEVICE", "cpu")).lower()
        self._actual_device = "cpu"
        self._confidence_threshold = confidence_threshold or getattr(settings, "YOLO_CONFIDENCE_THRESHOLD", 0.35)
        self._loaded = False
        self._session = None  # ONNX Runtime InferenceSession
        self._input_name: Optional[str] = None
        self._input_shape: Optional[Tuple[int, ...]] = None

    @property
    def weights_path(self) -> str:
        return self._weights_path

    @property
    def device(self) -> str:
        return self._actual_device

    def is_ready(self) -> bool:
        """Returns True only when model weights are loaded in memory and ready for inference."""
        return bool(self._loaded and self._session is not None)

    def load(self, weights_path: Optional[str] = None, device: Optional[str] = None) -> bool:
        """
        Loads road damage model weights lazily into memory.
        Automatically detects GPU availability and falls back to CPU if CUDA is unavailable.
        """
        if weights_path:
            self._weights_path = weights_path
        if device:
            self._requested_device = device.lower()

        # Check if weights file exists on disk
        if not os.path.isfile(self._weights_path):
            logger.info(
                f"[RoadDamageDetector] Model weights not found at '{self._weights_path}'. "
                "Detector will operate in fallback mode until weights are placed in directory."
            )
            self._loaded = False
            self._session = None
            return False

        try:
            import onnxruntime as ort

            available_providers = ort.get_available_providers()
            logger.info(f"[RoadDamageDetector] Available ONNX execution providers: {available_providers}")

            # Provider selection with automatic CPU fallback
            if self._requested_device.startswith("cuda") and "CUDAExecutionProvider" in available_providers:
                providers = [
                    ("CUDAExecutionProvider", {
                        "device_id": 0,
                        "arena_extend_strategy": "kNextPowerOfTwo",
                        "gpu_mem_limit": 2 * 1024 * 1024 * 1024,  # Cap to 2GB to protect 4GB GTX 1650
                    }),
                    "CPUExecutionProvider",
                ]
                self._actual_device = "cuda:0"
            else:
                if self._requested_device.startswith("cuda"):
                    logger.warning("[RoadDamageDetector] CUDA requested but CUDAExecutionProvider not available; falling back to CPU.")
                providers = ["CPUExecutionProvider"]
                self._actual_device = "cpu"

            # Create optimized ONNX inference session
            sess_options = ort.SessionOptions()
            sess_options.intra_op_num_threads = 4
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self._session = ort.InferenceSession(self._weights_path, sess_options, providers=providers)
            self._input_name = self._session.get_inputs()[0].name
            self._input_shape = self._session.get_inputs()[0].shape
            self._loaded = True

            logger.info(
                f"[RoadDamageDetector] Successfully loaded road damage weights from '{self._weights_path}' "
                f"on device '{self._actual_device}' (input: '{self._input_name}', shape: {self._input_shape})."
            )
            return True

        except Exception as e:
            logger.error(f"[RoadDamageDetector] Failed to load ONNX model weights '{self._weights_path}': {e}")
            self._loaded = False
            self._session = None
            return False

    def unload(self) -> None:
        """Releases session resources and frees system and GPU memory."""
        self._session = None
        self._loaded = False
        self._input_name = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        logger.info("[RoadDamageDetector] Model weights unloaded and memory reclaimed.")

    def detect(self, image_path: str, confidence_threshold: Optional[float] = None) -> RoadDamageAnalysisResult:
        """
        Executes local road damage detection on an image:
        1. Preprocesses and letterboxes image to 640x640 via OpenCV.
        2. Executes ONNX inference or returns clear readiness status.
        3. Decodes bounding boxes, applies NMS, and scales back to original image space.
        4. Calculates visual damage estimation score (0-100).
        """
        start_time = time.perf_counter()
        conf_thresh = confidence_threshold if confidence_threshold is not None else self._confidence_threshold

        # 1. Image validation and loading
        image, err = ImagePreprocessor.load_image(image_path)
        if err or image is None:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status = "CORRUPT_IMAGE" if "corrupt" in (err or "").lower() else "ERROR"
            return RoadDamageAnalysisResult(
                processing_status=status,
                model_name="YOLO-RDD-Nano",
                model_version="rdd2022-v1",
                inference_device=self._actual_device,
                inference_time_ms=elapsed_ms,
                image_width=0,
                image_height=0,
                detection_count=0,
                pothole_detected=False,
                crack_detected=False,
                estimated_visual_damage_level=0.0,
                visual_evidence_explanation=f"Image inspection failed: {err}",
                detections=[],
            )

        orig_h, orig_w = image.shape[:2]

        # 2. Lazy loading check
        if not self.is_ready():
            # Attempt lazy load
            loaded = self.load()
            if not loaded:
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return RoadDamageAnalysisResult(
                    processing_status="WEIGHTS_NOT_FOUND",
                    model_name="YOLO-RDD-Nano",
                    model_version="rdd2022-v1",
                    inference_device=self._actual_device,
                    inference_time_ms=elapsed_ms,
                    image_width=orig_w,
                    image_height=orig_h,
                    detection_count=0,
                    pothole_detected=False,
                    crack_detected=False,
                    estimated_visual_damage_level=0.0,
                    visual_evidence_explanation=(
                        "Local road damage model weights not initialized on server. "
                        "Triage proceeding via multimodal linguistic reasoning."
                    ),
                    detections=[],
                )

        # 3. Letterbox Preprocessing
        prep = ImagePreprocessor.letterbox(image, target_size=(640, 640))

        # 4. Model Inference
        try:
            raw_outputs = self._session.run(None, {self._input_name: prep.tensor})
            raw_tensor = raw_outputs[0]
        except Exception as e:
            logger.error(f"[RoadDamageDetector] Inference execution failed: {e}")
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return RoadDamageAnalysisResult(
                processing_status="ERROR",
                model_name="YOLO-RDD-Nano",
                model_version="rdd2022-v1",
                inference_device=self._actual_device,
                inference_time_ms=elapsed_ms,
                image_width=orig_w,
                image_height=orig_h,
                detection_count=0,
                pothole_detected=False,
                crack_detected=False,
                estimated_visual_damage_level=0.0,
                visual_evidence_explanation=f"Inference execution error: {str(e)[:150]}",
                detections=[],
            )

        # 5. Parse Output Predictions & Apply NMS
        detections = self._postprocess_yolo(
            raw_tensor=raw_tensor,
            conf_thresh=conf_thresh,
            prep=prep,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        detection_count = len(detections)

        # 6. Aggregate visual damage and generate transparent explanation
        potholes = [d for d in detections if d.class_id == "D40" or "pothole" in d.class_name.lower()]
        cracks = [d for d in detections if d not in potholes]

        pothole_detected = len(potholes) > 0
        crack_detected = len(cracks) > 0

        if detection_count == 0:
            status = "NO_DAMAGE_DETECTED"
            visual_damage_score = 20.0  # Baseline low visual defect score
            explanation = "Inspection completed: No road surface cavities, potholes, or structural cracks detected above confidence threshold."
        else:
            status = "SUCCESS"
            # Calculate explainable visual damage score (0-100)
            # Potholes carry higher physical risk (85 base), cracks carry 50-70 base
            max_pothole_conf = max([p.confidence for p in potholes], default=0.0)
            max_crack_conf = max([c.confidence for c in cracks], default=0.0)
            total_area_pct = sum(d.relative_area_percent for d in detections)

            score_components = []
            if pothole_detected:
                pothole_score = 70.0 + (len(potholes) * 5.0) + (max_pothole_conf * 15.0)
                score_components.append(min(95.0, pothole_score))
            if crack_detected:
                crack_score = 45.0 + (len(cracks) * 4.0) + (max_crack_conf * 10.0)
                score_components.append(min(75.0, crack_score))

            base_score = max(score_components) if score_components else 40.0
            # Area impact bonus (up to +10 for large damage areas)
            area_bonus = min(10.0, total_area_pct * 2.0)
            visual_damage_score = round(max(0.0, min(100.0, base_score + area_bonus)), 2)

            parts = []
            if potholes:
                parts.append(f"{len(potholes)} Pothole(s) [max conf {max_pothole_conf*100:.1f}%]")
            if cracks:
                parts.append(f"{len(cracks)} Surface Crack(s) [max conf {max_crack_conf*100:.1f}%]")
            explanation = (
                f"Visual AI Evidence: Identified {', '.join(parts)}. "
                f"Combined visual defect severity estimated at {visual_damage_score}/100."
            )

        return RoadDamageAnalysisResult(
            processing_status=status,
            model_name="YOLO-RDD-Nano",
            model_version="rdd2022-v1",
            inference_device=self._actual_device,
            inference_time_ms=elapsed_ms,
            image_width=orig_w,
            image_height=orig_h,
            detection_count=detection_count,
            pothole_detected=pothole_detected,
            crack_detected=crack_detected,
            estimated_visual_damage_level=visual_damage_score,
            visual_evidence_explanation=explanation,
            detections=detections,
        )

    def _postprocess_yolo(
        self,
        raw_tensor: np.ndarray,
        conf_thresh: float,
        prep: Any,
    ) -> List[RoadDamageDetection]:
        """
        Parses raw model output array, applies confidence filtering, NMS suppression,
        and converts coordinates back to original image space.
        """
        # Shape handling: YOLOv8 typically outputs [1, 4 + num_classes, 8400]
        preds = raw_tensor
        if len(preds.shape) == 3:
            preds = preds[0]  # Remove batch dim -> (4 + num_classes, 8400) or (8400, 4 + num_classes)

        if preds.shape[0] < preds.shape[1]:
            preds = preds.T  # Transpose to (8400, 4 + num_classes)

        num_classes = preds.shape[1] - 4
        boxes_for_nms = []
        confidences_for_nms = []
        class_ids_for_nms = []

        for row in preds:
            class_scores = row[4:]
            max_score = float(np.max(class_scores))
            if max_score < conf_thresh:
                continue

            class_idx = int(np.argmax(class_scores))
            cx, cy, w, h = float(row[0]), float(row[1]), float(row[2]), float(row[3])

            # Convert center format to top-left [x, y, w, h] for cv2.dnn.NMSBoxes
            x1 = cx - (w / 2.0)
            y1 = cy - (h / 2.0)

            boxes_for_nms.append([x1, y1, w, h])
            confidences_for_nms.append(max_score)
            class_ids_for_nms.append(class_idx)

        if not boxes_for_nms:
            return []

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes_for_nms,
            scores=confidences_for_nms,
            score_threshold=conf_thresh,
            nms_threshold=0.45,
        )

        detections: List[RoadDamageDetection] = []
        if len(indices) == 0:
            return detections

        total_image_pixels = float(prep.orig_width * prep.orig_height)
        flat_indices = indices.flatten() if hasattr(indices, "flatten") else [i[0] for i in indices]

        for idx in flat_indices:
            x, y, w, h = boxes_for_nms[idx]
            conf = confidences_for_nms[idx]
            cls_idx = class_ids_for_nms[idx]

            # Convert to [x_min, y_min, x_max, y_max]
            box_640 = [x, y, x + w, y + h]
            orig_box = ImagePreprocessor.scale_coords_to_original(
                box=box_640,
                ratio=prep.ratio,
                pad_w=prep.pad_w,
                pad_h=prep.pad_h,
                orig_width=prep.orig_width,
                orig_height=prep.orig_height,
            )

            # Look up RDD class information
            class_info = RDD_CLASSES.get(cls_idx, {
                "id": f"D{cls_idx}",
                "name": f"Road Damage Defect {cls_idx}",
                "category": "damage",
            })

            box_area = max(0.0, (orig_box[2] - orig_box[0]) * (orig_box[3] - orig_box[1]))
            rel_area = (box_area / total_image_pixels * 100.0) if total_image_pixels > 0 else 0.0

            detections.append(
                RoadDamageDetection(
                    class_id=class_info["id"],
                    class_name=class_info["name"],
                    confidence=round(conf, 4),
                    bounding_box=orig_box,
                    area_pixels=round(box_area, 1),
                    relative_area_percent=round(rel_area, 2),
                )
            )

        return detections
