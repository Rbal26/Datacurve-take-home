import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
from main import app
from app.storage import save_trace
from app.models import Trace, RepoInfo, ReasoningStepEvent, ReasoningStepEventData

client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    data_dir = Path("data")
    for file in data_dir.glob("test-*.json"):
        file.unlink()


@pytest.fixture
def trace_with_reasoning():
    return Trace(
        trace_id="test-finalize-001",
        developer_id="dev-test",
        repo=RepoInfo(
            name="sample-repo",
            url="https://github.com/test/repo",
            branch="main",
            commit_before="abc",
            commit_after="def",
            test_command="pytest"
        ),
        start_time=datetime.now(),
        events=[
            ReasoningStepEvent(
                event_type="reasoning_step",
                timestamp=datetime.now(),
                data=ReasoningStepEventData(content="I think the bug is in login.py")
            ),
            ReasoningStepEvent(
                event_type="reasoning_step",
                timestamp=datetime.now(),
                data=ReasoningStepEventData(content="Added null check")
            )
        ]
    )


def test_finalize_endpoint_success(trace_with_reasoning):
    save_trace(trace_with_reasoning)
    
    with patch('app.qa.llm_judge.client') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"score": 4.0, "feedback": "Good reasoning"}'
        mock_client.chat.completions.create.return_value = mock_response
        
        response = client.post("/traces/test-finalize-001/finalize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["qa_results"] is not None
        assert data["qa_results"]["tests_passed"] is True
        assert data["qa_results"]["reasoning_score"] == 4.0


def test_finalize_nonexistent_trace():
    response = client.post("/traces/does-not-exist/finalize")
    assert response.status_code == 404


def test_finalize_without_reasoning_steps():
    trace = Trace(
        trace_id="test-finalize-002",
        developer_id="dev-test",
        repo=RepoInfo(
            name="sample-repo",
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
    
    response = client.post("/traces/test-finalize-002/finalize")
    
    assert response.status_code == 200
    data = response.json()
    assert data["qa_results"]["tests_passed"] is True
    assert data["qa_results"]["reasoning_score"] is None