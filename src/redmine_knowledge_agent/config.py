"""Configuration management for Redmine Knowledge Agent.

Supports YAML config with multiple output directories and per-project settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml  # type: ignore
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedmineConfig(BaseModel):
    """Redmine server configuration."""

    url: str = Field(..., description="Redmine server URL")
    api_key: str = Field(..., description="API key for authentication")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL doesn't have trailing slash."""
        return v.rstrip("/")

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env_var(cls, v: str) -> str:
        """Resolve environment variable references like ${VAR_NAME}."""
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            resolved = os.environ.get(env_var)
            if not resolved:
                msg = f"Environment variable {env_var} is not set"
                raise ValueError(msg)
            return resolved
        return v


class OutputConfig(BaseModel):
    """Configuration for a single output directory."""

    path: str = Field(..., description="Output directory path")
    projects: list[str] = Field(..., description="List of project identifiers to fetch")
    include_subprojects: bool = Field(
        default=False, description="Whether to include issues from subprojects",
    )

    def get_output_path(self) -> Path:
        """Get the output path as a Path object."""
        return Path(self.path).expanduser().resolve()


class MultimodalLLMConfig(BaseModel):
    """Configuration for multimodal LLM processing."""

    enabled: bool = Field(default=False)
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-4o")
    api_key: str | None = Field(default=None)

    @field_validator("api_key", mode="before")
    @classmethod
    def resolve_env_var(cls, v: str | None) -> str | None:
        """Resolve environment variable references."""
        if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            return os.environ.get(env_var)
        return v


class ProcessingConfig(BaseModel):
    """Configuration for content processing."""

    textile_to_markdown: bool = Field(default=True)
    ocr_enabled: bool = Field(default=True)
    ocr_engine: Literal["pytesseract", "easyocr", "multimodal_llm"] = Field(default="pytesseract")
    multimodal_llm: MultimodalLLMConfig = Field(default_factory=MultimodalLLMConfig)


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    format: Literal["json", "console"] = Field(default="json")


class StateConfig(BaseModel):
    """Configuration for state persistence."""

    backend: Literal["sqlite", "json"] = Field(default="sqlite")
    path: str = Field(default="./.state.db")

    def get_state_path(self) -> Path:
        """Get the state file path as a Path object."""
        return Path(self.path).expanduser().resolve()


class AppConfig(BaseModel):
    """Main application configuration."""

    redmine: RedmineConfig
    outputs: list[OutputConfig] = Field(..., min_length=1)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    state: StateConfig = Field(default_factory=StateConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> AppConfig:
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file.

        Returns:
            Loaded AppConfig instance.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            yaml.YAMLError: If the YAML is invalid.
            ValidationError: If the config doesn't match the schema.

        """
        config_path = Path(path).expanduser().resolve()
        if not config_path.exists():
            msg = f"Configuration file not found: {config_path}"
            raise FileNotFoundError(msg)

        with config_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    def get_all_projects(self) -> list[str]:
        """Get a flat list of all unique project identifiers."""
        projects: set[str] = set()
        for output in self.outputs:
            projects.update(output.projects)
        return sorted(projects)


class EnvSettings(BaseSettings):
    """Environment-based settings (for simple CLI usage without YAML)."""

    model_config = SettingsConfigDict(
        env_prefix="REDMINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url: str = Field(default="http://localhost:3000")
    api_key: str = Field(default="")
    output_path: str = Field(default="./output")
    log_level: str = Field(default="INFO")
