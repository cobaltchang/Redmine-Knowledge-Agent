"""Tests for Redmine client module."""

from typing import Any
import httpx
import pytest
import respx

from redmine_knowledge_agent.client import RedmineClient
from redmine_knowledge_agent.config import RedmineConfig
from redmine_knowledge_agent.exceptions import (
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
)
from redmine_knowledge_agent.models import Issue, IssueList


class TestRedmineClientInit:
    """Tests for RedmineClient initialization."""

    def test_create_client_with_config(self) -> None:
        """Test creating client with RedmineConfig."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)
        assert client._config == config

    def test_client_sets_correct_headers(self) -> None:
        """Test that client sets correct authentication headers."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)
        # Headers should include API key header
        assert "X-Redmine-API-Key" in client._headers
        assert client._headers["X-Redmine-API-Key"] == "test_api_key_12345678901234567890"

    def test_client_sets_user_agent(self) -> None:
        """Test that client sets User-Agent header."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)
        assert "User-Agent" in client._headers
        assert "RedmineKnowledgeAgent" in client._headers["User-Agent"]


class TestRedmineClientGetIssues:
    """Tests for RedmineClient.get_issues method."""

    @respx.mock
    def test_get_issues_success(
        self, sample_issues_list_response: dict[str, Any]
    ) -> None:
        """Test successful retrieval of issues list."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(200, json=sample_issues_list_response)
        )

        result = client.get_issues()
        assert isinstance(result, IssueList)
        assert len(result.issues) == 2

    @respx.mock
    def test_get_issues_with_pagination(self) -> None:
        """Test issues retrieval with pagination parameters."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "issues": [],
                    "total_count": 0,
                    "offset": 25,
                    "limit": 25,
                },
            )
        )

        result = client.get_issues(offset=25, limit=25)
        assert result.offset == 25
        assert result.limit == 25

    @respx.mock
    def test_get_issues_with_project_filter(self) -> None:
        """Test issues retrieval filtered by project."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        route = respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "issues": [],
                    "total_count": 0,
                    "offset": 0,
                    "limit": 25,
                },
            )
        )

        client.get_issues(project_id=1)
        assert route.called
        assert "project_id=1" in str(route.calls[0].request.url)

    @respx.mock
    def test_get_issues_with_status_filter(self) -> None:
        """Test issues retrieval filtered by status."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        route = respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "issues": [],
                    "total_count": 0,
                    "offset": 0,
                    "limit": 25,
                },
            )
        )

        client.get_issues(status_id="open")
        assert route.called
        assert "status_id=open" in str(route.calls[0].request.url)

    @respx.mock
    def test_get_issues_authentication_error(self) -> None:
        """Test handling of authentication error (401)."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="invalid_api_key_12345678901",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(401, text="Unauthorized")
        )

        with pytest.raises(AuthenticationError):
            client.get_issues()

    @respx.mock
    def test_get_issues_connection_error(self) -> None:
        """Test handling of connection error."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues.json").mock(
            side_effect=httpx.ConnectError("Connection refused")
        )

        with pytest.raises(ConnectionError):
            client.get_issues()

    @respx.mock
    def test_get_issues_rate_limit_error(self) -> None:
        """Test handling of rate limit error (429)."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(
                429,
                headers={"Retry-After": "60"},
                text="Too Many Requests",
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.get_issues()
        assert exc_info.value.retry_after == 60


class TestRedmineClientGetIssue:
    """Tests for RedmineClient.get_issue method."""

    @respx.mock
    def test_get_issue_success(self, sample_issue_response: dict[str, Any]) -> None:
        """Test successful retrieval of single issue."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues/1.json").mock(
            return_value=httpx.Response(200, json={"issue": sample_issue_response})
        )

        result = client.get_issue(1)
        assert isinstance(result, Issue)
        assert result.id == 1
        assert result.subject == "Test Issue"

    @respx.mock
    def test_get_issue_not_found(self) -> None:
        """Test handling of not found error (404)."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        respx.get("https://redmine.test.local/issues/999.json").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        with pytest.raises(NotFoundError) as exc_info:
            client.get_issue(999)
        assert "Issue" in str(exc_info.value)
        assert "999" in str(exc_info.value)

    @respx.mock
    def test_get_issue_with_attachments(self) -> None:
        """Test retrieval of issue with attachments included."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        route = respx.get("https://redmine.test.local/issues/1.json").mock(
            return_value=httpx.Response(
                200,
                json={
                    "issue": {
                        "id": 1,
                        "subject": "Test",
                        "description": "Test",
                        "project": {"id": 1, "name": "Test"},
                        "tracker": {"id": 1, "name": "Bug"},
                        "status": {"id": 1, "name": "New"},
                        "priority": {"id": 2, "name": "Normal"},
                        "author": {"id": 1, "name": "Test"},
                        "created_on": "2026-01-26T10:00:00Z",
                        "updated_on": "2026-01-26T10:00:00Z",
                        "attachments": [],
                    }
                },
            )
        )

        client.get_issue(1, include_attachments=True)
        assert route.called
        assert "include=attachments" in str(route.calls[0].request.url)


class TestRedmineClientContextManager:
    """Tests for RedmineClient context manager."""

    def test_client_as_context_manager(self) -> None:
        """Test using client as context manager."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        with RedmineClient(config) as client:
            assert client is not None

    @respx.mock
    def test_client_closes_on_exit(self) -> None:
        """Test that client properly closes HTTP client on exit."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        
        with RedmineClient(config) as client:
            pass
        
        # After context exit, client should be closed
        assert client._http_client.is_closed


class TestRedmineClientSecurity:
    """Tests for security aspects of RedmineClient."""

    def test_api_key_not_in_repr(self) -> None:
        """Test that API key is not exposed in repr."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)
        repr_str = repr(client)
        assert "test_api_key_12345678901234567890" not in repr_str

    def test_api_key_not_in_str(self) -> None:
        """Test that API key is not exposed in str."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)
        str_repr = str(client)
        assert "test_api_key_12345678901234567890" not in str_repr

    @respx.mock
    def test_api_key_sent_in_header_not_url(self) -> None:
        """Test that API key is sent in header, not URL query parameter."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        client = RedmineClient(config)

        route = respx.get("https://redmine.test.local/issues.json").mock(
            return_value=httpx.Response(
                200,
                json={"issues": [], "total_count": 0, "offset": 0, "limit": 25},
            )
        )

        client.get_issues()
        
        # API key should NOT be in URL
        assert "test_api_key_12345678901234567890" not in str(route.calls[0].request.url)
        # API key SHOULD be in headers
        assert route.calls[0].request.headers["X-Redmine-API-Key"] == "test_api_key_12345678901234567890"
