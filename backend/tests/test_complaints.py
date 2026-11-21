import sys
import os
import io
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db

init_db()

client = TestClient(app)


def get_citizen_token():
    res = client.post("/api/auth/demo-login", json={"role": "citizen"})
    assert res.status_code == 200
    return res.json()["access_token"]


def get_admin_token():
    res = client.post("/api/auth/demo-login", json={"role": "admin"})
    assert res.status_code == 200
    return res.json()["access_token"]


def create_dynamic_user(role: str = "citizen"):
    unique_id = uuid.uuid4().hex[:8]
    email = f"user_{role}_{unique_id}@civiceye.gov"
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password@123",
        "full_name": f"Test {role.capitalize()} {unique_id}",
        "role": role,
    })
    assert res.status_code == 201, res.text
    return res.json()["access_token"], res.json()["user"]


def test_media_upload():
    # Simulate a small fake PNG file upload
    fake_png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("pothole_sample.png", io.BytesIO(fake_png_data), "image/png")}
    
    res = client.post("/api/complaints/upload-media", files=files)
    assert res.status_code == 200, res.text
    data = res.json()
    assert "file_url" in data
    assert data["media_type"] == "IMAGE"
    assert data["file_url"].startswith("/uploads/")


def test_media_upload_unsupported_format_rejected():
    files = {"file": ("bad_script.exe", io.BytesIO(b"malicious_bytes"), "application/octet-stream")}
    res = client.post("/api/complaints/upload-media", files=files)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_successful_complaint_submission():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    complaint_payload = {
        "title": "Severe Road Pothole near Main Market",
        "description": "Large cavity causing severe vehicle damage and risk of two-wheeler accidents.",
        "category": "Road Infrastructure",
        "subcategory": "Pothole / Road Cavity",
        "severity": "HIGH",
        "severity_score": 75.0,
        "risk_level": "HIGH",
        "address": "Opposite Gandhi Statue, Ward 4, Hyderabad",
        "latitude": 17.3850,
        "longitude": 78.4867,
        "location": {
            "latitude": 17.3850,
            "longitude": 78.4867,
            "address": "Opposite Gandhi Statue, Ward 4, Hyderabad",
            "ward": "Ward 4",
            "city": "Hyderabad"
        },
        "media": [
            {
                "media_type": "IMAGE",
                "file_url": "/uploads/test_pothole_01.jpg",
                "file_size": 102400,
                "mime_type": "image/jpeg"
            }
        ]
    }

    res = client.post("/api/complaints", json=complaint_payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["title"] == complaint_payload["title"]
    assert data["status"] == "SUBMITTED"
    assert data["tracking_id"].startswith("CVE-")
    assert data["department_name"] == "Municipal Roads & Infrastructure"
    assert len(data["media"]) == 1
    assert data["location"]["latitude"] == 17.3850


def test_unauthorized_submission_rejected():
    complaint_payload = {
        "title": "Unauthorized submission attempt",
        "description": "Should fail with 401 Unauthorized",
        "category": "Sanitation",
    }
    # No Authorization header
    res = client.post("/api/complaints", json=complaint_payload)
    assert res.status_code == 401

    # Invalid token
    res2 = client.post("/api/complaints", json=complaint_payload, headers={"Authorization": "Bearer invalid_token_123"})
    assert res2.status_code == 401


def test_invalid_payload_rejected():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Missing description (description has min_length=5)
    res = client.post("/api/complaints", json={"title": "Short title only"}, headers=headers)
    assert res.status_code == 422

    # Title too short (< 3 characters)
    res2 = client.post("/api/complaints", json={"title": "No", "description": "Valid description length"}, headers=headers)
    assert res2.status_code == 422


def test_complaint_retrieval():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Create a complaint
    create_res = client.post("/api/complaints", json={
        "title": "Retrievable Complaint Record",
        "description": "Ensuring complaints can be queried by ID.",
        "category": "Drainage",
    }, headers=headers)
    assert create_res.status_code == 201
    complaint_id = create_res.json()["id"]

    # Retrieve by ID
    get_res = client.get(f"/api/complaints/{complaint_id}", headers=headers)
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == complaint_id
    assert retrieved["title"] == "Retrievable Complaint Record"
    assert retrieved["category"] == "Drainage"


def test_citizen_data_isolation():
    # Citizen A and Citizen B
    token_a, user_a = create_dynamic_user(role="citizen")
    token_b, user_b = create_dynamic_user(role="citizen")

    # Citizen A creates Complaint A
    res_a = client.post("/api/complaints", json={
        "title": "Citizen A Private Grievance",
        "description": "This grievance belongs exclusively to Citizen A.",
        "category": "Sanitation",
    }, headers={"Authorization": f"Bearer {token_a}"})
    assert res_a.status_code == 201
    complaint_a_id = res_a.json()["id"]

    # Citizen B creates Complaint B
    res_b = client.post("/api/complaints", json={
        "title": "Citizen B Private Grievance",
        "description": "This grievance belongs exclusively to Citizen B.",
        "category": "Water Supply",
    }, headers={"Authorization": f"Bearer {token_b}"})
    assert res_b.status_code == 201
    complaint_b_id = res_b.json()["id"]

    # Citizen B queries complaints: must only receive Citizen B's complaint
    list_res_b = client.get("/api/complaints", headers={"Authorization": f"Bearer {token_b}"})
    assert list_res_b.status_code == 200
    b_ids = [c["id"] for c in list_res_b.json()]
    assert complaint_b_id in b_ids
    assert complaint_a_id not in b_ids

    # Citizen B attempts to access Citizen A's complaint directly: must return 403 Forbidden
    direct_res = client.get(f"/api/complaints/{complaint_a_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert direct_res.status_code == 403
    assert "Access denied" in direct_res.json()["detail"]


def test_administrator_access():
    token_citizen, _ = create_dynamic_user(role="citizen")
    token_admin = get_admin_token()

    # Citizen creates a complaint
    res = client.post("/api/complaints", json={
        "title": "Hazard for Administrative Review",
        "description": "Testing that admins can review all municipal reports.",
        "category": "Public Infrastructure",
    }, headers={"Authorization": f"Bearer {token_citizen}"})
    assert res.status_code == 201
    complaint_id = res.json()["id"]

    # Administrator can view the citizen's complaint by ID
    admin_get = client.get(f"/api/complaints/{complaint_id}", headers={"Authorization": f"Bearer {token_admin}"})
    assert admin_get.status_code == 200
    assert admin_get.json()["id"] == complaint_id

    # Administrator can view the full administrative queue
    admin_list = client.get("/api/complaints", headers={"Authorization": f"Bearer {token_admin}"})
    assert admin_list.status_code == 200
    all_ids = [c["id"] for c in admin_list.json()]
    assert complaint_id in all_ids


def test_media_metadata_persistence():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    complaint_payload = {
        "title": "Multimodal Grievance with Image and Audio",
        "description": "Verifying persistence of photo and audio metadata.",
        "category": "Road Infrastructure",
        "media": [
            {
                "media_type": "IMAGE",
                "file_url": "/uploads/road_defect.jpg",
                "file_size": 204800,
                "mime_type": "image/jpeg",
            },
            {
                "media_type": "AUDIO",
                "file_url": "/uploads/voice_report.webm",
                "file_size": 51200,
                "mime_type": "audio/webm",
            },
        ],
    }

    res = client.post("/api/complaints", json=complaint_payload, headers=headers)
    assert res.status_code == 201
    complaint_id = res.json()["id"]

    # Fetch complaint and verify media records
    get_res = client.get(f"/api/complaints/{complaint_id}", headers=headers)
    assert get_res.status_code == 200
    media_items = get_res.json()["media"]
    assert len(media_items) == 2
    types = {m["media_type"] for m in media_items}
    assert "IMAGE" in types
    assert "AUDIO" in types


def test_tracking_id_uniqueness():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    tracking_ids = set()
    for i in range(4):
        res = client.post("/api/complaints", json={
            "title": f"Batch Complaint {i}",
            "description": f"Verifying unique tracking ID generation iteration {i}.",
            "category": "Sanitation",
        }, headers=headers)
        assert res.status_code == 201
        tid = res.json()["tracking_id"]
        assert tid.startswith("CVE-")
        assert tid not in tracking_ids
        tracking_ids.add(tid)

    assert len(tracking_ids) == 4


def test_status_history_persistence():
    token = get_citizen_token()
    admin_token = get_admin_token()

    # Create complaint
    create_res = client.post("/api/complaints", json={
        "title": "Status Audit Trail Verification",
        "description": "Testing state machine transitions and audit trail logging.",
        "category": "Electricity and Streetlights",
    }, headers={"Authorization": f"Bearer {token}"})
    assert create_res.status_code == 201
    complaint = create_res.json()
    complaint_id = complaint["id"]

    # Verify initial SUBMITTED audit log
    assert len(complaint["status_history"]) >= 1
    assert complaint["status_history"][0]["new_status"] == "SUBMITTED"

    # Transition to UNDER_REVIEW
    patch1 = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "UNDER_REVIEW", "notes": "Under preliminary review by municipal officer."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch1.status_code == 200
    assert patch1.json()["status"] == "UNDER_REVIEW"

    # Transition to ASSIGNED
    patch2 = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "ASSIGNED", "notes": "Work order dispatched to Field Division #3."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert patch2.status_code == 200
    assert patch2.json()["status"] == "ASSIGNED"

    # Fetch complaint and verify complete audit history
    get_res = client.get(f"/api/complaints/{complaint_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get_res.status_code == 200
    history = get_res.json()["status_history"]
    assert len(history) == 3
    statuses = [h["new_status"] for h in history]
    assert statuses == ["SUBMITTED", "UNDER_REVIEW", "ASSIGNED"]


def test_track_complaint_public():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/api/complaints", json={
        "title": "Public Tracking Verification",
        "description": "Testing open transparency tracking without authentication.",
        "category": "Water Supply",
    }, headers=headers)
    assert create_res.status_code == 201
    tracking_id = create_res.json()["tracking_id"]

    # Track publicly without Authorization header
    track_res = client.get(f"/api/complaints/track/{tracking_id}")
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert track_data["tracking_id"] == tracking_id
    assert track_data["status"] == "SUBMITTED"
    assert len(track_data["timeline_stages"]) == 5
    assert track_data["timeline_stages"][0]["completed"] is True
