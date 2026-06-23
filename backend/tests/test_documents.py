from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_store import vector_store

client = TestClient(app)

TEST_USER = {"username": "doc_test_user", "email": "doc@test.com", "password": "Test@1234"}


@pytest.fixture
def token():
    client.post("/api/auth/register", json=TEST_USER)
    resp = client.post("/api/auth/login", json=TEST_USER)
    return resp.json()["access_token"]


@pytest.fixture
def doc_id(token):
    content = b"This is a test document for RAG processing."
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", content, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    return resp.json()["document"]["id"]


@pytest.fixture(autouse=True)
def mock_vector_store():
    with patch.object(vector_store, "add_chunks", return_value=None), \
         patch.object(vector_store, "delete_document_chunks", return_value=None):
        yield


def test_upload_txt(token):
    content = b"Hello world."
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("hello.txt", content, "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["document"]["filename"] == "hello.txt"
    assert data["document"]["file_type"] == "txt"


def test_list_documents(token, doc_id):
    resp = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "documents" in data
    assert data["total"] >= 1


def test_get_document(token, doc_id):
    resp = client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["document"]["id"] == doc_id


def test_get_document_not_found(token):
    resp = client.get("/api/documents/nonexistent", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_upload_invalid_type(token):
    content = b"not an image"
    resp = client.post(
        "/api/documents/upload",
        files={"file": ("test.png", content, "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_delete_document(token, doc_id):
    resp = client.delete(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = client.get(f"/api/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_upload_unauthorized():
    resp = client.post("/api/documents/upload", files={"file": ("test.txt", b"content", "text/plain")})
    assert resp.status_code == 401
