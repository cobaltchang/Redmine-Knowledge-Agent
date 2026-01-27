"""Tests for Redmine client."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from redmine_knowledge_agent.client import RedmineClient
from redmine_knowledge_agent.config import RedmineConfig


class TestRedmineClient:
    """Tests for RedmineClient."""

    @pytest.fixture
    def config(self) -> RedmineConfig:
        """Create a test config."""
        return RedmineConfig(
            url="https://redmine.test.com",
            api_key="test_api_key",
        )

    @pytest.fixture
    def mock_redmine(self) -> MagicMock:
        """Create a mock Redmine instance."""
        return MagicMock()

    @pytest.fixture
    def client(self, config: RedmineConfig, mock_redmine: MagicMock) -> RedmineClient:
        """Create a RedmineClient with mock."""
        return RedmineClient(config, redmine_instance=mock_redmine)

    def test_redmine_property_creates_instance(self, config: RedmineConfig) -> None:
        """Test that redmine property creates instance when needed."""
        client = RedmineClient(config)

        with patch("redmine_knowledge_agent.client.Redmine") as mock_redmine_class:
            mock_instance = MagicMock()
            mock_redmine_class.return_value = mock_instance

            result = client.redmine

            mock_redmine_class.assert_called_once_with(
                "https://redmine.test.com",
                key="test_api_key",
            )
            assert result is mock_instance

    def test_list_projects(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test listing projects."""
        # Setup mock projects
        proj1 = MagicMock()
        proj1.id = 1
        proj1.identifier = "project_a"
        proj1.name = "Project A"
        proj1.description = "Description A"

        proj2 = MagicMock()
        proj2.id = 2
        proj2.identifier = "project_b"
        proj2.name = "Project B"
        proj2.description = ""

        mock_redmine.project.all.return_value = [proj1, proj2]

        projects = client.list_projects()

        assert len(projects) == 2
        assert projects[0]["identifier"] == "project_a"
        assert projects[0]["name"] == "Project A"
        assert projects[1]["identifier"] == "project_b"

    def test_list_projects_error(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test list_projects handles errors."""
        mock_redmine.project.all.side_effect = RuntimeError("Connection failed")

        with pytest.raises(RuntimeError, match="Connection failed"):
            client.list_projects()

    def test_get_project_issues(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_issue: MagicMock,
    ) -> None:
        """Test fetching project issues."""
        # Setup mock
        mock_redmine.issue.filter.return_value = [mock_redmine_issue]
        mock_redmine.issue.get.return_value = mock_redmine_issue

        issues = list(client.get_project_issues("test_project"))

        assert len(issues) == 1
        assert issues[0].id == 12345
        assert issues[0].project == "mock_project"

    def test_get_project_issues_with_updated_after(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_issue: MagicMock,
    ) -> None:
        """Test filtering issues by updated_after."""
        # Issue updated before filter
        mock_redmine_issue.updated_on = datetime(2024, 1, 1, tzinfo=UTC)
        mock_redmine.issue.filter.return_value = [mock_redmine_issue]

        issues = list(
            client.get_project_issues(
                "test_project",
                updated_after=datetime(2024, 1, 15, tzinfo=UTC),
            ),
        )

        assert len(issues) == 0

    def test_get_project_issues_error_on_single_issue(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test handling error when fetching individual issue."""
        mock_issue = MagicMock()
        mock_issue.id = 1
        mock_issue.updated_on = datetime(2024, 1, 20, tzinfo=UTC)

        mock_redmine.issue.filter.return_value = [mock_issue]
        mock_redmine.issue.get.side_effect = ValueError("Access denied")

        # Should skip the problematic issue and continue
        issues = list(client.get_project_issues("test_project"))
        assert len(issues) == 0

    def test_get_issue(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_issue: MagicMock,
    ) -> None:
        """Test fetching a single issue."""
        mock_redmine.issue.get.return_value = mock_redmine_issue

        issue = client.get_issue(12345)

        assert issue.id == 12345
        mock_redmine.issue.get.assert_called_once_with(
            12345,
            include=["attachments", "journals"],
        )

    def test_get_issue_error(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test get_issue error handling."""
        mock_redmine.issue.get.side_effect = RuntimeError("Not found")

        with pytest.raises(RuntimeError, match="Not found"):
            client.get_issue(99999)

    def test_get_project_wiki_pages(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_wiki_page: MagicMock,
    ) -> None:
        """Test fetching wiki pages."""
        page_info = MagicMock()
        page_info.title = "MockWikiPage"

        mock_redmine.wiki_page.filter.return_value = [page_info]
        mock_redmine.wiki_page.get.return_value = mock_redmine_wiki_page

        pages = list(client.get_project_wiki_pages("test_project"))

        assert len(pages) == 1
        assert pages[0].title == "MockWikiPage"

    def test_get_project_wiki_pages_no_wiki(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test handling project without wiki."""
        mock_redmine.wiki_page.filter.side_effect = RuntimeError("Wiki not enabled")

        # Should not raise - wiki errors are handled gracefully (empty list)
        pages = list(client.get_project_wiki_pages("test_project"))
        assert len(pages) == 0

    def test_get_wiki_page(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_wiki_page: MagicMock,
    ) -> None:
        """Test fetching a single wiki page."""
        mock_redmine.wiki_page.get.return_value = mock_redmine_wiki_page

        page = client.get_wiki_page("test_project", "MockWikiPage")

        assert page.title == "MockWikiPage"

    def test_get_wiki_page_error(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test get_wiki_page error handling."""
        mock_redmine.wiki_page.get.side_effect = RuntimeError("Not found")

        with pytest.raises(RuntimeError, match="Not found"):
            client.get_wiki_page("test_project", "NonExistent")

    @patch("redmine_knowledge_agent.client.requests")
    def test_download_attachment(
        self,
        mock_requests: MagicMock,
        client: RedmineClient,
        tmp_path: Path,
    ) -> None:
        """Test downloading an attachment."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"file", b"data"]
        mock_requests.get.return_value = mock_response

        output_path = tmp_path / "subdir" / "file.txt"

        result = client.download_attachment(
            "https://redmine.test.com/attachments/download/1/file.txt",
            output_path,
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.read_bytes() == b"filedata"

        # Check headers
        mock_requests.get.assert_called_once()
        call_kwargs = mock_requests.get.call_args[1]
        assert call_kwargs["headers"]["X-Redmine-API-Key"] == "test_api_key"

    @patch("redmine_knowledge_agent.client.requests.get")
    def test_download_attachment_error(
        self,
        mock_get: MagicMock,
        client: RedmineClient,
        tmp_path: Path,
    ) -> None:
        """Test download_attachment error handling."""
        mock_get.side_effect = requests.RequestException("Network error")

        with pytest.raises(requests.RequestException, match="Network error"):
            client.download_attachment(
                "https://redmine.test.com/attachments/download/1/file.txt",
                tmp_path / "file.txt",
            )

    def test_get_project_issues_with_subprojects(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
        mock_redmine_issue: MagicMock,
    ) -> None:
        """Test fetching issues including subprojects."""
        mock_redmine.issue.filter.return_value = [mock_redmine_issue]
        mock_redmine.issue.get.return_value = mock_redmine_issue

        list(client.get_project_issues("test_project", include_subprojects=True))

        # Verify subproject parameter is set
        call_kwargs = mock_redmine.issue.filter.call_args[1]
        assert "subproject_id" in call_kwargs

    def test_get_project_issues_raises_on_filter_error(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test get_project_issues raises on filter error."""
        mock_redmine.issue.filter.side_effect = RuntimeError("API Error")

        with pytest.raises(RuntimeError, match="API Error"):
            list(client.get_project_issues("test_project"))

    def test_get_wiki_page_error_handling_in_iteration(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test wiki page iteration continues on individual page errors."""
        page1 = MagicMock()
        page1.title = "Page1"
        page2 = MagicMock()
        page2.title = "Page2"

        mock_redmine.wiki_page.filter.return_value = [page1, page2]

        # First page fails, second succeeds
        mock_wiki = MagicMock()
        mock_wiki.title = "Page2"
        mock_wiki.text = "Content"
        mock_wiki.version = 1
        mock_wiki.created_on = MagicMock()
        mock_wiki.updated_on = MagicMock()

        def get_wiki_side_effect(title: str, **_kwargs: object) -> MagicMock:
            msg = "Page not accessible"
            if title == "Page1":
                raise ValueError(msg)
            return mock_wiki

        mock_redmine.wiki_page.get.side_effect = get_wiki_side_effect

        # Patch the from_redmine_wiki method
        with patch(
            "redmine_knowledge_agent.client.WikiPageMetadata.from_redmine_wiki",
        ) as mock_from:
            mock_from.return_value = MagicMock()
            pages = list(client.get_project_wiki_pages("test_project"))

        # Should have 1 page (Page2)
        assert len(pages) == 1

    def test_get_project_issues_updated_after_no_attribute(
        self,
        client: RedmineClient,
        mock_redmine: MagicMock,
    ) -> None:
        """Test issues without updated_on attribute are processed."""
        # Create a mock issue without updated_on using spec to restrict attributes
        mock_issue = MagicMock(spec=["id"])  # Only has 'id' attribute
        mock_issue.id = 1

        mock_redmine.issue.filter.return_value = [mock_issue]

        # Full issue has updated_on
        full_issue = MagicMock()
        full_issue.id = 1
        full_issue.project = MagicMock()
        full_issue.project.identifier = "test"
        full_issue.tracker = MagicMock()
        full_issue.tracker.name = "Bug"
        full_issue.status = MagicMock()
        full_issue.status.name = "Open"
        full_issue.priority = MagicMock()
        full_issue.priority.name = "Normal"
        full_issue.subject = "Test"
        full_issue.description = ""
        full_issue.created_on = datetime(2024, 1, 1, tzinfo=UTC)
        full_issue.updated_on = datetime(2024, 1, 20, tzinfo=UTC)
        full_issue.attachments = []
        full_issue.journals = []

        mock_redmine.issue.get.return_value = full_issue

        # Even with updated_after filter, issues without updated_on should still be fetched
        issues = list(
            client.get_project_issues(
                "test_project",
                updated_after=datetime(2024, 1, 15, tzinfo=UTC),
            ),
        )

        # Should be fetched because hasattr(mock_issue, 'updated_on') is False
        assert len(issues) == 1
