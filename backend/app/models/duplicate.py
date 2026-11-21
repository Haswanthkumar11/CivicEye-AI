import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from app.core.database import Base


class DuplicateGroup(Base):
    __tablename__ = "duplicate_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(255), nullable=False)
    primary_complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False)  # ACTIVE, MERGED, DISMISSED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class DuplicateRelation(Base):
    __tablename__ = "duplicate_relations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("duplicate_groups.id"), nullable=False, index=True)
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=False)  # 0.0 - 1.0
    matched_by = Column(String(50), default="GEO", nullable=False)  # GEO, TEXT, IMAGE, COMPOSITE
    confirmed_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="SUGGESTED", nullable=False)  # SUGGESTED, CONFIRMED, REJECTED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
