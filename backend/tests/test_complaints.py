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


def test_create_complaint():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    complaint_payload = {
        "title": "Severe Road Pothole near Main Market",
        "description": "Large cavity causing severe vehicle damage and risk of two-wheeler accidents.",
        "category": "Road Infrastructure",
        "subcategory": "Pothole",
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


def test_list_complaints():
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/complaints?mine=true", headers=headers)
    assert res.status_code == 200
    complaints = res.json()
    assert isinstance(complaints, list)
    assert len(complaints) >= 1
    assert "tracking_id" in complaints[0]


def test_track_complaint_public():
    # First create a complaint
    token = get_citizen_token()
    headers = {"Authorization": f"Bearer {token}"}
    create_res = client.post("/api/complaints", json={
        "title": "Streetlight Broken and Dark Junction",
        "description": "Lamp fixture broken and hanging dangerously.",
        "category": "Electricity and Streetlights",
        "severity": "MEDIUM",
        "severity_score": 55.0,
        "latitude": 17.4000,
        "longitude": 78.4900
    }, headers=headers)
    assert create_res.status_code == 201
    tracking_id = create_res.json()["tracking_id"]

    # Now track publicly WITHOUT any auth header
    track_res = client.get(f"/api/complaints/track/{tracking_id}")
    assert track_res.status_code == 200
    track_data = track_res.json()
    assert track_data["tracking_id"] == tracking_id
    assert track_data["status"] == "SUBMITTED"
    assert len(track_data["timeline_stages"]) == 5
    assert track_data["timeline_stages"][0]["completed"] is True


def test_update_complaint_status():
    token = get_citizen_token()
    admin_token = get_admin_token()

    # Create complaint
    create_res = client.post("/api/complaints", json={
        "title": "Contaminated Tap Water Supply",
        "description": "Muddy brown water pouring from community taps.",
        "category": "Water Supply",
        "severity": "CRITICAL",
        "severity_score": 90.0,
    }, headers={"Authorization": f"Bearer {token}"})
    assert create_res.status_code == 201
    complaint_id = create_res.json()["id"]

    # Transition to UNDER_REVIEW
    patch_res = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "UNDER_REVIEW", "notes": "Initial municipal triage review begun."},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "UNDER_REVIEW"

    # Transition to ASSIGNED
    patch_res2 = client.patch(
        f"/api/complaints/{complaint_id}/status",
        json={"status": "ASSIGNED", "notes": "Dispatched to Water Board Emergency Division."},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "ASSIGNED"
    assert len(patch_res2.json()["status_history"]) >= 3
