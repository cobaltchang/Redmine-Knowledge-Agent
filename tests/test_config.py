"""Tests for configuration module."""

import os
import pytest

from redmine_knowledge_agent.config import RedmineConfig, Settings
from redmine_knowledge_agent.exceptions import ConfigurationError


class TestRedmineConfig:
    """Tests for RedmineConfig class."""

    def test_valid_config_creation(self, mock_env_vars: dict[str, str]) -> None:
        """Test creating config with valid values."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        assert str(config.url) == "https://redmine.test.local/"
        assert config.api_key == "test_api_key_12345678901234567890"

    def test_url_must_be_https_or_http(self) -> None:
        """Test that URL must be valid HTTP(S) URL."""
        with pytest.raises(ValueError):
            RedmineConfig(
                url="ftp://invalid.local",
                api_key="test_api_key_12345678901234567890",
            )

    def test_api_key_minimum_length(self) -> None:
        """Test that API key must meet minimum length requirement."""
        with pytest.raises(ValueError):
            RedmineConfig(
                url="https://redmine.test.local",
                api_key="short",  # Too short
            )

    def test_api_key_maximum_length(self) -> None:
        """Test that API key must not exceed maximum length."""
        with pytest.raises(ValueError):
            RedmineConfig(
                url="https://redmine.test.local",
                api_key="x" * 101,  # Too long
            )

    def test_api_key_valid_characters(self) -> None:
        """Test that API key only contains valid characters."""
        # Valid characters: alphanumeric, underscore, hyphen
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="valid_api-key_12345678901234",
        )
        assert config.api_key == "valid_api-key_12345678901234"

    def test_api_key_invalid_characters(self) -> None:
        """Test that API key rejects invalid characters."""
        with pytest.raises(ValueError):
            RedmineConfig(
                url="https://redmine.test.local",
                api_key="invalid!@#$%^&*()key123456",
            )

    def test_config_is_immutable(self) -> None:
        """Test that config is frozen (immutable)."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
            config.api_key = "new_key"  # type: ignore

    def test_api_key_not_in_repr(self) -> None:
        """Test that API key is not exposed in repr for security."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        repr_str = repr(config)
        assert "test_api_key_12345678901234567890" not in repr_str

    def test_api_key_masked_in_str(self) -> None:
        """Test that API key is masked in string representation."""
        config = RedmineConfig(
            url="https://redmine.test.local",
            api_key="test_api_key_12345678901234567890",
        )
        str_repr = str(config)
        assert "test_api_key_12345678901234567890" not in str_repr


class TestSettings:
    """Tests for Settings class."""

    def test_load_from_env_vars(self, mock_env_vars: dict[str, str]) -> None:
        """Test loading settings from environment variables."""
        settings = Settings()
        assert str(settings.redmine_url) == "https://redmine.test.local/"
        assert settings.redmine_api_key == "test_api_key_12345678901234567890"

    def test_missing_required_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when required environment variable is missing."""
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)
        with pytest.raises(ConfigurationError):
            Settings()

    def test_default_values(self, mock_env_vars: dict[str, str]) -> None:
        """Test that default values are applied correctly."""
        settings = Settings()
        assert settings.request_timeout == 30
        assert settings.batch_size == 25
        assert settings.request_interval_ms == 100
        assert settings.log_level == "INFO"

    def test_custom_values_from_env(
        self, mock_env_vars: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test loading custom values from environment."""
        monkeypatch.setenv("REQUEST_TIMEOUT", "60")
        monkeypatch.setenv("BATCH_SIZE", "50")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        
        settings = Settings()
        assert settings.request_timeout == 60
        assert settings.batch_size == 50
        assert settings.log_level == "DEBUG"

    def test_create_redmine_config(self, mock_env_vars: dict[str, str]) -> None:
        """Test creating RedmineConfig from Settings."""
        settings = Settings()
        config = settings.create_redmine_config()
        
        assert isinstance(config, RedmineConfig)
        assert str(config.url) == str(settings.redmine_url)
        assert config.api_key == settings.redmine_api_key

    def test_settings_sensitive_data_not_in_repr(
        self, mock_env_vars: dict[str, str]
    ) -> None:
        """Test that sensitive data is not exposed in repr."""
        settings = Settings()
        repr_str = repr(settings)
        assert "test_api_key_12345678901234567890" not in repr_str

    def test_invalid_log_level(
        self, mock_env_vars: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test validation of log level."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID")
        with pytest.raises(ValueError):
            Settings()

    def test_output_dir_default(self, mock_env_vars: dict[str, str]) -> None:
        """Test default output directory."""
        settings = Settings()
        assert settings.output_dir == "./output"

    def test_output_dir_custom(
        self, mock_env_vars: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test custom output directory."""
        monkeypatch.setenv("OUTPUT_DIR", "/custom/output")
        settings = Settings()
        assert settings.output_dir == "/custom/output"
