import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ComplaintMediaCreate(BaseModel):
    media_type: str = Field(..., description="IMAGE, VIDEO, or AUDIO")
    file_url: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class ComplaintMediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    media_type: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: Optional[Any] = None


class LocationCreate(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    landmark: Optional[str] = None
    ward: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    landmark: Optional[str] = None
    ward: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None


class StatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    changed_by: Optional[str] = None
    previous_status: str
    new_status: str
    notes: Optional[str] = None
    created_at: Optional[Any] = None


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=5)
    category: str = Field("Other", description="Road Infrastructure, Water Supply, Sanitation, Drainage, Electricity and Streetlights, Public Infrastructure, Other")
    subcategory: Optional[str] = None
    severity: Optional[str] = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    severity_score: Optional[float] = Field(50.0, ge=0.0, le=100.0)
    risk_level: Optional[str] = "MEDIUM"
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    department_id: Optional[str] = None
    media: Optional[List[ComplaintMediaCreate]] = []
    location: Optional[LocationCreate] = None


class ComplaintStatusUpdate(BaseModel):
    status: str = Field(..., description="SUBMITTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS, RESOLVED, REJECTED")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tracking_id: str
    citizen_id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str] = None
    severity: str
    severity_score: float
    risk_level: str
    status: str
    rejection_reason: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    department_id: Optional[str] = None
    duplicate_group_id: Optional[str] = None
    created_at: Optional[Any] = None
    updated_at: Optional[Any] = None

    media: List[ComplaintMediaResponse] = []
    location: Optional[LocationResponse] = None
    status_history: List[StatusHistoryResponse] = []
    department_name: Optional[str] = None


class MediaUploadResponse(BaseModel):
    file_url: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    media_type: str
