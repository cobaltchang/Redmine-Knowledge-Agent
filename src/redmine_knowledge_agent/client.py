"""Redmine API client module.

This module provides a client for interacting with the Redmine REST API.
It handles authentication, request management, and error handling.

Security considerations:
- API key is sent via header, never in URL
- Sensitive data is not logged or exposed in errors
- TLS certificate verification is enabled by default
"""

from typing import Any, Optional, Self

import httpx

from redmine_knowledge_agent import __version__
from redmine_knowledge_agent.config import RedmineConfig
from redmine_knowledge_agent.exceptions import (
    AuthenticationError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
)
from redmine_knowledge_agent.models import Issue, IssueList


class RedmineClient:
    """Client for interacting with Redmine REST API.
    
    This client provides methods for fetching issues and their attachments
    from a Redmine server. It handles authentication, pagination, and
    error handling.
    
    The client can be used as a context manager to ensure proper cleanup:
    
        with RedmineClient(config) as client:
            issues = client.get_issues()
    
    Attributes:
        _config: The Redmine configuration.
        _headers: HTTP headers including authentication.
        _http_client: The underlying HTTP client.
    """
    
    def __init__(
        self,
        config: RedmineConfig,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Redmine client.
        
        Args:
            config: The Redmine configuration with URL and API key.
            timeout: Request timeout in seconds.
        """
        self._config = config
        self._headers = {
            "X-Redmine-API-Key": config.api_key,
            "User-Agent": f"RedmineKnowledgeAgent/{__version__}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._http_client = httpx.Client(
            base_url=str(config.url),
            headers=self._headers,
            timeout=httpx.Timeout(timeout),
            verify=True,  # Always verify TLS certificates
            follow_redirects=False,  # Don't follow redirects for security
        )
    
    def __enter__(self) -> Self:
        """Enter context manager."""
        return self
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit context manager and close HTTP client."""
        self.close()
    
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._http_client.close()
    
    def __repr__(self) -> str:
        """Return a safe representation without exposing the API key."""
        return f"RedmineClient(url={self._config.url!r})"
    
    def __str__(self) -> str:
        """Return a safe string representation."""
        return f"RedmineClient connected to {self._config.url}"
    
    def _handle_response_error(
        self,
        response: httpx.Response,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
    ) -> None:
        """Handle HTTP error responses.
        
        Args:
            response: The HTTP response to check.
            resource_type: Type of resource being accessed (for 404 errors).
            resource_id: ID of resource being accessed (for 404 errors).
            
        Raises:
            AuthenticationError: For 401 responses.
            NotFoundError: For 404 responses.
            RateLimitError: For 429 responses.
        """
        if response.status_code == 401:
            raise AuthenticationError()
        
        if response.status_code == 404:
            raise NotFoundError(
                resource_type=resource_type,
                resource_id=resource_id,
            )
        
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                retry_after=int(retry_after) if retry_after else None
            )
        
        # For other errors, raise generic HTTP error
        response.raise_for_status()
    
    def get_issues(
        self,
        project_id: Optional[int] = None,
        status_id: Optional[str | int] = None,
        tracker_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 25,
    ) -> IssueList:
        """Fetch a list of issues from Redmine.
        
        Args:
            project_id: Filter by project ID.
            status_id: Filter by status ID or special value ("open", "closed", "*").
            tracker_id: Filter by tracker ID.
            offset: Pagination offset (0-based).
            limit: Maximum number of issues to return.
            
        Returns:
            An IssueList containing the matching issues.
            
        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to server fails.
            RateLimitError: If rate limit is exceeded.
        """
        params: dict[str, Any] = {
            "offset": offset,
            "limit": limit,
        }
        
        if project_id is not None:
            params["project_id"] = project_id
        if status_id is not None:
            params["status_id"] = status_id
        if tracker_id is not None:
            params["tracker_id"] = tracker_id
        
        try:
            response = self._http_client.get("/issues.json", params=params)
        except httpx.ConnectError as e:
            raise ConnectionError() from e
        
        self._handle_response_error(response)
        
        return IssueList.from_api_response(response.json())
    
    def get_issue(
        self,
        issue_id: int,
        include_attachments: bool = False,
        include_journals: bool = False,
    ) -> Issue:
        """Fetch a single issue by ID.
        
        Args:
            issue_id: The ID of the issue to fetch.
            include_attachments: Whether to include attachments in the response.
            include_journals: Whether to include journals (comments) in the response.
            
        Returns:
            The Issue with the specified ID.
            
        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to server fails.
            NotFoundError: If the issue does not exist.
            RateLimitError: If rate limit is exceeded.
        """
        params: dict[str, Any] = {}
        
        includes = []
        if include_attachments:
            includes.append("attachments")
        if include_journals:
            includes.append("journals")
        
        if includes:
            params["include"] = ",".join(includes)
        
        try:
            response = self._http_client.get(
                f"/issues/{issue_id}.json",
                params=params,
            )
        except httpx.ConnectError as e:
            raise ConnectionError() from e
        
        self._handle_response_error(
            response,
            resource_type="Issue",
            resource_id=issue_id,
        )
        
        data = response.json()
        return Issue.from_api_response(data["issue"])
