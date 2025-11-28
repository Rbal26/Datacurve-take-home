from typing import Optional
from pydantic import BaseModel, Field


class QAResults(BaseModel):
    tests_passed: Optional[bool] = None
    test_exit_code: Optional[int] = None
    test_output_snippet: Optional[str] = None
    reasoning_score: Optional[float] = Field(None, ge=1.0, le=5.0)
    reasoning_feedback: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "tests_passed": True,
                "test_exit_code": 0,
                "test_output_snippet": "All tests passed.",
                "reasoning_score": 4.5,
                "reasoning_feedback": "Clear and methodical reasoning."
            }
        }