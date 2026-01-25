"""Exception classes for Redmine Knowledge Agent.

This module defines custom exceptions used throughout the application.
All exceptions follow security best practices:
- No sensitive data in error messages
- No internal URLs or IP addresses exposed
- Consistent error codes for logging and debugging
"""

from typing import Optional


class RedmineKnowledgeAgentError(Exception):
    """Base exception class for Redmine Knowledge Agent.
    
    All custom exceptions inherit from this class.
    
    Attributes:
        error_code: A unique error code for this exception type.
    """
    
    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str = "RKA-000",
    ) -> None:
        """Initialize the exception.
        
        Args:
            message: Human-readable error message (must not contain sensitive data).
            error_code: Unique error code for this error type.
        """
        self.error_code = error_code
        super().__init__(message)


class ConfigurationError(RedmineKnowledgeAgentError):
    """Raised when there is a configuration error.
    
    Examples:
        - Missing required environment variables
        - Invalid configuration values
        - Configuration file not found
    """
    
    def __init__(self, message: str = "Configuration error occurred") -> None:
        """Initialize ConfigurationError.
        
        Args:
            message: Description of the configuration error.
        """
        super().__init__(message=message, error_code="RKA-007")


class AuthenticationError(RedmineKnowledgeAgentError):
    """Raised when authentication fails.
    
    This exception intentionally does not include any information
    about the API key or credentials to prevent information leakage.
    """
    
    def __init__(self) -> None:
        """Initialize AuthenticationError with a safe message."""
        super().__init__(
            message="Authentication failed. Please verify your credentials.",
            error_code="RKA-002",
        )


class ConnectionError(RedmineKnowledgeAgentError):
    """Raised when connection to Redmine server fails.
    
    This exception intentionally does not include the server URL
    or IP address to prevent information leakage.
    """
    
    def __init__(self) -> None:
        """Initialize ConnectionError with a safe message."""
        super().__init__(
            message="Cannot connect to Redmine server. Please check your network connection.",
            error_code="RKA-001",
        )


class NotFoundError(RedmineKnowledgeAgentError):
    """Raised when a requested resource is not found.
    
    Attributes:
        resource_type: Type of resource that was not found.
        resource_id: ID of the resource that was not found.
    """
    
    def __init__(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
    ) -> None:
        """Initialize NotFoundError.
        
        Args:
            resource_type: Type of resource (e.g., "Issue", "Project").
            resource_id: ID of the resource.
        """
        if resource_type and resource_id:
            message = f"{resource_type} with ID {resource_id} was not found."
        else:
            message = "The requested resource was not found."
        
        super().__init__(message=message, error_code="RKA-003")


class RateLimitError(RedmineKnowledgeAgentError):
    """Raised when API rate limit is exceeded.
    
    Attributes:
        retry_after: Number of seconds to wait before retrying.
    """
    
    def __init__(self, retry_after: Optional[int] = None) -> None:
        """Initialize RateLimitError.
        
        Args:
            retry_after: Seconds to wait before retrying (from Retry-After header).
        """
        self.retry_after = retry_after
        
        if retry_after:
            message = f"Rate limit exceeded. Please retry after {retry_after} seconds."
        else:
            message = "Rate limit exceeded. Please try again later."
        
        super().__init__(message=message, error_code="RKA-004")


class ParseError(RedmineKnowledgeAgentError):
    """Raised when content parsing fails.
    
    This can occur when:
    - JSON response is malformed
    - PDF parsing fails
    - OCR processing fails
    
    Attributes:
        content_type: Type of content that failed to parse.
        details: Additional details about the parse failure.
    """
    
    def __init__(
        self,
        content_type: Optional[str] = None,
        details: Optional[str] = None,
    ) -> None:
        """Initialize ParseError.
        
        Args:
            content_type: Type of content (e.g., "JSON", "PDF", "Image").
            details: Additional error details.
        """
        self.content_type = content_type
        self.details = details
        
        if content_type:
            message = f"Failed to parse {content_type} content."
        else:
            message = "Content parsing failed."
        
        super().__init__(message=message, error_code="RKA-005")
