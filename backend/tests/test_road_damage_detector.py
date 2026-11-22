import sys
import os
import io
import time
import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db
from app.core.config import settings
from app.services.ai.detection_schemas import (
    RoadDamageDetection,
    RoadDamageAnalysisResult,
    RoadDamageDetectionRequest,
)
from app.services.ai.image_preprocessor import ImagePreprocessor, PreprocessedImageData
from app.services.ai.road_damage_detector import RoadDamageDetector, RDD_CLASSES
from app.services.ai.model_registry import ModelRegistry, IRoadDamageDetector
from app.services.ai.ai_pipeline import AIPipeline
from app.services.ai.schemas import ComplaintAnalysisRequest

init_db()
client = TestClient(app)


def get_citizen_token():
    res = client.post("/api/auth/demo-login", json={"role": "citizen"})
    assert res.status_code == 200
    return res.json()["access_token"]


def create_dummy_image(file_path: str, width: int = 640, height: int = 480):
    """Creates a temporary synthetic image for testing."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # Add simple gradient to mimic asphalt texture
    img[:, :] = [100, 100, 100]
    cv2.imwrite(file_path, img)


# ==============================================================================
# 1. Model Registry Lazy Loading
# ==============================================================================

def test_model_registry_lazy_loading():
    """Verify detector is not loaded prematurely until inference is requested."""
    detector = RoadDamageDetector(weights_path="models/weights/non_existent.onnx")
    assert detector.is_ready() is False
    assert detector.device == "cpu"


# ==============================================================================
# 2. Model Initialization Failure Handling
# ==============================================================================

def test_model_initialization_failure():
    """Verify missing weights file fails gracefully without unhandled exceptions."""
    detector = RoadDamageDetector(weights_path="models/weights/missing_weights.onnx")
    loaded = detector.load()
    assert loaded is False
    assert detector.is_ready() is False


# ==============================================================================
# 3. CPU Fallback Behavior
# ==============================================================================

def test_cpu_fallback_when_cuda_unavailable():
    """Verify requesting CUDA device falls back to CPU when CUDA provider is missing."""
    detector = RoadDamageDetector(device="cuda:0")
    with patch("onnxruntime.get_available_providers", return_value=["CPUExecutionProvider"]):
        # Test provider selection logic
        detector.load("models/weights/non_existent.onnx", device="cuda:0")
        assert detector.device == "cpu"


# ==============================================================================
# 4. GPU Availability Detection
# ==============================================================================

def test_gpu_availability_detection():
    """Verify detection logic accurately checks CUDA provider."""
    with patch("onnxruntime.get_available_providers", return_value=["CUDAExecutionProvider", "CPUExecutionProvider"]):
        detector = RoadDamageDetector(device="cuda:0")
        with patch("os.path.isfile", return_value=True), \
             patch("onnxruntime.InferenceSession") as mock_sess:
            mock_instance = MagicMock()
            mock_instance.get_inputs.return_value = [MagicMock(name="images", shape=[1, 3, 640, 640])]
            mock_sess.return_value = mock_instance
            loaded = detector.load("models/weights/dummy.onnx", device="cuda:0")
            assert loaded is True
            assert detector.device == "cuda:0"
            detector.unload()
            assert detector.is_ready() is False


# ==============================================================================
# 5. Image Preprocessing & Letterboxing
# ==============================================================================

def test_image_preprocessing_letterbox(tmp_path):
    """Verify OpenCV letterbox transforms arbitrary dimensions to exact 640x640 float32 tensor."""
    img_path = str(tmp_path / "test_800x600.jpg")
    create_dummy_image(img_path, width=800, height=600)

    image, err = ImagePreprocessor.load_image(img_path)
    assert err is None
    assert image is not None
    assert image.shape == (600, 800, 3)

    prep = ImagePreprocessor.letterbox(image, target_size=(640, 640))
    assert isinstance(prep, PreprocessedImageData)
    assert prep.tensor.shape == (1, 3, 640, 640)
    assert prep.tensor.dtype == np.float32
    assert 0.0 <= prep.tensor.min() <= prep.tensor.max() <= 1.0
    assert prep.orig_width == 800
    assert prep.orig_height == 600


# ==============================================================================
# 6. Invalid Image File Rejection
# ==============================================================================

def test_invalid_image_rejection(tmp_path):
    """Verify non-image formats, zero-byte files, and non-existent files are rejected."""
    # 1. Non-existent file
    valid, err = ImagePreprocessor.validate_file(str(tmp_path / "not_there.jpg"))
    assert valid is False
    assert "not found" in err.lower()

    # 2. Unsupported extension
    txt_path = str(tmp_path / "test.txt")
    with open(txt_path, "w") as f:
        f.write("text content")
    valid, err = ImagePreprocessor.validate_file(txt_path)
    assert valid is False
    assert "unsupported" in err.lower()

    # 3. Empty file
    empty_jpg = str(tmp_path / "empty.jpg")
    with open(empty_jpg, "wb") as f:
        pass
    valid, err = ImagePreprocessor.validate_file(empty_jpg)
    assert valid is False
    assert "empty" in err.lower()


# ==============================================================================
# 7. Corrupt Image Handling
# ==============================================================================

def test_corrupt_image_handling(tmp_path):
    """Verify corrupt binary data returns CORRUPT_IMAGE status safely."""
    corrupt_jpg = str(tmp_path / "corrupt.jpg")
    with open(corrupt_jpg, "wb") as f:
        f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01corrupt_random_bytes_xxyyzz")

    detector = RoadDamageDetector()
    res = detector.detect(corrupt_jpg)
    assert res.processing_status in ["CORRUPT_IMAGE", "ERROR"]
    assert res.detection_count == 0


# ==============================================================================
# 8. Empty Detection Results
# ==============================================================================

def test_empty_detection_results(tmp_path):
    """Verify zero detections above threshold returns NO_DAMAGE_DETECTED without error."""
    img_path = str(tmp_path / "clean_road.jpg")
    create_dummy_image(img_path, width=640, height=480)

    detector = RoadDamageDetector()
    # Mock ready session returning zeros (no detections)
    mock_session = MagicMock()
    # Output tensor shape [1, 8, 8400]: 4 coords + 4 class scores all 0.0
    mock_session.run.return_value = [np.zeros((1, 8, 8400), dtype=np.float32)]
    mock_input = MagicMock()
    mock_input.name = "images"
    mock_session.get_inputs.return_value = [mock_input]

    detector._loaded = True
    detector._session = mock_session
    detector._input_name = "images"

    res = detector.detect(img_path, confidence_threshold=0.35)
    assert res.processing_status == "NO_DAMAGE_DETECTED"
    assert res.detection_count == 0
    assert res.pothole_detected is False
    assert res.crack_detected is False
    assert res.estimated_visual_damage_level == 20.0
    assert "no road surface cavities" in res.visual_evidence_explanation.lower()


# ==============================================================================
# 9. Multiple Detection Results (Pothole & Cracks)
# ==============================================================================

def test_multiple_detection_results(tmp_path):
    """Verify parser extracts multiple defects with correct RDD class mapping."""
    img_path = str(tmp_path / "damaged_road.jpg")
    create_dummy_image(img_path, width=640, height=480)

    detector = RoadDamageDetector()
    mock_session = MagicMock()

    # Construct synthetic output: [1, 8, 8400]
    # Row format: cx, cy, w, h, D00_score, D10_score, D20_score, D40_score
    out = np.zeros((1, 8, 8400), dtype=np.float32)
    # Box 1: Pothole (D40 -> class index 3, score = 0.88)
    out[0, 0, 10] = 320.0  # cx
    out[0, 1, 10] = 240.0  # cy
    out[0, 2, 10] = 100.0  # w
    out[0, 3, 10] = 80.0   # h
    out[0, 7, 10] = 0.88   # D40 pothole score

    # Box 2: Alligator Crack (D20 -> class index 2, score = 0.76)
    out[0, 0, 50] = 150.0  # cx
    out[0, 1, 50] = 150.0  # cy
    out[0, 2, 50] = 80.0   # w
    out[0, 3, 50] = 60.0   # h
    out[0, 6, 50] = 0.76   # D20 alligator crack score

    mock_session.run.return_value = [out]
    mock_input = MagicMock()
    mock_input.name = "images"
    mock_session.get_inputs.return_value = [mock_input]

    detector._loaded = True
    detector._session = mock_session
    detector._input_name = "images"

    res = detector.detect(img_path, confidence_threshold=0.35)
    assert res.processing_status == "SUCCESS"
    assert res.detection_count == 2
    assert res.pothole_detected is True
    assert res.crack_detected is True
    assert res.estimated_visual_damage_level >= 70.0

    class_names = [d.class_name for d in res.detections]
    assert "Pothole" in class_names
    assert "Alligator Crack" in class_names


# ==============================================================================
# 10. Confidence Threshold Filtering
# ==============================================================================

def test_confidence_threshold_filtering(tmp_path):
    """Verify detections below confidence threshold are strictly excluded."""
    img_path = str(tmp_path / "low_conf_road.jpg")
    create_dummy_image(img_path, width=640, height=480)

    detector = RoadDamageDetector()
    mock_session = MagicMock()

    # Synthetic output with confidence 0.25 (below default 0.35 threshold)
    out = np.zeros((1, 8, 8400), dtype=np.float32)
    out[0, 0, 5] = 200.0
    out[0, 1, 5] = 200.0
    out[0, 2, 5] = 50.0
    out[0, 3, 5] = 50.0
    out[0, 7, 5] = 0.25  # Below 0.35

    mock_session.run.return_value = [out]
    mock_input = MagicMock()
    mock_input.name = "images"
    mock_session.get_inputs.return_value = [mock_input]

    detector._loaded = True
    detector._session = mock_session
    detector._input_name = "images"

    # With threshold 0.35 -> 0 detections
    res_filtered = detector.detect(img_path, confidence_threshold=0.35)
    assert res_filtered.detection_count == 0

    # With lower threshold 0.20 -> 1 detection
    res_included = detector.detect(img_path, confidence_threshold=0.20)
    assert res_included.detection_count == 1
    assert res_included.detections[0].confidence == 0.25


# ==============================================================================
# 11. Bounding Box Coordinate Inversion & Clamping
# ==============================================================================

def test_bounding_box_coordinate_conversion():
    """Verify letterbox padding and scaling are accurately inverted into original image space."""
    # Letterbox with target 640x640 for an original 1280x720 image
    # ratio = 640 / 1280 = 0.5
    # new_h = 720 * 0.5 = 360, pad_h = (640 - 360)/2 = 140
    # pad_w = 0.0
    orig_w, orig_h = 1280, 720
    ratio = 0.5
    pad_w = 0.0
    pad_h = 140.0

    # Box in 640x640: [100, 190, 300, 340]
    box_640 = [100.0, 190.0, 300.0, 340.0]
    orig_box = ImagePreprocessor.scale_coords_to_original(
        box=box_640,
        ratio=ratio,
        pad_w=pad_w,
        pad_h=pad_h,
        orig_width=orig_w,
        orig_height=orig_h,
    )

    # Expected: x_min = 100/0.5 = 200, y_min = (190-140)/0.5 = 100
    #           x_max = 300/0.5 = 600, y_max = (340-140)/0.5 = 400
    assert orig_box == [200.0, 100.0, 600.0, 400.0]


# ==============================================================================
# 12. Detection Result Schema Validation
# ==============================================================================

def test_detection_result_schema_validation():
    """Verify Pydantic schema validation for RoadDamageDetection and AnalysisResult."""
    det = RoadDamageDetection(
        class_id="D40",
        class_name="Pothole",
        confidence=0.895,
        bounding_box=[10.0, 20.0, 110.0, 120.0],
        area_pixels=10000.0,
        relative_area_percent=3.25,
    )
    assert det.class_id == "D40"
    assert det.confidence == 0.895

    res = RoadDamageAnalysisResult(
        processing_status="SUCCESS",
        model_name="YOLO-RDD-Nano",
        model_version="rdd2022-v1",
        inference_device="cpu",
        inference_time_ms=25.4,
        image_width=1280,
        image_height=720,
        detection_count=1,
        pothole_detected=True,
        crack_detected=False,
        estimated_visual_damage_level=85.0,
        visual_evidence_explanation="Detected 1 Pothole (89.5% conf).",
        detections=[det],
    )
    assert res.detection_count == 1
    assert res.pothole_detected is True
    assert res.detections[0].class_name == "Pothole"


# ==============================================================================
# 13. Integration with Severity Engine
# ==============================================================================

@pytest.mark.anyio
async def test_integration_with_severity_engine(tmp_path):
    """Verify visual road damage evidence modulates physical damage in AIPipeline."""
    img_name = "test_pipeline_pothole.jpg"
    img_path = os.path.join(settings.MEDIA_UPLOAD_DIR, img_name)
    create_dummy_image(img_path, width=640, height=480)

    try:
        # Mock detector returning high visual damage
        mock_detector = MagicMock(spec=IRoadDamageDetector)
        mock_cv_res = RoadDamageAnalysisResult(
            processing_status="SUCCESS",
            model_name="YOLO-RDD-Nano",
            model_version="rdd2022-v1",
            inference_device="cpu",
            inference_time_ms=30.0,
            image_width=640,
            image_height=480,
            detection_count=2,
            pothole_detected=True,
            crack_detected=False,
            estimated_visual_damage_level=90.0,
            visual_evidence_explanation="Visual AI: Detected 2 severe potholes.",
            detections=[],
        )
        mock_detector.detect.return_value = mock_cv_res

        pipeline = AIPipeline(cv_detector=mock_detector)

        req = ComplaintAnalysisRequest(
            text="Dangerous road cavity on highway near junction",
            category_hint="Road Infrastructure",
            media_urls=[f"/uploads/{img_name}"],
        )

        res = await pipeline.analyze(req)
        assert res.yolo_analysis is not None
        assert res.yolo_analysis["pothole_detected"] is True
        assert res.yolo_analysis["detection_count"] == 2
        # Verify visual damage modulated severity calculation
        assert "Visual AI: Detected 2 severe potholes" in res.severity.calculation_explanation
    finally:
        if os.path.isfile(img_path):
            os.remove(img_path)


# ==============================================================================
# 14. YOLO Failure & Fallback Path
# ==============================================================================

@pytest.mark.anyio
async def test_yolo_failure_fallback():
    """Verify AIPipeline proceeds gracefully when YOLO fails or weights are missing."""
    mock_detector = MagicMock(spec=IRoadDamageDetector)
    # Simulate unhandled exception or missing weights in detector
    mock_detector.detect.side_effect = RuntimeError("Weights file corrupted or missing")

    pipeline = AIPipeline(cv_detector=mock_detector)
    req = ComplaintAnalysisRequest(
        text="Deep road pothole on main street",
        category_hint="Road Infrastructure",
        media_urls=["/uploads/non_existent.jpg"],
    )

    # Should NOT throw exception; pipeline must complete cleanly via fallback
    res = await pipeline.analyze(req)
    assert res.status in ["COMPLETED", "FALLBACK"]
    assert res.severity.final_score > 0.0
    assert res.routing.department_code == "ROADS"


# ==============================================================================
# 15. API Endpoint Authentication & Input Validation
# ==============================================================================

def test_api_detect_road_damage_unauthenticated_rejected():
    """Verify /api/ai/detect-road-damage rejects unauthenticated callers with 401."""
    res = client.post("/api/ai/detect-road-damage", data={"media_url": "/uploads/test.jpg"})
    assert res.status_code == 401


def test_api_detect_road_damage_path_traversal_rejected():
    """Verify path traversal in media_url is strictly rejected with 400."""
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.post(
        "/api/ai/detect-road-damage",
        data={"media_url": "/uploads/../../etc/passwd"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "invalid media url" in res.json()["detail"].lower()


def test_api_detect_road_damage_authenticated_file_upload(tmp_path):
    """Verify authenticated image upload executes detection endpoint successfully."""
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Generate test image in memory
    img = np.zeros((300, 400, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    file_bytes = io.BytesIO(buf.tobytes())

    res = client.post(
        "/api/ai/detect-road-damage",
        files={"file": ("test_road.jpg", file_bytes, "image/jpeg")},
        data={"confidence_threshold": "0.35"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "processing_status" in data
    assert "model_name" in data
    assert "detection_count" in data
    assert "estimated_visual_damage_level" in data
