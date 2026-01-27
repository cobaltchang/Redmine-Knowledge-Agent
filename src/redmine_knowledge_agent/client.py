"""Redmine client using python-redmine.

Provides high-level interface for fetching Issues and Wiki pages.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import requests  # type: ignore
import structlog
from redminelib import Redmine  # type: ignore

from .config import RedmineConfig
from .models import IssueMetadata, WikiPageMetadata

logger = structlog.get_logger(__name__)


class RedmineClient:
    """Client for interacting with Redmine API."""

    def __init__(
        self,
        config: RedmineConfig,
        redmine_instance: Redmine | None = None,
    ) -> None:
        """Initialize the Redmine client.

        Args:
            config: Redmine configuration.
            redmine_instance: Optional pre-configured Redmine instance (for testing).

        """
        self.config = config
        self._redmine = redmine_instance

    @property
    def redmine(self) -> Redmine:
        """Get or create the Redmine instance."""
        if self._redmine is None:
            self._redmine = Redmine(
                self.config.url,
                key=self.config.api_key,
            )
        return self._redmine

    def list_projects(self) -> list[dict[str, Any]]:
        """List all accessible projects.

        Returns:
            List of project info dicts with id, identifier, name.

        """
        projects: list[dict[str, Any]] = []
        try:
            projects.extend(
                {
                    "id": project.id,
                    "identifier": project.identifier,
                    "name": project.name,
                    "description": getattr(project, "description", ""),
                }
                for project in self.redmine.project.all()
            )
        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.exception("Failed to list projects", error=str(e))
            raise

        return projects

    def get_project_issues(
        self,
        project_id: str,
        include_subprojects: bool = False,
        updated_after: datetime | None = None,
        status: str = "*",  # all statuses
    ) -> Iterator[IssueMetadata]:
        """Fetch issues for a project.

        Args:
            project_id: Project identifier.
            include_subprojects: Whether to include issues from subprojects.
            updated_after: Only fetch issues updated after this time.
            status: Status filter (* for all, open, closed, or specific status).

        Yields:
            IssueMetadata for each issue.

        """
        logger.info(
            "Fetching issues",
            project=project_id,
            include_subprojects=include_subprojects,
            updated_after=updated_after,
        )

        try:
            # Build query parameters
            params = {
                "project_id": project_id,
                "status_id": status,
                "sort": "updated_on:desc",
                "include": ["attachments", "journals"],
            }

            if include_subprojects:
                params["subproject_id"] = "!*"  # Include all subprojects

            # Fetch issues
            issues = self.redmine.issue.filter(**params)

            for issue in issues:  # pragma: no branch
                # Check updated_after filter
                if (
                    updated_after
                    and hasattr(issue, "updated_on")
                    and issue.updated_on <= updated_after
                ):  # pragma: no branch
                    continue

                try:
                    # Refresh to get full details including journals
                    full_issue = self.redmine.issue.get(
                        issue.id,
                        include=["attachments", "journals"],
                    )
                    yield IssueMetadata.from_redmine_issue(full_issue)
                except (ConnectionError, TimeoutError, ValueError) as e:
                    logger.warning(
                        "Failed to fetch issue details",
                        issue_id=issue.id,
                        error=str(e),
                    )
                    continue

        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.exception(
                "Failed to fetch project issues",
                project=project_id,
                error=str(e),
            )
            raise

    def get_issue(self, issue_id: int) -> IssueMetadata:
        """Fetch a single issue by ID.

        Args:
            issue_id: Issue ID.

        Returns:
            IssueMetadata for the issue.

        """
        try:
            issue = self.redmine.issue.get(
                issue_id,
                include=["attachments", "journals"],
            )
            return IssueMetadata.from_redmine_issue(issue)
        except Exception as e:
            logger.exception("Failed to fetch issue", issue_id=issue_id, error=str(e))
            raise

    def get_project_wiki_pages(
        self,
        project_id: str,
    ) -> Iterator[WikiPageMetadata]:
        """Fetch wiki pages for a project.

        Args:
            project_id: Project identifier.

        Yields:
            WikiPageMetadata for each wiki page.

        """
        logger.info("Fetching wiki pages", project=project_id)

        try:
            # Get wiki page list (index)
            wiki_pages = self.redmine.wiki_page.filter(project_id=project_id)

            for page_info in wiki_pages:
                try:
                    # Fetch full page content
                    full_page = self.redmine.wiki_page.get(
                        page_info.title,
                        project_id=project_id,
                        include=["attachments"],
                    )
                    yield WikiPageMetadata.from_redmine_wiki(full_page, project_id)
                except (ConnectionError, TimeoutError, ValueError) as e:
                    logger.warning(
                        "Failed to fetch wiki page",
                        project=project_id,
                        page=page_info.title,
                        error=str(e),
                    )
                    continue

        except (ConnectionError, TimeoutError, RuntimeError) as e:
            logger.exception(
                "Failed to fetch wiki pages",
                project=project_id,
                error=str(e),
            )
            # Wiki might not be enabled for project, don't raise
            return

    def get_wiki_page(self, project_id: str, page_title: str) -> WikiPageMetadata:
        """Fetch a single wiki page.

        Args:
            project_id: Project identifier.
            page_title: Wiki page title.

        Returns:
            WikiPageMetadata for the page.

        """
        try:
            page = self.redmine.wiki_page.get(
                page_title,
                project_id=project_id,
                include=["attachments"],
            )
            return WikiPageMetadata.from_redmine_wiki(page, project_id)
        except Exception as e:
            logger.exception(
                "Failed to fetch wiki page",
                project=project_id,
                page=page_title,
                error=str(e),
            )
            raise

    def download_attachment(
        self,
        content_url: str,
        output_path: Path,
    ) -> Path:
        """Download an attachment to a file.

        Args:
            content_url: URL to download from.
            output_path: Path to save the file.

        Returns:
            Path to the downloaded file.

        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Use the API key for authentication
            response = requests.get(
                content_url,
                headers={"X-Redmine-API-Key": self.config.api_key},
                stream=True,
                timeout=10,
            )
            response.raise_for_status()

            with output_path.open("wb") as f:
                f.writelines(response.iter_content(chunk_size=8192))

            logger.debug("Downloaded attachment", url=content_url, path=str(output_path))

        except (OSError, requests.RequestException) as e:
            logger.exception(
                "Failed to download attachment",
                url=content_url,
                error=str(e),
            )
            raise

        return output_path
