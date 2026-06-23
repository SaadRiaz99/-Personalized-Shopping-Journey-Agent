import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_register():
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test@1234",
    })
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert data["username"] == "testuser"


def test_register_duplicate():
    resp = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test2@example.com",
        "password": "Test@1234",
    })
    assert resp.status_code == 409


def test_register_weak_password():
    resp = client.post("/api/auth/register", json={
        "username": "weakuser",
        "email": "weak@example.com",
        "password": "short",
    })
    assert resp.status_code == 400


def test_login():
    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234",
    })
    assert resp.status_code == 200, resp.json()
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data


def test_login_wrong_password():
    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "WrongPass@1",
    })
    assert resp.status_code == 401


def test_me():
    login_resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234",
    })
    token = login_resp.json()["access_token"]
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"


def test_me_unauthorized():
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_token_refresh():
    login_resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234",
    })
    refresh_token = login_resp.json()["refresh_token"]
    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_logout():
    login_resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234",
    })
    token = login_resp.json()["access_token"]
    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_change_password():
    login_resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "Test@1234",
    })
    token = login_resp.json()["access_token"]
    resp = client.post("/api/auth/change-password", headers={"Authorization": f"Bearer {token}"}, json={
        "current_password": "Test@1234",
        "new_password": "NewTest@123",
    })
    assert resp.status_code == 200

    resp = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "NewTest@123",
    })
    assert resp.status_code == 200
