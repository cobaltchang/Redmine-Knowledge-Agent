"""Configuration management for Redmine Knowledge Agent.

This module handles loading and validating configuration from environment
variables, following security best practices for sensitive data handling.
"""

import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from redmine_knowledge_agent.exceptions import ConfigurationError


class RedmineConfig(BaseModel):
    """Configuration for connecting to Redmine server.
    
    This class is immutable (frozen) to prevent accidental modification
    of configuration values at runtime.
    
    Attributes:
        url: The Redmine server URL (must be HTTP or HTTPS).
        api_key: The API key for authentication.
    """
    
    model_config = {"frozen": True}
    
    url: HttpUrl
    api_key: Annotated[str, Field(min_length=20, max_length=100)]
    
    @field_validator("api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate that API key contains only valid characters.
        
        Args:
            v: The API key to validate.
            
        Returns:
            The validated API key.
            
        Raises:
            ValueError: If the API key contains invalid characters.
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "API key must contain only alphanumeric characters, "
                "underscores, and hyphens"
            )
        return v
    
    def __repr__(self) -> str:
        """Return a safe representation without exposing the API key."""
        return f"RedmineConfig(url={self.url!r}, api_key='***')"
    
    def __str__(self) -> str:
        """Return a safe string representation without exposing the API key."""
        return f"RedmineConfig(url={self.url}, api_key=***)"


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Settings are loaded from environment variables and .env file.
    Sensitive values are never exposed in repr or logs.
    
    Attributes:
        redmine_url: The Redmine server URL.
        redmine_api_key: The API key for authentication.
        output_dir: Directory for output files.
        request_timeout: HTTP request timeout in seconds.
        batch_size: Number of items per batch request.
        request_interval_ms: Minimum interval between requests in milliseconds.
        log_level: Logging level.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Required settings
    redmine_url: HttpUrl
    redmine_api_key: Annotated[str, Field(min_length=20, max_length=100)]
    
    # Optional settings with defaults
    output_dir: str = "./output"
    attachment_dir: str = "./attachments"
    request_timeout: int = Field(default=30, ge=1, le=300)
    batch_size: int = Field(default=25, ge=1, le=100)
    request_interval_ms: int = Field(default=100, ge=0, le=10000)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_file: str | None = None
    
    @field_validator("redmine_api_key")
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate that API key contains only valid characters."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "API key must contain only alphanumeric characters, "
                "underscores, and hyphens"
            )
        return v
    
    @model_validator(mode="before")
    @classmethod
    def check_required_fields(cls, values: dict) -> dict:
        """Ensure required fields are present.
        
        Raises:
            ConfigurationError: If required fields are missing.
        """
        # Check for None values from env vars
        if not values.get("redmine_url"):
            raise ConfigurationError("REDMINE_URL environment variable is required")
        if not values.get("redmine_api_key"):
            raise ConfigurationError("REDMINE_API_KEY environment variable is required")
        return values
    
    def create_redmine_config(self) -> RedmineConfig:
        """Create a RedmineConfig instance from settings.
        
        Returns:
            A RedmineConfig instance with URL and API key.
        """
        return RedmineConfig(
            url=self.redmine_url,
            api_key=self.redmine_api_key,
        )
    
    def __repr__(self) -> str:
        """Return a safe representation without exposing sensitive data."""
        return (
            f"Settings(redmine_url={self.redmine_url!r}, "
            f"output_dir={self.output_dir!r}, "
            f"log_level={self.log_level!r})"
        )
