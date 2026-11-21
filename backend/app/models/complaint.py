import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    tracking_id = Column(String(50), unique=True, index=True, nullable=False)
    citizen_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    severity = Column(String(20), default="MEDIUM", nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    severity_score = Column(Float, default=50.0, nullable=False)  # Deterministic score 0-100
    risk_level = Column(String(20), default="MEDIUM", nullable=False)
    status = Column(String(30), default="SUBMITTED", nullable=False, index=True)  # SUBMITTED, UNDER_REVIEW, ASSIGNED, IN_PROGRESS, RESOLVED, REJECTED
    rejection_reason = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    duplicate_group_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    media = relationship("ComplaintMedia", back_populates="complaint", cascade="all, delete-orphan")
    location = relationship("Location", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    status_history = relationship("ComplaintStatusHistory", back_populates="complaint", cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysisResult", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    resolution_evidence = relationship("ResolutionEvidence", back_populates="complaint", uselist=False, cascade="all, delete-orphan")


class ComplaintMedia(Base):
    __tablename__ = "complaint_media"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    media_type = Column(String(20), nullable=False)  # IMAGE, VIDEO, AUDIO
    file_url = Column(String(1000), nullable=False)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="media")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(500), nullable=True)
    landmark = Column(String(255), nullable=True)
    ward = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="location")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=False, index=True)
    assigned_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    due_at = Column(DateTime, nullable=True)


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    changed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    previous_status = Column(String(30), nullable=False)
    new_status = Column(String(30), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="status_history")


class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    language_detected = Column(String(50), nullable=True)
    transcription_text = Column(Text, nullable=True)
    yolo_detections = Column(JSON, nullable=True)
    gemini_analysis = Column(JSON, nullable=True)
    damage_score = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    impact_score = Column(Float, nullable=True)
    sensitivity_score = Column(Float, nullable=True)
    calculated_severity = Column(Float, nullable=True)
    model_versions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="ai_analysis")


class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    evidence_image_url = Column(String(1000), nullable=False)
    inspection_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="resolution_evidence")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), default="INFO", nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
