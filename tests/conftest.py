"""Test fixtures and configuration for pytest."""

import pytest
from typing import Any


@pytest.fixture
def sample_issue_response() -> dict[str, Any]:
    """Sample Redmine issue response for testing."""
    return {
        "id": 1,
        "project": {"id": 1, "name": "Test Project"},
        "tracker": {"id": 1, "name": "Bug"},
        "status": {"id": 1, "name": "New"},
        "priority": {"id": 2, "name": "Normal"},
        "author": {"id": 1, "name": "Test User"},
        "subject": "Test Issue",
        "description": "This is a test issue description.",
        "created_on": "2026-01-26T10:00:00Z",
        "updated_on": "2026-01-26T10:00:00Z",
        "attachments": [],
    }


@pytest.fixture
def sample_issues_list_response(sample_issue_response: dict[str, Any]) -> dict[str, Any]:
    """Sample Redmine issues list response for testing."""
    return {
        "issues": [
            sample_issue_response,
            {
                **sample_issue_response,
                "id": 2,
                "subject": "Second Test Issue",
            },
        ],
        "total_count": 2,
        "offset": 0,
        "limit": 25,
    }


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Set up mock environment variables for testing."""
    env_vars = {
        "REDMINE_URL": "https://redmine.test.local",
        "REDMINE_API_KEY": "test_api_key_12345678901234567890",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
