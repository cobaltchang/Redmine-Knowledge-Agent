"""Tests for exceptions module."""

import pytest

from redmine_knowledge_agent.exceptions import (
    RedmineKnowledgeAgentError,
    ConfigurationError,
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ParseError,
)


class TestRedmineKnowledgeAgentError:
    """Tests for base exception class."""

    def test_base_exception_with_message(self) -> None:
        """Test that base exception can be created with a message."""
        error = RedmineKnowledgeAgentError("Test error message")
        assert str(error) == "Test error message"
        assert error.error_code == "RKA-000"

    def test_base_exception_with_code(self) -> None:
        """Test that base exception stores error code."""
        error = RedmineKnowledgeAgentError("Test error", error_code="RKA-999")
        assert error.error_code == "RKA-999"

    def test_base_exception_is_exception(self) -> None:
        """Test that base exception inherits from Exception."""
        error = RedmineKnowledgeAgentError("Test")
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error_default_message(self) -> None:
        """Test ConfigurationError with default message."""
        error = ConfigurationError()
        assert "Configuration error" in str(error)
        assert error.error_code == "RKA-007"

    def test_configuration_error_custom_message(self) -> None:
        """Test ConfigurationError with custom message."""
        error = ConfigurationError("Missing REDMINE_URL")
        assert "Missing REDMINE_URL" in str(error)

    def test_configuration_error_inheritance(self) -> None:
        """Test that ConfigurationError inherits from base error."""
        error = ConfigurationError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_authentication_error_default_message(self) -> None:
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert "Authentication failed" in str(error)
        assert error.error_code == "RKA-002"

    def test_authentication_error_no_sensitive_data(self) -> None:
        """Test that AuthenticationError does not expose sensitive data."""
        error = AuthenticationError()
        error_str = str(error)
        # Should not contain any API key hints
        assert "key" not in error_str.lower() or "api" not in error_str.lower()

    def test_authentication_error_inheritance(self) -> None:
        """Test that AuthenticationError inherits from base error."""
        error = AuthenticationError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestConnectionError:
    """Tests for ConnectionError."""

    def test_connection_error_default_message(self) -> None:
        """Test ConnectionError with default message."""
        error = ConnectionError()
        assert "Cannot connect" in str(error)
        assert error.error_code == "RKA-001"

    def test_connection_error_no_url_exposed(self) -> None:
        """Test that ConnectionError does not expose internal URLs."""
        error = ConnectionError()
        error_str = str(error)
        # Should not contain IP addresses or specific URLs
        assert "192.168" not in error_str
        assert "localhost" not in error_str

    def test_connection_error_inheritance(self) -> None:
        """Test that ConnectionError inherits from base error."""
        error = ConnectionError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_not_found_error_default_message(self) -> None:
        """Test NotFoundError with default message."""
        error = NotFoundError()
        assert "not found" in str(error).lower()
        assert error.error_code == "RKA-003"

    def test_not_found_error_with_resource(self) -> None:
        """Test NotFoundError with resource identifier."""
        error = NotFoundError(resource_type="Issue", resource_id=123)
        assert "Issue" in str(error)
        assert "123" in str(error)

    def test_not_found_error_inheritance(self) -> None:
        """Test that NotFoundError inherits from base error."""
        error = NotFoundError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_rate_limit_error_default_message(self) -> None:
        """Test RateLimitError with default message."""
        error = RateLimitError()
        assert "rate limit" in str(error).lower() or "too many" in str(error).lower()
        assert error.error_code == "RKA-004"

    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test RateLimitError with retry_after value."""
        error = RateLimitError(retry_after=60)
        assert error.retry_after == 60

    def test_rate_limit_error_inheritance(self) -> None:
        """Test that RateLimitError inherits from base error."""
        error = RateLimitError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestParseError:
    """Tests for ParseError."""

    def test_parse_error_default_message(self) -> None:
        """Test ParseError with default message."""
        error = ParseError()
        assert "parse" in str(error).lower() or "parsing" in str(error).lower()
        assert error.error_code == "RKA-005"

    def test_parse_error_with_details(self) -> None:
        """Test ParseError with parsing details."""
        error = ParseError(content_type="JSON", details="Invalid syntax")
        assert "JSON" in str(error)

    def test_parse_error_inheritance(self) -> None:
        """Test that ParseError inherits from base error."""
        error = ParseError()
        assert isinstance(error, RedmineKnowledgeAgentError)


class TestExceptionRaising:
    """Tests for raising exceptions in different contexts."""

    def test_raise_and_catch_authentication_error(self) -> None:
        """Test raising and catching AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError()
        assert exc_info.value.error_code == "RKA-002"

    def test_raise_and_catch_as_base_error(self) -> None:
        """Test that specific errors can be caught as base error."""
        with pytest.raises(RedmineKnowledgeAgentError):
            raise ConnectionError()

    def test_exception_chaining(self) -> None:
        """Test exception chaining preserves original cause."""
        original = ValueError("Original error")
        with pytest.raises(ParseError) as exc_info:
            try:
                raise original
            except ValueError as e:
                raise ParseError(content_type="JSON") from e
        assert exc_info.value.__cause__ is original
