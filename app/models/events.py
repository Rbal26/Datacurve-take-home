from datetime import datetime
from typing import Union, Literal, Optional
from pydantic import BaseModel, Field


class FileOpenEventData(BaseModel):
    file_path: str


class FileOpenEvent(BaseModel):
    event_type: Literal["file_open"] = "file_open"
    timestamp: datetime
    data: FileOpenEventData


class FileCloseEventData(BaseModel):
    file_path: str


class FileCloseEvent(BaseModel):
    event_type: Literal["file_close"] = "file_close"
    timestamp: datetime
    data: FileCloseEventData


class CodeEditEventData(BaseModel):
    file_path: str
    diff: str
    snapshot_after: Optional[str] = None


class CodeEditEvent(BaseModel):
    event_type: Literal["code_edit"] = "code_edit"
    timestamp: datetime
    data: CodeEditEventData


class TerminalCommandEventData(BaseModel):
    command: str
    exit_code: int
    output: str
    duration_ms: int


class TerminalCommandEvent(BaseModel):
    event_type: Literal["terminal_command"] = "terminal_command"
    timestamp: datetime
    data: TerminalCommandEventData


class TestResultEventData(BaseModel):
    tests_passed: bool
    test_command: str
    failed_tests: list[str] = []
    summary: str


class TestResultEvent(BaseModel):
    event_type: Literal["test_result"] = "test_result"
    timestamp: datetime
    data: TestResultEventData


class ReasoningStepEventData(BaseModel):
    content: str


class ReasoningStepEvent(BaseModel):
    event_type: Literal["reasoning_step"] = "reasoning_step"
    timestamp: datetime
    data: ReasoningStepEventData


Event = Union[
    FileOpenEvent,
    FileCloseEvent,
    CodeEditEvent,
    TerminalCommandEvent,
    TestResultEvent,
    ReasoningStepEvent
]