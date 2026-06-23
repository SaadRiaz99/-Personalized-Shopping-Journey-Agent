from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.vector_store import vector_store

client = TestClient(app)

TEST_USER = {"username": "conv_test_user", "email": "conv@test.com", "password": "Test@1234"}


@pytest.fixture(autouse=True)
def mock_vector_store():
    with patch.object(vector_store, "add_chunks", return_value=None), \
         patch.object(vector_store, "delete_document_chunks", return_value=None), \
         patch.object(vector_store, "search", return_value={"ids": [[]], "documents": [[]], "distances": [[]], "metadatas": [[]]}):
        yield


@pytest.fixture
def token():
    client.post("/api/auth/register", json=TEST_USER)
    resp = client.post("/api/auth/login", json=TEST_USER)
    return resp.json()["access_token"]


def test_create_conversation(token):
    resp = client.post("/api/conversations", json={
        "title": "Test Conversation",
        "document_ids": [],
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["conversation"]["title"] == "Test Conversation"
    return data["conversation"]["id"]


def test_list_conversations(token):
    resp = client.get("/api/conversations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert "conversations" in resp.json()


def test_get_conversation(token):
    conv_id = test_create_conversation(token)
    resp = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["conversation"]["id"] == conv_id
    assert "messages" in resp.json()


def test_update_conversation(token):
    conv_id = test_create_conversation(token)
    resp = client.patch(f"/api/conversations/{conv_id}", json={
        "title": "Updated Title",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["conversation"]["title"] == "Updated Title"


def test_delete_conversation(token):
    conv_id = test_create_conversation(token)
    resp = client.delete(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_send_chat(token):
    resp = client.post("/api/chat/send", json={
        "message": "Hello, this is a test message",
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    assert "message" in data


def test_get_messages(token):
    resp = client.post("/api/chat/send", json={
        "message": "Test message for history",
    }, headers={"Authorization": f"Bearer {token}"})
    conv_id = resp.json()["conversation_id"]
    resp = client.get(f"/api/chat/{conv_id}/messages", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["total"] > 0
