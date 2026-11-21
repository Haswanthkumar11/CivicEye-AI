import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.init_db import init_db

# Initialize database tables before test execution
init_db()

client = TestClient(app)


def test_seed_demo_accounts_exist():
    # Test logging in with seeded citizen credentials
    res = client.post("/api/auth/login", json={
        "email": "citizen@civiceye.gov",
        "password": "Citizen@123"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "citizen"

    # Test logging in with seeded admin credentials
    res_admin = client.post("/api/auth/login", json={
        "email": "admin@civiceye.gov",
        "password": "Admin@123"
    })
    assert res_admin.status_code == 200, res_admin.text
    data_admin = res_admin.json()
    assert "access_token" in data_admin
    assert data_admin["user"]["role"] == "admin"


import uuid

def test_user_registration():
    new_email = f"tester_citizen_{uuid.uuid4().hex[:8]}@example.com"
    res = client.post("/api/auth/register", json={
        "email": new_email,
        "password": "StrongPassword!123",
        "full_name": "Test Citizen User",
        "phone_number": "+91 91234 56789",
        "role": "citizen"
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == new_email
    assert data["user"]["role"] == "citizen"


def test_duplicate_registration_rejected():
    res = client.post("/api/auth/register", json={
        "email": "citizen@civiceye.gov",
        "password": "AnyPassword123",
        "full_name": "Duplicate Tester"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_invalid_login_rejected():
    res = client.post("/api/auth/login", json={
        "email": "citizen@civiceye.gov",
        "password": "WrongPassword999"
    })
    assert res.status_code == 401


def test_get_me_authenticated():
    # Login first
    login_res = client.post("/api/auth/login", json={
        "email": "admin@civiceye.gov",
        "password": "Admin@123"
    })
    token = login_res.json()["access_token"]

    # Call /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_res.status_code == 200
    user_info = me_res.json()
    assert user_info["email"] == "admin@civiceye.gov"
    assert user_info["role"] == "admin"


def test_demo_login_endpoints():
    # Citizen demo login
    res_cit = client.post("/api/auth/demo-login", json={"role": "citizen"})
    assert res_cit.status_code == 200
    assert res_cit.json()["user"]["role"] == "citizen"

    # Admin demo login
    res_adm = client.post("/api/auth/demo-login", json={"role": "admin"})
    assert res_adm.status_code == 200
    assert res_adm.json()["user"]["role"] == "admin"
