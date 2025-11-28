import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from datetime import datetime
from main import app
from app.storage import save_trace
from app.models import Trace, RepoInfo
from app.models import ReasoningStepEvent

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    data_dir = Path("data")
    for file in data_dir.glob("test-*.json"):
        file.unlink()


@pytest.fixture
def base_trace():
    return Trace(
        trace_id="test-incremental-001",
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


def test_append_events_to_existing_trace(base_trace, auth_headers):
    save_trace(base_trace)
    
    new_events = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {
                    "content": "First reasoning step"
                }
            },
            {
                "event_type": "file_open",
                "timestamp": "2025-11-27T10:02:00Z",
                "data": {
                    "file_path": "src/test.py"
                }
            }
        ]
    }
    
    response = client.post("/traces/test-incremental-001/events", json=new_events, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["trace_id"] == "test-incremental-001"
    assert response.json()["appended_events"] == 2


def test_append_events_multiple_times(base_trace, auth_headers):
    save_trace(base_trace)
    
    first_batch = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {"content": "First"}
            }
        ]
    }
    
    second_batch = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:02:00Z",
                "data": {"content": "Second"}
            }
        ]
    }
    
    client.post("/traces/test-incremental-001/events", json=first_batch, headers=auth_headers)
    client.post("/traces/test-incremental-001/events", json=second_batch, headers=auth_headers)
    
    response = client.get("/traces/test-incremental-001", headers=auth_headers)
    trace_data = response.json()
    
    assert len(trace_data["events"]) == 2
    assert trace_data["events"][0]["data"]["content"] == "First"
    assert trace_data["events"][1]["data"]["content"] == "Second"


def test_append_events_maintains_chronological_order(base_trace, auth_headers):
    save_trace(base_trace)
    
    # First batch with timestamp at 10:00
    first_batch = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:00:00Z",
                "data": {"content": "Middle"}
            }
        ]
    }
    client.post("/traces/test-incremental-001/events", json=first_batch, headers=auth_headers)
    
    # Second batch with earlier and later timestamps
    second_batch = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T09:59:00Z",
                "data": {"content": "Earlier"}
            },
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {"content": "Later"}
            }
        ]
    }
    client.post("/traces/test-incremental-001/events", json=second_batch, headers=auth_headers)
    
    response = client.get("/traces/test-incremental-001", headers=auth_headers)
    events = response.json()["events"]
    
    assert len(events) == 3
    assert events[0]["data"]["content"] == "Earlier"
    assert events[1]["data"]["content"] == "Middle"
    assert events[2]["data"]["content"] == "Later"


def test_append_to_nonexistent_trace(auth_headers):
    new_events = {
        "events": [
            {
                "event_type": "reasoning_step",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {"content": "Test"}
            }
        ]
    }
    
    response = client.post("/traces/does-not-exist/events", json=new_events, headers=auth_headers)
    assert response.status_code == 404


def test_append_empty_events_list(base_trace, auth_headers):
    save_trace(base_trace)
    
    response = client.post("/traces/test-incremental-001/events", json={"events": []}, headers=auth_headers)
    assert response.status_code == 400


def test_append_invalid_event_type(base_trace, auth_headers):
    save_trace(base_trace)
    
    invalid_events = {
        "events": [
            {
                "event_type": "invalid_type",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {}
            }
        ]
    }
    
    response = client.post("/traces/test-incremental-001/events", json=invalid_events, headers=auth_headers)
    assert response.status_code == 400


def test_append_mixed_event_types(base_trace, auth_headers):
    save_trace(base_trace)
    
    mixed_events = {
        "events": [
            {
                "event_type": "file_open",
                "timestamp": "2025-11-27T10:01:00Z",
                "data": {"file_path": "test.py"}
            },
            {
                "event_type": "code_edit",
                "timestamp": "2025-11-27T10:02:00Z",
                "data": {
                    "file_path": "test.py",
                    "diff": "@@ -1,1 +1,2 @@\n+new line"
                }
            },
            {
                "event_type": "terminal_command",
                "timestamp": "2025-11-27T10:03:00Z",
                "data": {
                    "command": "pytest",
                    "exit_code": 0,
                    "output": "OK",
                    "duration_ms": 100
                }
            }
        ]
    }
    
    response = client.post("/traces/test-incremental-001/events", json=mixed_events, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["appended_events"] == 3
    
    trace_response = client.get("/traces/test-incremental-001", headers=auth_headers)
    events = trace_response.json()["events"]
    assert len(events) == 3
    assert events[0]["event_type"] == "file_open"
    assert events[1]["event_type"] == "code_edit"
    assert events[2]["event_type"] == "terminal_command"