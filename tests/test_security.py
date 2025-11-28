import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime
from main import app
from app.storage import save_trace
from app.models import Trace, RepoInfo

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    data_dir = Path("data")
    for file in data_dir.glob("test-*.json"):
        file.unlink()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-123"}


@pytest.fixture
def sample_trace():
    return {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc123",
            "commit_after": "def456",
            "test_command": "pytest"
        },
        "start_time": "2025-11-28T10:00:00Z"
    }


def test_missing_api_key(sample_trace):
    response = client.post("/traces", json=sample_trace)
    assert response.status_code == 401
    assert "Authorization" in response.json()["detail"]


def test_invalid_api_key(sample_trace):
    response = client.post(
        "/traces",
        json=sample_trace,
        headers={"Authorization": "Bearer wrong-token"}
    )
    assert response.status_code == 401


def test_valid_api_key(sample_trace, auth_headers):
    response = client.post("/traces", json=sample_trace, headers=auth_headers)
    assert response.status_code == 201


def test_path_traversal_rejected(auth_headers):
    trace = {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-28T10:00:00Z",
        "events": [
            {
                "event_type": "file_open",
                "timestamp": "2025-11-28T10:01:00Z",
                "data": {"file_path": "../../etc/passwd"}
            }
        ]
    }
    
    response = client.post("/traces", json=trace, headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid file path" in response.json()["detail"]


def test_absolute_path_rejected(auth_headers):
    trace = {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-28T10:00:00Z",
        "events": [
            {
                "event_type": "code_edit",
                "timestamp": "2025-11-28T10:01:00Z",
                "data": {
                    "file_path": "/etc/passwd",
                    "diff": "some change"
                }
            }
        ]
    }
    
    response = client.post("/traces", json=trace, headers=auth_headers)
    assert response.status_code == 400


def test_command_injection_rejected(auth_headers):
    trace = {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest; rm -rf /"
        },
        "start_time": "2025-11-28T10:00:00Z"
    }
    
    response = client.post("/traces", json=trace, headers=auth_headers)
    assert response.status_code == 400
    assert "dangerous patterns" in response.json()["detail"]


def test_command_with_pipe_rejected(auth_headers):
    trace = {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest | grep fail"
        },
        "start_time": "2025-11-28T10:00:00Z"
    }
    
    response = client.post("/traces", json=trace, headers=auth_headers)
    assert response.status_code == 400


def test_valid_relative_path_accepted(auth_headers):
    trace = {
        "developer_id": "dev-test",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-28T10:00:00Z",
        "events": [
            {
                "event_type": "file_open",
                "timestamp": "2025-11-28T10:01:00Z",
                "data": {"file_path": "src/main.py"}
            }
        ]
    }
    
    response = client.post("/traces", json=trace, headers=auth_headers)
    assert response.status_code == 201


def test_append_events_path_validation(auth_headers):
    trace = Trace(
        trace_id="test-security-001",
        developer_id="dev-test",
        repo=RepoInfo(
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_before="abc",
            commit_after="def",
            test_command="pytest"
        ),
        start_time=datetime.now(),
        events=[]
    )
    save_trace(trace)
    
    malicious_events = {
        "events": [
            {
                "event_type": "file_open",
                "timestamp": "2025-11-28T10:01:00Z",
                "data": {"file_path": "../../../etc/passwd"}
            }
        ]
    }
    
    response = client.post(
        "/traces/test-security-001/events",
        json=malicious_events,
        headers=auth_headers
    )
    assert response.status_code == 400

