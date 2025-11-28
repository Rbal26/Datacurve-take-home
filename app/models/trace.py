from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .events import Event
from .qa_results import QAResults


class RepoInfo(BaseModel):
    name: str
    url: str
    branch: str
    commit_before: str
    commit_after: str
    test_command: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "example-project",
                "url": "https://github.com/org/example-project",
                "branch": "bugfix/login-error",
                "commit_before": "a1b2c3d",
                "commit_after": "d4e5f6a",
                "test_command": "pytest"
            }
        }


class Trace(BaseModel):
    schema_version: str = "1.0"
    trace_id: Optional[str] = None
    developer_id: str
    bug_id: Optional[str] = None
    repo: RepoInfo
    start_time: datetime
    end_time: Optional[datetime] = None
    events: list[Event] = []
    qa_results: Optional[QAResults] = None

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1.0",
                "trace_id": "abcd-1234-efgh-5678",
                "developer_id": "anon-dev-42",
                "bug_id": "BUG-123",
                "repo": {
                    "name": "example-project",
                    "url": "https://github.com/org/example",
                    "branch": "bugfix/login",
                    "commit_before": "a1b2c3d",
                    "commit_after": "d4e5f6a",
                    "test_command": "pytest"
                },
                "start_time": "2025-11-27T15:00:00Z",
                "end_time": "2025-11-27T15:30:00Z",
                "events": [],
                "qa_results": None
            }
        }