"""Tests for logging utilities."""

import pytest

from redmine_knowledge_agent.logging import (
    SensitiveDataFilter,
    mask_api_key,
)


class TestSensitiveDataFilter:
    """Tests for SensitiveDataFilter class."""

    def test_filter_api_key_in_string(self) -> None:
        """Test filtering API key from string."""
        text = 'Using api_key="abc123secretkey456"'
        result = SensitiveDataFilter.filter_string(text)
        assert "abc123secretkey456" not in result
        assert "***" in result

    def test_filter_token_in_string(self) -> None:
        """Test filtering token from string."""
        text = "Authorization token=mysecrettoken123"
        result = SensitiveDataFilter.filter_string(text)
        assert "mysecrettoken123" not in result

    def test_filter_password_in_string(self) -> None:
        """Test filtering password from string."""
        text = 'password="supersecret123"'
        result = SensitiveDataFilter.filter_string(text)
        assert "supersecret123" not in result

    def test_filter_redmine_api_key_header(self) -> None:
        """Test filtering X-Redmine-API-Key header."""
        text = "X-Redmine-API-Key: abcdef123456789012345"
        result = SensitiveDataFilter.filter_string(text)
        assert "abcdef123456789012345" not in result

    def test_filter_string_without_sensitive_data(self) -> None:
        """Test that non-sensitive data is preserved."""
        text = "This is a normal log message"
        result = SensitiveDataFilter.filter_string(text)
        assert result == text

    def test_filter_dict_with_api_key(self) -> None:
        """Test filtering dictionary with API key."""
        data = {
            "url": "https://redmine.local",
            "api_key": "supersecretkey123456",
            "method": "GET",
        }
        result = SensitiveDataFilter.filter_dict(data)
        assert result["api_key"] == "***"
        assert result["url"] == "https://redmine.local"
        assert result["method"] == "GET"

    def test_filter_dict_case_insensitive(self) -> None:
        """Test that key matching is case insensitive."""
        data = {
            "API_KEY": "secret123",
            "Token": "token456",
            "PASSWORD": "pass789",
        }
        result = SensitiveDataFilter.filter_dict(data)
        assert result["API_KEY"] == "***"
        assert result["Token"] == "***"
        assert result["PASSWORD"] == "***"

    def test_filter_nested_dict(self) -> None:
        """Test filtering nested dictionary."""
        data = {
            "config": {
                "api_key": "nested_secret",
                "url": "https://example.com",
            },
            "name": "test",
        }
        result = SensitiveDataFilter.filter_dict(data)
        assert result["config"]["api_key"] == "***"
        assert result["config"]["url"] == "https://example.com"

    def test_filter_dict_preserves_non_string_values(self) -> None:
        """Test that non-string values are preserved."""
        data = {
            "count": 42,
            "enabled": True,
            "items": ["a", "b", "c"],
        }
        result = SensitiveDataFilter.filter_dict(data)
        assert result["count"] == 42
        assert result["enabled"] is True
        assert result["items"] == ["a", "b", "c"]


class TestMaskApiKey:
    """Tests for mask_api_key function."""

    def test_mask_normal_key(self) -> None:
        """Test masking a normal length API key."""
        result = mask_api_key("abc123def456ghi789")
        assert result == "ab***89"
        assert "abc123def456ghi789" not in result

    def test_mask_short_key(self) -> None:
        """Test masking a short API key."""
        result = mask_api_key("abc")
        assert result == "****"

    def test_mask_exactly_four_chars(self) -> None:
        """Test masking exactly 4 character key."""
        result = mask_api_key("abcd")
        assert result == "****"

    def test_mask_five_chars(self) -> None:
        """Test masking 5 character key."""
        result = mask_api_key("abcde")
        assert result == "ab***de"

    def test_mask_empty_string(self) -> None:
        """Test masking empty string."""
        result = mask_api_key("")
        assert result == "****"
