import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime
from main import app
from app.models import Trace, RepoInfo

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    data_dir = Path("data")
    for file in data_dir.glob("test-*.json"):
        file.unlink()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_trace(auth_headers):
    trace_data = {
        "trace_id": "test-api-001",
        "developer_id": "dev-api-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-27T10:00:00Z"
    }
    
    response = client.post("/traces", json=trace_data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["trace_id"] == "test-api-001"
    assert response.json()["status"] == "stored"


def test_create_trace_without_id(auth_headers):
    trace_data = {
        "developer_id": "dev-api-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-27T10:00:00Z"
    }
    
    response = client.post("/traces", json=trace_data, headers=auth_headers)
    assert response.status_code == 201
    assert "trace_id" in response.json()
    assert len(response.json()["trace_id"]) == 36


def test_get_trace(auth_headers):
    trace_data = {
        "trace_id": "test-api-002",
        "developer_id": "dev-api-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-27T10:00:00Z"
    }
    
    client.post("/traces", json=trace_data, headers=auth_headers)
    response = client.get("/traces/test-api-002", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "test-api-002"
    assert data["developer_id"] == "dev-api-test"


def test_get_nonexistent_trace(auth_headers):
    response = client.get("/traces/does-not-exist", headers=auth_headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_invalid_trace(auth_headers):
    invalid_data = {
        "developer_id": "dev-test"
    }
    
    response = client.post("/traces", json=invalid_data, headers=auth_headers)
    assert response.status_code == 422


def test_create_and_retrieve_with_events(auth_headers):
    trace_data = {
        "trace_id": "test-api-003",
        "developer_id": "dev-api-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-27T10:00:00Z",
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {
                    "content": "Testing API with events"
                }
            }
        ]
    }
    
    client.post("/traces", json=trace_data, headers=auth_headers)
    response = client.get("/traces/test-api-003", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "reasoning_step"