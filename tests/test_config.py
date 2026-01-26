"""Tests for configuration module."""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from redmine_knowledge_agent.config import (
    AppConfig,
    EnvSettings,
    LoggingConfig,
    MultimodalLLMConfig,
    OutputConfig,
    ProcessingConfig,
    RedmineConfig,
    StateConfig,
)


class TestRedmineConfig:
    """Tests for RedmineConfig."""
    
    def test_basic_creation(self) -> None:
        """Test basic config creation."""
        config = RedmineConfig(
            url="https://redmine.example.com/",
            api_key="test_key",
        )
        # URL should have trailing slash removed
        assert config.url == "https://redmine.example.com"
        assert config.api_key == "test_key"
    
    def test_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable resolution for api_key."""
        monkeypatch.setenv("TEST_REDMINE_KEY", "secret_from_env")
        
        config = RedmineConfig(
            url="https://redmine.example.com",
            api_key="${TEST_REDMINE_KEY}",
        )
        assert config.api_key == "secret_from_env"
    
    def test_env_var_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test error when env var is not set."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        
        with pytest.raises(ValueError, match="Environment variable"):
            RedmineConfig(
                url="https://redmine.example.com",
                api_key="${NONEXISTENT_VAR}",
            )


class TestOutputConfig:
    """Tests for OutputConfig."""
    
    def test_basic_creation(self) -> None:
        """Test basic output config creation."""
        config = OutputConfig(
            path="./output/test",
            projects=["proj_a", "proj_b"],
        )
        assert config.path == "./output/test"
        assert config.projects == ["proj_a", "proj_b"]
        assert config.include_subprojects is False
    
    def test_include_subprojects(self) -> None:
        """Test include_subprojects option."""
        config = OutputConfig(
            path="./output",
            projects=["proj"],
            include_subprojects=True,
        )
        assert config.include_subprojects is True
    
    def test_get_output_path(self) -> None:
        """Test get_output_path returns Path object."""
        config = OutputConfig(path="./output/test", projects=["proj"])
        path = config.get_output_path()
        assert isinstance(path, Path)
        assert path.is_absolute()


class TestProcessingConfig:
    """Tests for ProcessingConfig."""
    
    def test_defaults(self) -> None:
        """Test default processing config values."""
        config = ProcessingConfig()
        assert config.textile_to_markdown is True
        assert config.ocr_enabled is True
        assert config.ocr_engine == "pytesseract"
        assert config.multimodal_llm.enabled is False
    
    def test_custom_values(self) -> None:
        """Test custom processing config values."""
        config = ProcessingConfig(
            textile_to_markdown=False,
            ocr_enabled=False,
            ocr_engine="easyocr",
        )
        assert config.textile_to_markdown is False
        assert config.ocr_enabled is False
        assert config.ocr_engine == "easyocr"


class TestMultimodalLLMConfig:
    """Tests for MultimodalLLMConfig."""
    
    def test_defaults(self) -> None:
        """Test default values."""
        config = MultimodalLLMConfig()
        assert config.enabled is False
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key is None
    
    def test_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable resolution."""
        monkeypatch.setenv("TEST_LLM_KEY", "llm_secret")
        
        config = MultimodalLLMConfig(
            enabled=True,
            api_key="${TEST_LLM_KEY}",
        )
        assert config.api_key == "llm_secret"
    
    def test_env_var_not_set_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that unset env var returns None."""
        monkeypatch.delenv("NONEXISTENT_VAR", raising=False)
        
        config = MultimodalLLMConfig(api_key="${NONEXISTENT_VAR}")
        assert config.api_key is None


class TestLoggingConfig:
    """Tests for LoggingConfig."""
    
    def test_defaults(self) -> None:
        """Test default logging config."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
    
    def test_custom_values(self) -> None:
        """Test custom logging config."""
        config = LoggingConfig(level="DEBUG", format="console")
        assert config.level == "DEBUG"
        assert config.format == "console"


class TestStateConfig:
    """Tests for StateConfig."""
    
    def test_defaults(self) -> None:
        """Test default state config."""
        config = StateConfig()
        assert config.backend == "sqlite"
        assert config.path == "./.state.db"
    
    def test_get_state_path(self) -> None:
        """Test get_state_path returns Path object."""
        config = StateConfig(path="./custom.db")
        path = config.get_state_path()
        assert isinstance(path, Path)
        assert path.is_absolute()


class TestAppConfig:
    """Tests for AppConfig."""
    
    def test_creation(self, sample_app_config: AppConfig) -> None:
        """Test basic app config creation."""
        assert sample_app_config.redmine.url == "https://redmine.example.com"
        assert len(sample_app_config.outputs) == 1
    
    def test_get_all_projects(self) -> None:
        """Test get_all_projects returns unique sorted projects."""
        config = AppConfig(
            redmine=RedmineConfig(url="https://test.com", api_key="key"),
            outputs=[
                OutputConfig(path="./a", projects=["proj_c", "proj_a"]),
                OutputConfig(path="./b", projects=["proj_b", "proj_a"]),
            ],
        )
        projects = config.get_all_projects()
        assert projects == ["proj_a", "proj_b", "proj_c"]
    
    def test_from_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config from YAML file."""
        monkeypatch.setenv("TEST_API_KEY", "yaml_test_key")
        
        config_data = {
            "redmine": {
                "url": "https://redmine.yaml.test",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": "./output",
                    "projects": ["project_x"],
                    "include_subprojects": True,
                },
            ],
            "logging": {"level": "DEBUG"},
        }
        
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        loaded = AppConfig.from_yaml(config_file)
        
        assert loaded.redmine.url == "https://redmine.yaml.test"
        assert loaded.redmine.api_key == "yaml_test_key"
        assert loaded.outputs[0].include_subprojects is True
        assert loaded.logging.level == "DEBUG"
    
    def test_from_yaml_file_not_found(self, tmp_path: Path) -> None:
        """Test error when YAML file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            AppConfig.from_yaml(tmp_path / "nonexistent.yaml")
    
    def test_outputs_min_length(self) -> None:
        """Test that at least one output is required."""
        with pytest.raises(Exception):  # pydantic ValidationError
            AppConfig(
                redmine=RedmineConfig(url="https://test.com", api_key="key"),
                outputs=[],
            )


class TestEnvSettings:
    """Tests for EnvSettings."""
    
    def test_defaults(self) -> None:
        """Test default env settings."""
        settings = EnvSettings()
        assert settings.url == "http://localhost:3000"
        assert settings.api_key == ""
        assert settings.output_path == "./output"
        assert settings.log_level == "INFO"
    
    def test_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading from environment variables."""
        monkeypatch.setenv("REDMINE_URL", "https://env.redmine.com")
        monkeypatch.setenv("REDMINE_API_KEY", "env_key")
        monkeypatch.setenv("REDMINE_OUTPUT_PATH", "/custom/output")
        monkeypatch.setenv("REDMINE_LOG_LEVEL", "DEBUG")
        
        settings = EnvSettings()
        assert settings.url == "https://env.redmine.com"
        assert settings.api_key == "env_key"
        assert settings.output_path == "/custom/output"
        assert settings.log_level == "DEBUG"


class TestMultimodalLLMConfig:
    """Tests for MultimodalLLMConfig."""
    
    def test_env_var_resolution(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable resolution for api_key."""
        monkeypatch.setenv("MY_LLM_KEY", "secret_key_123")
        
        from redmine_knowledge_agent.config import MultimodalLLMConfig
        config = MultimodalLLMConfig(api_key="${MY_LLM_KEY}")
        
        assert config.api_key == "secret_key_123"
    
    def test_env_var_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable when not set."""
        # Ensure env var doesn't exist
        monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
        
        from redmine_knowledge_agent.config import MultimodalLLMConfig
        config = MultimodalLLMConfig(api_key="${NONEXISTENT_KEY}")
        
        assert config.api_key is None
    
    def test_literal_value(self) -> None:
        """Test literal value (not env var reference)."""
        from redmine_knowledge_agent.config import MultimodalLLMConfig
        config = MultimodalLLMConfig(api_key="literal_key")
        
        assert config.api_key == "literal_key"
