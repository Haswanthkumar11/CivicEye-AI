import sys
import os
import uuid
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.database import create_db_engine
from app.services.media_storage import MediaStorageService, media_storage_service
from app.services.ai.road_damage_detector import RoadDamageDetector

client = TestClient(app)


def test_public_admin_self_registration_strictly_prevented():
    """
    CRITICAL SECURITY TEST:
    Verifies that public self-registration attempting to supply role='admin'
    is forced to 'citizen' by the backend.
    """
    email = f"attacker_admin_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Privilege Escalation Attempt",
        "phone_number": "+91 98888 77777",
        "role": "admin"
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["user"]["role"] == "citizen", "CRITICAL: Public user was able to self-assign admin role!"


def test_public_registration_with_arbitrary_role_defaults_to_citizen():
    """
    Verifies that any custom or non-citizen role string in registration
    is coerced to 'citizen'.
    """
    email = f"attacker_officer_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Arbitrary Role Attempt",
        "role": "super_officer"
    })
    assert res.status_code == 201
    assert res.json()["user"]["role"] == "citizen"


def test_production_database_forbids_sqlite_fallback():
    """
    INFRASTRUCTURE GUARD TEST:
    Verifies that in production mode, create_db_engine() raises RuntimeError
    rather than silently creating an ephemeral SQLite file.
    """
    with patch.object(settings, "ENVIRONMENT", "production"):
        with patch.object(settings, "DATABASE_URL", "sqlite:///./ephemeral.db"):
            with pytest.raises(RuntimeError, match="CRITICAL: Production environment is configured with an ephemeral SQLite"):
                create_db_engine()

        # Test unreachable PostgreSQL in production raises RuntimeError
        with patch.object(settings, "DATABASE_URL", "postgresql://fake:fake@nonexistent.invalid.domain:5432/db"):
            with pytest.raises(RuntimeError, match="CRITICAL: Failed to connect to production PostgreSQL database"):
                create_db_engine()


def test_cors_allows_vercel_production_and_preview_origins():
    """
    NETWORK & CORS TEST:
    Verifies that the deployed Vercel production URL and preview subdomains
    receive proper Access-Control-Allow-Origin headers.
    """
    # 1. Check settings origin list contains the production Vercel domain
    assert "https://frontend-jc64-r7u81vqfy-haswanth1.vercel.app" in settings.cors_origins_list

    # 2. Production Vercel URL
    res_prod = client.get("/api/health", headers={
        "Origin": "https://frontend-jc64-r7u81vqfy-haswanth1.vercel.app"
    })
    assert res_prod.status_code == 200
    assert res_prod.headers.get("access-control-allow-origin") == "https://frontend-jc64-r7u81vqfy-haswanth1.vercel.app"

    # 3. Preview Vercel URL (regex-matched)
    res_preview = client.get("/api/health", headers={
        "Origin": "https://civiceye-preview-1234.vercel.app"
    })
    assert res_preview.status_code == 200
    assert res_preview.headers.get("access-control-allow-origin") == "https://civiceye-preview-1234.vercel.app"


def test_health_endpoints_accessible():
    """
    ROUTING TEST:
    Verifies that both /health and /api/health respond with 200 OK.
    """
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert res1.json()["status"] in ["healthy", "ok"]

    res2 = client.get("/api/health")
    assert res2.status_code == 200
    assert res2.json()["status"] in ["healthy", "ok"]


def test_yolo_model_path_resolution_across_working_dirs():
    """
    MODEL RESOLUTION TEST:
    Verifies that RoadDamageDetector and settings resolve weights
    whether in root directory or nested backend/ directory.
    """
    resolved = settings.resolved_yolo_model_path
    assert os.path.isfile(resolved), f"YOLO model weights not found at resolved path: {resolved}"

    detector = RoadDamageDetector()
    assert os.path.isfile(detector.weights_path), f"Detector could not resolve weights path: {detector.weights_path}"


def test_media_storage_service_local_and_rehydration():
    """
    STORAGE TEST:
    Verifies that MediaStorageService stores files locally, rejects path traversal,
    and returns proper URLs.
    """
    storage = MediaStorageService()
    test_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    safe_filename = f"test_{uuid.uuid4().hex[:8]}.png"

    result = storage.store_file(test_data, safe_filename, "image/png")
    assert "file_url" in result
    assert "file_path" in result
    assert os.path.isfile(result["file_path"])

    # Path traversal attempt should raise ValueError
    with pytest.raises(ValueError, match="Path traversal"):
        storage.store_file(test_data, "../../etc/passwd", "image/png")

    # Clean up test file
    if os.path.isfile(result["file_path"]):
        os.remove(result["file_path"])
