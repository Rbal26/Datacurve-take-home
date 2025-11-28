import pytest
from pathlib import Path
from app.qa import run_tests_in_docker


def test_run_tests_success():
    result = run_tests_in_docker("sample_repo", "pytest")
    
    assert result["tests_passed"] is True
    assert result["test_exit_code"] == 0
    assert "passed" in result["test_output_snippet"].lower()


def test_run_tests_with_failing_test():
    test_file_path = Path("sample_repo/tests/test_failing.py")
    
    test_file_path.write_text("""
def test_this_will_fail():
    assert 1 == 2
""")
    
    try:
        result = run_tests_in_docker("sample_repo", "pytest tests/test_failing.py")
        
        assert result["tests_passed"] is False
        assert result["test_exit_code"] != 0
        
    finally:
        if test_file_path.exists():
            test_file_path.unlink()


def test_run_tests_nonexistent_repo():
    result = run_tests_in_docker("nonexistent_repo", "pytest")
    
    assert result["tests_passed"] is False
    assert result["test_exit_code"] == -1
    assert "not found" in result["test_output_snippet"].lower()


def test_run_tests_with_specific_file():
    result = run_tests_in_docker("sample_repo", "pytest tests/test_calculator.py::test_add")
    
    assert result["tests_passed"] is True
    assert result["test_exit_code"] == 0


def test_output_truncation():
    result = run_tests_in_docker("sample_repo", "pytest -v")
    
    assert len(result["test_output_snippet"]) <= 2000