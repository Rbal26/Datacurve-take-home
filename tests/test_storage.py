import pytest
from pathlib import Path
from datetime import datetime
from app.storage import save_trace, load_trace, trace_exists
from app.models import Trace, RepoInfo


@pytest.fixture
def sample_trace():
    return Trace(
        trace_id="test-storage-001",
        developer_id="dev-test",
        repo=RepoInfo(
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_before="abc",
            commit_after="def",
            test_command="pytest"
        ),
        start_time=datetime.now()
    )


@pytest.fixture(autouse=True)
def cleanup():
    yield
    data_dir = Path("data")
    for file in data_dir.glob("test-*.json"):
        file.unlink()


def test_save_trace_with_id(sample_trace):
    trace_id = save_trace(sample_trace)
    assert trace_id == "test-storage-001"
    assert trace_exists(trace_id)


def test_save_trace_without_id():
    trace = Trace(
        developer_id="dev-test",
        repo=RepoInfo(
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_before="abc",
            commit_after="def",
            test_command="pytest"
        ),
        start_time=datetime.now()
    )
    trace_id = save_trace(trace)
    assert trace_id is not None
    assert len(trace_id) == 36
    assert trace_exists(trace_id)


def test_load_trace(sample_trace):
    trace_id = save_trace(sample_trace)
    loaded = load_trace(trace_id)
    assert loaded.trace_id == trace_id
    assert loaded.developer_id == "dev-test"


def test_load_nonexistent_trace():
    with pytest.raises(FileNotFoundError):
        load_trace("nonexistent-trace-id")


def test_trace_exists():
    assert not trace_exists("definitely-does-not-exist")


def test_roundtrip_with_events(sample_trace):
    from app.models import ReasoningStepEvent
    
    sample_trace.events = [
        ReasoningStepEvent(
            timestamp=datetime.now(),
            data={"content": "Testing roundtrip"}
        )
    ]
    
    trace_id = save_trace(sample_trace)
    loaded = load_trace(trace_id)
    
    assert len(loaded.events) == 1
    assert loaded.events[0].event_type == "reasoning_step"