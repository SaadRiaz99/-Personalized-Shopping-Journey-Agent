import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_USER = {"username": "admin", "password": "Admin@123"}
REG_USER = {"username": "admin_test_reg", "email": "admin_test@test.com", "password": "Test@1234"}


@pytest.fixture
def admin_token():
    resp = client.post("/api/auth/login", json=ADMIN_USER)
    return resp.json()["access_token"]


@pytest.fixture
def user_token():
    client.post("/api/auth/register", json=REG_USER)
    resp = client.post("/api/auth/login", json=REG_USER)
    return resp.json()["access_token"]


def test_admin_stats(admin_token):
    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_documents" in data


def test_admin_stats_unauthorized(user_token):
    resp = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_admin_list_users(admin_token):
    resp = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert "users" in resp.json()
