import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models import (
    Trace,
    RepoInfo,
    FileOpenEvent,
    CodeEditEvent,
    ReasoningStepEvent,
    QAResults
)


def test_repo_info_valid():
    repo = RepoInfo(
        name="test-repo",
        url="https://github.com/test/repo",
        branch="main",
        commit_before="abc123",
        commit_after="def456",
        test_command="pytest"
    )
    assert repo.name == "test-repo"
    assert repo.test_command == "pytest"


def test_file_open_event_valid():
    event = FileOpenEvent(
        event_type="file_open",
        timestamp=datetime.now(),
        data={"file_path": "src/main.py"}
    )
    assert event.event_type == "file_open"
    assert event.data.file_path == "src/main.py"


def test_code_edit_event_valid():
    event = CodeEditEvent(
        event_type="code_edit",
        timestamp=datetime.now(),
        data={
            "file_path": "src/auth.py",
            "diff": "@@ -1,3 +1,4 @@\n+import logging",
            "snapshot_after": None
        }
    )
    assert event.event_type == "code_edit"
    assert "import logging" in event.data.diff


def test_reasoning_step_event_valid():
    event = ReasoningStepEvent(
        event_type="reasoning_step",
        timestamp=datetime.now(),
        data={"content": "I think the bug is in login.py"}
    )
    assert event.data.content == "I think the bug is in login.py"


def test_qa_results_valid():
    qa = QAResults(
        tests_passed=True,
        test_exit_code=0,
        test_output_snippet="All tests passed",
        reasoning_score=4.5,
        reasoning_feedback="Good reasoning"
    )
    assert qa.tests_passed is True
    assert qa.reasoning_score == 4.5


def test_qa_results_score_validation():
    with pytest.raises(ValidationError):
        QAResults(reasoning_score=6.0)
    
    with pytest.raises(ValidationError):
        QAResults(reasoning_score=0.5)


def test_trace_minimal_valid():
    trace = Trace(
        developer_id="dev-123",
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
    assert trace.schema_version == "1.0"
    assert trace.developer_id == "dev-123"
    assert trace.events == []


def test_trace_with_events():
    trace = Trace(
        developer_id="dev-123",
        repo=RepoInfo(
            name="test-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_before="abc",
            commit_after="def",
            test_command="pytest"
        ),
        start_time=datetime.now(),
        events=[
            FileOpenEvent(
                timestamp=datetime.now(),
                data={"file_path": "test.py"}
            ),
            ReasoningStepEvent(
                timestamp=datetime.now(),
                data={"content": "Testing hypothesis"}
            )
        ]
    )
    assert len(trace.events) == 2
    assert trace.events[0].event_type == "file_open"
    assert trace.events[1].event_type == "reasoning_step"


def test_trace_missing_required_field():
    with pytest.raises(ValidationError):
        Trace(
            repo=RepoInfo(
                name="test",
                url="https://github.com/test",
                branch="main",
                commit_before="a",
                commit_after="b",
                test_command="pytest"
            ),
            start_time=datetime.now()
        )


def test_trace_json_serialization():
    trace = Trace(
        trace_id="test-123",
        developer_id="dev-456",
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
    json_str = trace.model_dump_json()
    assert "test-123" in json_str
    assert "dev-456" in json_str


def test_trace_json_deserialization():
    json_data = {
        "schema_version": "1.0",
        "trace_id": "test-789",
        "developer_id": "dev-999",
        "repo": {
            "name": "test-repo",
            "url": "https://github.com/test/repo",
            "branch": "main",
            "commit_before": "abc",
            "commit_after": "def",
            "test_command": "pytest"
        },
        "start_time": "2025-11-27T15:00:00Z",
        "events": []
    }
    trace = Trace.model_validate(json_data)
    assert trace.trace_id == "test-789"
    assert trace.developer_id == "dev-999"