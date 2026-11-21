import os
import uuid
import random
import string
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.department import Department
from app.models.complaint import (
    Complaint,
    ComplaintMedia,
    Location,
    ComplaintStatusHistory,
)
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
    MediaUploadResponse,
)

router = APIRouter()

# Category to Department Code rule mapping
CATEGORY_DEPARTMENT_MAP = {
    "Road Infrastructure": "ROADS",
    "Water Supply": "WATER",
    "Sanitation": "SANITATION",
    "Drainage": "DRAINAGE",
    "Electricity and Streetlights": "ELECTRICAL",
    "Public Infrastructure": "PUBLIC_INFRA",
}


def generate_tracking_id() -> str:
    """Generates unique civic grievance tracking code e.g. CVE-20261121-AB89"""
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_str = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"CVE-{date_str}-{random_str}"


def resolve_department_id(category: str, db: Session) -> Optional[str]:
    """Resolves default department UUID based on category code mapping"""
    dept_code = CATEGORY_DEPARTMENT_MAP.get(category, "ROADS")
    dept = db.query(Department).filter(Department.code == dept_code).first()
    return dept.id if dept else None


@router.post("/upload-media", response_model=MediaUploadResponse, summary="Upload Grievance Media (Photo, Video, Voice Recording)")
async def upload_media(file: UploadFile = File(...)):
    """
    Accepts photographs (.jpg, .png, .jpeg), videos (.mp4, .mov, .webm), and voice recordings (.wav, .mp3, .m4a, .ogg).
    Validates file size (up to 25MB) and saves securely to media directory.
    """
    allowed_extensions = {
        "jpg", "jpeg", "png", "webp",  # Images
        "wav", "mp3", "m4a", "ogg", "aac", "weba",  # Audio recordings
        "mp4", "mov", "webm", "avi",  # Videos
    }

    filename = file.filename or "upload.bin"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(allowed_extensions))}",
        )

    # Determine media category
    if ext in {"jpg", "jpeg", "png", "webp"}:
        media_type = "IMAGE"
    elif ext in {"wav", "mp3", "m4a", "ogg", "aac", "weba"}:
        media_type = "AUDIO"
    else:
        media_type = "VIDEO"

    # Generate unique stored filename
    stored_filename = f"{uuid.uuid4().hex}_{filename.replace(' ', '_')}"
    os.makedirs(settings.MEDIA_UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.MEDIA_UPLOAD_DIR, stored_filename)

    # Read and check file size
    contents = await file.read()
    file_size = len(contents)
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(contents)

    relative_url = f"/uploads/{stored_filename}"

    return {
        "file_url": relative_url,
        "file_name": filename,
        "file_path": file_path,
        "file_size": file_size,
        "mime_type": file.content_type or "application/octet-stream",
        "media_type": media_type,
    }


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED, summary="Submit a Civic Grievance")
async def create_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a structured civic complaint record.
    Links photos, voice notes, videos, and geographic coordinates.
    Generates unique tracking code and initializes status audit history.
    """
    # Generate unique tracking code
    tracking_id = generate_tracking_id()
    while db.query(Complaint).filter(Complaint.tracking_id == tracking_id).first():
        tracking_id = generate_tracking_id()

    # Determine assigned department if not explicitly given
    department_id = payload.department_id
    if not department_id:
        department_id = resolve_department_id(payload.category, db)

    # Coordinate fallback from location object if set
    lat = payload.latitude
    lon = payload.longitude
    addr = payload.address
    if payload.location:
        if lat is None:
            lat = payload.location.latitude
        if lon is None:
            lon = payload.location.longitude
        if addr is None:
            addr = payload.location.address

    complaint = Complaint(
        tracking_id=tracking_id,
        citizen_id=current_user.id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        subcategory=payload.subcategory,
        severity=payload.severity or "MEDIUM",
        severity_score=payload.severity_score if payload.severity_score is not None else 50.0,
        risk_level=payload.risk_level or "MEDIUM",
        status="SUBMITTED",
        address=addr,
        latitude=lat,
        longitude=lon,
        department_id=department_id,
    )
    db.add(complaint)
    db.flush()  # assign UUID to complaint.id

    # Attach Media items
    if payload.media:
        for media_item in payload.media:
            cm = ComplaintMedia(
                complaint_id=complaint.id,
                media_type=media_item.media_type,
                file_url=media_item.file_url,
                file_path=media_item.file_path,
                file_size=media_item.file_size,
                mime_type=media_item.mime_type,
            )
            db.add(cm)

    # Attach Location
    if lat is not None and lon is not None:
        loc = Location(
            complaint_id=complaint.id,
            latitude=lat,
            longitude=lon,
            address=addr,
            landmark=payload.location.landmark if payload.location else None,
            ward=payload.location.ward if payload.location else None,
            city=payload.location.city if payload.location else "Hyderabad",
            postal_code=payload.location.postal_code if payload.location else None,
        )
        db.add(loc)

    # Create initial status history audit record
    initial_history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by=current_user.id,
        previous_status="NONE",
        new_status="SUBMITTED",
        notes="Citizen grievance recorded in civic intelligence registry.",
    )
    db.add(initial_history)

    db.commit()
    db.refresh(complaint)

    # Set dynamic department_name on model instance for Pydantic serialization
    dept_name = None
    if complaint.department_id:
        dept = db.query(Department).filter(Department.id == complaint.department_id).first()
        dept_name = dept.name if dept else None
    setattr(complaint, "department_name", dept_name)

    return complaint


@router.get("", response_model=List[ComplaintResponse], summary="List Grievances with Filters")
async def list_complaints(
    mine: bool = Query(False, description="Filter complaints submitted by the authenticated citizen"),
    category: Optional[str] = Query(None, description="Filter by complaint category"),
    status: Optional[str] = Query(None, description="Filter by grievance status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns grievances matching criteria.
    Citizens can view their submitted reports; administrators can view all reports.
    """
    query = db.query(Complaint)

    if mine or current_user.role == "citizen":
        query = query.filter(Complaint.citizen_id == current_user.id)

    if category:
        query = query.filter(Complaint.category == category)
    if status:
        query = query.filter(Complaint.status == status)

    complaints = query.order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()

    for c in complaints:
        dept_name = None
        if c.department_id:
            dept = db.query(Department).filter(Department.id == c.department_id).first()
            dept_name = dept.name if dept else None
        setattr(c, "department_name", dept_name)

    return complaints


@router.get("/track/{tracking_id}", summary="Public Complaint Tracker (No Auth Required)")
async def track_complaint(tracking_id: str, db: Session = Depends(get_db)):
    """
    Allows any citizen or public inspector to track status timeline using tracking ID.
    Sanitizes personal identity for public transparency and privacy protection.
    """
    complaint = db.query(Complaint).filter(Complaint.tracking_id == tracking_id.upper().strip()).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No grievance found with tracking ID '{tracking_id}'",
        )

    dept_name = None
    if complaint.department_id:
        dept = db.query(Department).filter(Department.id == complaint.department_id).first()
        dept_name = dept.name if dept else None

    # Status progression sequence
    progression_order = ["SUBMITTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]
    current_index = progression_order.index(complaint.status) if complaint.status in progression_order else -1

    return {
        "id": complaint.id,
        "tracking_id": complaint.tracking_id,
        "title": complaint.title,
        "description": complaint.description,
        "category": complaint.category,
        "subcategory": complaint.subcategory,
        "severity": complaint.severity,
        "severity_score": complaint.severity_score,
        "risk_level": complaint.risk_level,
        "status": complaint.status,
        "rejection_reason": complaint.rejection_reason,
        "department_name": dept_name,
        "address": complaint.address,
        "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
        "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
        "status_history": [
            {
                "previous_status": h.previous_status,
                "new_status": h.new_status,
                "notes": h.notes,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in complaint.status_history
        ],
        "media": [
            {
                "id": m.id,
                "media_type": m.media_type,
                "file_url": m.file_url,
            }
            for m in complaint.media
        ],
        "timeline_stages": [
            {"key": "SUBMITTED", "label": "Submitted", "completed": current_index >= 0},
            {"key": "UNDER_REVIEW", "label": "Under Review", "completed": current_index >= 1},
            {"key": "ASSIGNED", "label": "Assigned to Dept", "completed": current_index >= 2},
            {"key": "IN_PROGRESS", "label": "Field Work in Progress", "completed": current_index >= 3},
            {"key": "RESOLVED", "label": "Resolved & Verified", "completed": current_index >= 4},
        ],
    }


@router.get("/{id}", response_model=ComplaintResponse, summary="Get Full Complaint Details")
async def get_complaint(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns full details for a complaint by UUID ID.
    """
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    # Access control: citizen can only see their own complaints, admin can view all
    if current_user.role == "citizen" and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    dept_name = None
    if complaint.department_id:
        dept = db.query(Department).filter(Department.id == complaint.department_id).first()
        dept_name = dept.name if dept else None
    setattr(complaint, "department_name", dept_name)

    return complaint


@router.patch("/{id}/status", response_model=ComplaintResponse, summary="Update Grievance Status")
async def update_complaint_status(
    id: str,
    update_data: ComplaintStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the status of a complaint and appends to the audit history.
    """
    complaint = db.query(Complaint).filter(Complaint.id == id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")

    prev_status = complaint.status
    new_status = update_data.status.upper().strip()

    valid_statuses = {"SUBMITTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed values: {', '.join(valid_statuses)}",
        )

    if new_status == "REJECTED" and not update_data.rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A rejection_reason is mandatory when rejecting a complaint.",
        )

    complaint.status = new_status
    if update_data.rejection_reason:
        complaint.rejection_reason = update_data.rejection_reason

    # Add audit log
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        changed_by=current_user.id,
        previous_status=prev_status,
        new_status=new_status,
        notes=update_data.notes or f"Status changed from {prev_status} to {new_status}.",
    )
    db.add(history)
    db.commit()
    db.refresh(complaint)

    dept_name = None
    if complaint.department_id:
        dept = db.query(Department).filter(Department.id == complaint.department_id).first()
        dept_name = dept.name if dept else None
    setattr(complaint, "department_name", dept_name)

    return complaint
