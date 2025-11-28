import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    os.environ["API_TOKEN"] = "test-token-123"
    os.environ.setdefault("OPENAI_API_KEY", "test-key")

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token-123"}

