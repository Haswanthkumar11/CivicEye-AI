from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class BoundingBox(BaseModel):
    """Normalized or pixel coordinates of a detected defect."""
    x_min: float = Field(..., description="Top-left X coordinate in original image pixels")
    y_min: float = Field(..., description="Top-left Y coordinate in original image pixels")
    x_max: float = Field(..., description="Bottom-right X coordinate in original image pixels")
    y_max: float = Field(..., description="Bottom-right Y coordinate in original image pixels")


class RoadDamageDetection(BaseModel):
    """Individual road damage defect identified by the computer vision model."""
    model_config = ConfigDict(from_attributes=True)

    class_id: str = Field(..., description="Dataset standard class code (e.g. D40, D20, D00, D10)")
    class_name: str = Field(..., description="Human-readable defect name (e.g. Pothole, Alligator Crack)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence score between 0.0 and 1.0")
    bounding_box: List[float] = Field(..., min_length=4, max_length=4, description="[x_min, y_min, x_max, y_max] in pixels")
    area_pixels: float = Field(..., ge=0.0, description="Bounding box area in square pixels")
    relative_area_percent: float = Field(..., ge=0.0, le=100.0, description="Bounding box area as percentage of image")


class RoadDamageAnalysisResult(BaseModel):
    """Complete output payload from local computer vision road damage inference."""
    model_config = ConfigDict(from_attributes=True)

    processing_status: str = Field(
        ...,
        description="Status: SUCCESS, NO_DAMAGE_DETECTED, WEIGHTS_NOT_FOUND, CORRUPT_IMAGE, or ERROR",
    )
    model_name: str = Field(default="YOLO-RDD-Nano", description="Model architecture identifier")
    model_version: str = Field(default="rdd2022-v1", description="Model weight / dataset release version")
    inference_device: str = Field(default="cpu", description="Execution device: cpu or cuda:0")
    inference_time_ms: float = Field(default=0.0, ge=0.0, description="Inference latency in milliseconds")
    image_width: int = Field(default=0, ge=0, description="Original image width in pixels")
    image_height: int = Field(default=0, ge=0, description="Original image height in pixels")
    detection_count: int = Field(default=0, ge=0, description="Total number of road defects detected")
    pothole_detected: bool = Field(default=False, description="True if one or more potholes were detected")
    crack_detected: bool = Field(default=False, description="True if one or more surface cracks were detected")
    estimated_visual_damage_level: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Visual damage estimate (0.0 to 100.0) based on defect types, count, and area",
    )
    visual_evidence_explanation: str = Field(
        ...,
        description="Transparent natural language summary of detected visual defects and their severity impact",
    )
    detections: List[RoadDamageDetection] = Field(
        default_factory=list,
        description="Structured list of detected road damage bounding boxes and classifications",
    )


class RoadDamageDetectionRequest(BaseModel):
    """Input payload for road damage detection endpoint."""
    media_url: Optional[str] = Field(None, description="Internal relative media URL (/uploads/...) to analyze")
    confidence_threshold: Optional[float] = Field(
        default=0.35,
        ge=0.05,
        le=0.95,
        description="Minimum detection confidence threshold (default: 0.35)",
    )
