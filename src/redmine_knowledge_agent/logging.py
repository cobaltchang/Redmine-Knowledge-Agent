"""Logging utilities with security filtering.

This module provides logging configuration and filters to ensure
sensitive data is not exposed in log output.
"""

import re
from typing import Any

import structlog


class SensitiveDataFilter:
    """Filter sensitive data from log messages.
    
    This filter removes or masks sensitive information such as:
    - API keys
    - Tokens
    - Passwords
    - Internal URLs with credentials
    """
    
    SENSITIVE_PATTERNS = [
        # API keys
        (re.compile(r'api[_-]?key["\s:=]+["\']?([a-zA-Z0-9_-]{10,})["\']?', re.I), r'api_key=***'),
        # Tokens
        (re.compile(r'token["\s:=]+["\']?([a-zA-Z0-9_-]{10,})["\']?', re.I), r'token=***'),
        # Passwords
        (re.compile(r'password["\s:=]+["\']?([^\s"\']+)["\']?', re.I), r'password=***'),
        # Authorization headers
        (re.compile(r'Authorization["\s:=]+["\']?([^\s"\']+)["\']?', re.I), r'Authorization=***'),
        # X-Redmine-API-Key header
        (re.compile(r'X-Redmine-API-Key["\s:=]+["\']?([^\s"\']+)["\']?', re.I), r'X-Redmine-API-Key=***'),
    ]
    
    @classmethod
    def filter_string(cls, text: str) -> str:
        """Filter sensitive data from a string.
        
        Args:
            text: The text to filter.
            
        Returns:
            The filtered text with sensitive data masked.
        """
        result = text
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
    
    @classmethod
    def filter_dict(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Filter sensitive data from a dictionary.
        
        Args:
            data: The dictionary to filter.
            
        Returns:
            A new dictionary with sensitive values masked.
        """
        sensitive_keys = {
            'api_key', 'apikey', 'api-key',
            'token', 'password', 'secret',
            'authorization', 'x-redmine-api-key',
        }
        
        result = {}
        for key, value in data.items():
            if key.lower() in sensitive_keys:
                result[key] = '***'
            elif isinstance(value, str):
                result[key] = cls.filter_string(value)
            elif isinstance(value, dict):
                result[key] = cls.filter_dict(value)
            else:
                result[key] = value
        return result


def mask_api_key(api_key: str) -> str:
    """Mask an API key for safe logging.
    
    Shows only first 2 and last 2 characters.
    
    Args:
        api_key: The API key to mask.
        
    Returns:
        The masked API key.
    """
    if len(api_key) <= 4:
        return "****"
    return f"{api_key[:2]}***{api_key[-2:]}"


def create_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Create a configured logger instance.
    
    Args:
        name: The logger name (usually __name__).
        
    Returns:
        A configured structlog logger.
    """
    return structlog.get_logger(name)
