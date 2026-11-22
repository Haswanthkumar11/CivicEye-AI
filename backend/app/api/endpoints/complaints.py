import os
import re
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
    """Resolves default department UUID based on category code mapping. Returns None if unmapped."""
    dept_code = CATEGORY_DEPARTMENT_MAP.get(category)
    if not dept_code:
        return None
    dept = db.query(Department).filter(Department.code == dept_code).first()
    return dept.id if dept else None


# Allowed media types with category and accepted MIME types
ALLOWED_MEDIA_TYPES = {
    # Images
    "jpg": {"mime": ["image/jpeg", "image/pjpeg"], "category": "IMAGE"},
    "jpeg": {"mime": ["image/jpeg", "image/pjpeg"], "category": "IMAGE"},
    "png": {"mime": ["image/png"], "category": "IMAGE"},
    "webp": {"mime": ["image/webp"], "category": "IMAGE"},
    # Audio recordings
    "wav": {"mime": ["audio/wav", "audio/x-wav", "audio/wave"], "category": "AUDIO"},
    "mp3": {"mime": ["audio/mpeg", "audio/mp3"], "category": "AUDIO"},
    "m4a": {"mime": ["audio/mp4", "audio/x-m4a", "audio/m4a"], "category": "AUDIO"},
    "ogg": {"mime": ["audio/ogg", "application/ogg"], "category": "AUDIO"},
    "aac": {"mime": ["audio/aac", "audio/x-aac"], "category": "AUDIO"},
    "weba": {"mime": ["audio/webm", "audio/weba"], "category": "AUDIO"},
    # Videos
    "mp4": {"mime": ["video/mp4"], "category": "VIDEO"},
    "mov": {"mime": ["video/quicktime"], "category": "VIDEO"},
    "webm": {"mime": ["video/webm"], "category": "VIDEO"},
    "avi": {"mime": ["video/x-msvideo", "video/avi"], "category": "VIDEO"},
}


def verify_file_content_signature(ext: str, data: bytes) -> bool:
    """
    Validates magic bytes against declared extension to prevent MIME-spoofing and stored attacks.
    """
    if len(data) < 4:
        return False

    if ext in ("jpg", "jpeg"):
        return data.startswith(b"\xFF\xD8\xFF")
    elif ext == "png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    elif ext == "webp":
        return data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WEBP"
    elif ext == "wav":
        return data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"WAVE"
    elif ext == "avi":
        return data.startswith(b"RIFF") and len(data) >= 12 and data[8:12] == b"AVI "
    elif ext in ("webm", "weba"):
        return data.startswith(b"\x1A\x45\xDF\xA3")
    elif ext == "ogg":
        return data.startswith(b"OggS")
    elif ext == "mp3":
        return data.startswith(b"ID3") or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)
    elif ext in ("mp4", "mov", "m4a"):
        return b"ftyp" in data[:32] or b"moov" in data[:32]
    elif ext == "aac":
        return data.startswith(b"\xFF\xF1") or data.startswith(b"\xFF\xF9") or data.startswith(b"ID3")
    return True


@router.post("/upload-media", response_model=MediaUploadResponse, summary="Upload Grievance Media (Photo, Video, Voice Recording)")
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Accepts photographs (.jpg, .png, .jpeg, .webp), videos (.mp4, .mov, .webm, .avi), and voice recordings (.wav, .mp3, .m4a, .ogg, .aac, .weba).
    Requires authenticated session to prevent unauthenticated upload abuse.
    Enforces chunked stream size verification (up to 25MB), strict MIME validation, magic-byte inspection, and path sanitization.
    """
    raw_filename = file.filename or "upload.bin"
    clean_basename = os.path.basename(raw_filename.replace("\\", "/"))

    if "." in clean_basename:
        name_part, ext = clean_basename.rsplit(".", 1)
        ext = ext.lower().strip()
    else:
        name_part, ext = "upload", ""

    if ext not in ALLOWED_MEDIA_TYPES:
        allowed_list = sorted(list(ALLOWED_MEDIA_TYPES.keys()))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(allowed_list)}",
        )

    # Stream file contents with strict size limit to prevent memory exhaustion DoS
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    chunk_size = 64 * 1024  # 64 KB
    chunks = []
    total_bytes = 0

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB",
            )
        chunks.append(chunk)

    if total_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot upload an empty file.",
        )

    contents = b"".join(chunks)

    # Verify magic-byte content signature
    if not verify_file_content_signature(ext, contents):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content signature does not match declared '.{ext}' extension or file is corrupted.",
        )

    media_info = ALLOWED_MEDIA_TYPES[ext]
    media_type = media_info["category"]

    # Sanitize filename to avoid any path traversal
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name_part)[:32] or "media"
    stored_filename = f"{uuid.uuid4().hex}_{safe_name}.{ext}"

    upload_dir = os.path.abspath(settings.MEDIA_UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.abspath(os.path.join(upload_dir, stored_filename))

    # Defensive path containment check
    if not file_path.startswith(upload_dir):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid destination path detected.",
        )

    # Write securely to disk
    with open(file_path, "wb") as f:
        f.write(contents)

    relative_url = f"/uploads/{stored_filename}"

    return {
        "file_url": relative_url,
        "file_name": clean_basename,
        "file_path": file_path,
        "file_size": total_bytes,
        "mime_type": file.content_type or media_info["mime"][0],
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

    # Attach Media items with strict validation
    if payload.media:
        for media_item in payload.media:
            # Defensive check: ensure file_url is strictly internal to /uploads/
            if not media_item.file_url or not media_item.file_url.startswith("/uploads/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid media URL: only internal /uploads/ paths are accepted.",
                )
            if ".." in media_item.file_url or "\\" in media_item.file_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Path traversal in media URL is strictly prohibited.",
                )
            if media_item.media_type not in ["IMAGE", "VIDEO", "AUDIO"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="media_type must be IMAGE, VIDEO, or AUDIO.",
                )

            # Defensive canonical path computation
            safe_fname = os.path.basename(media_item.file_url)
            canonical_path = os.path.join(settings.MEDIA_UPLOAD_DIR, safe_fname)

            cm = ComplaintMedia(
                complaint_id=complaint.id,
                media_type=media_item.media_type,
                file_url=media_item.file_url,
                file_path=canonical_path,
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
    Requires administrator or municipal department officer privileges.
    """
    # Strict role check: Citizens cannot update or resolve complaints
    if current_user.role not in ["admin", "superadmin", "department_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to update grievance status.",
        )

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
