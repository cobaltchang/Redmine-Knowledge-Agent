"""Tests for main module."""

import pytest
from unittest.mock import MagicMock, patch

from redmine_knowledge_agent.__main__ import (
    fetch_all_issues,
    print_issues_summary,
    main,
)
from redmine_knowledge_agent.models import (
    Issue,
    IssueList,
    Project,
    Tracker,
    Status,
    Priority,
    User,
)
from redmine_knowledge_agent.exceptions import ConfigurationError, AuthenticationError


class TestFetchAllIssues:
    """Tests for fetch_all_issues function."""

    def test_fetch_single_page(self) -> None:
        """Test fetching issues that fit in a single page."""
        mock_client = MagicMock()
        mock_issue = self._create_mock_issue(1, "Test Issue")
        
        mock_client.get_issues.return_value = IssueList(
            issues=[mock_issue],
            total_count=1,
            offset=0,
            limit=25,
        )
        
        result = fetch_all_issues(mock_client, batch_size=25)
        
        assert len(result) == 1
        assert result[0].id == 1
        mock_client.get_issues.assert_called_once()

    def test_fetch_multiple_pages(self) -> None:
        """Test fetching issues across multiple pages."""
        mock_client = MagicMock()
        
        # First page
        first_page = IssueList(
            issues=[self._create_mock_issue(1, "Issue 1")],
            total_count=2,
            offset=0,
            limit=1,
        )
        # Second page
        second_page = IssueList(
            issues=[self._create_mock_issue(2, "Issue 2")],
            total_count=2,
            offset=1,
            limit=1,
        )
        
        mock_client.get_issues.side_effect = [first_page, second_page]
        
        result = fetch_all_issues(mock_client, batch_size=1)
        
        assert len(result) == 2
        assert mock_client.get_issues.call_count == 2

    def test_fetch_with_project_filter(self) -> None:
        """Test fetching issues with project filter."""
        mock_client = MagicMock()
        mock_client.get_issues.return_value = IssueList(
            issues=[],
            total_count=0,
            offset=0,
            limit=25,
        )
        
        fetch_all_issues(mock_client, project_id=123)
        
        mock_client.get_issues.assert_called_with(
            project_id=123,
            status_id="open",
            offset=0,
            limit=25,
        )

    def test_fetch_empty_result(self) -> None:
        """Test fetching when no issues exist."""
        mock_client = MagicMock()
        mock_client.get_issues.return_value = IssueList(
            issues=[],
            total_count=0,
            offset=0,
            limit=25,
        )
        
        result = fetch_all_issues(mock_client)
        
        assert len(result) == 0

    @staticmethod
    def _create_mock_issue(issue_id: int, subject: str) -> Issue:
        """Create a mock Issue for testing."""
        from datetime import datetime, timezone
        return Issue(
            id=issue_id,
            subject=subject,
            description=None,
            project=Project(id=1, name="Test Project"),
            tracker=Tracker(id=1, name="Bug"),
            status=Status(id=1, name="New"),
            priority=Priority(id=2, name="Normal"),
            author=User(id=1, name="Test User"),
            created_on=datetime.now(tz=timezone.utc),
            updated_on=datetime.now(tz=timezone.utc),
        )


class TestPrintIssuesSummary:
    """Tests for print_issues_summary function."""

    def test_print_empty_list(self, capsys: pytest.CaptureFixture) -> None:
        """Test printing empty issues list."""
        print_issues_summary([])
        
        captured = capsys.readouterr()
        assert "0 個 Issues" in captured.out

    def test_print_issues_with_data(self, capsys: pytest.CaptureFixture) -> None:
        """Test printing issues with data."""
        from datetime import datetime, timezone
        
        issue = Issue(
            id=1,
            subject="Test Issue Subject",
            description="Description",
            project=Project(id=1, name="My Project"),
            tracker=Tracker(id=1, name="Bug"),
            status=Status(id=1, name="Open"),
            priority=Priority(id=2, name="High"),
            author=User(id=1, name="John Doe"),
            assigned_to=User(id=2, name="Jane Doe"),
            created_on=datetime.now(tz=timezone.utc),
            updated_on=datetime.now(tz=timezone.utc),
        )
        
        print_issues_summary([issue])
        
        captured = capsys.readouterr()
        assert "#1: Test Issue Subject" in captured.out
        assert "My Project" in captured.out
        assert "John Doe" in captured.out
        assert "Jane Doe" in captured.out


class TestMain:
    """Tests for main function."""

    @patch("redmine_knowledge_agent.__main__.Settings")
    def test_main_configuration_error(self, mock_settings: MagicMock) -> None:
        """Test main handles configuration error."""
        mock_settings.side_effect = ConfigurationError("Missing REDMINE_URL")
        
        exit_code = main()
        
        assert exit_code == 1

    @patch("redmine_knowledge_agent.__main__.Settings")
    @patch("redmine_knowledge_agent.__main__.RedmineClient")
    def test_main_authentication_error(
        self,
        mock_client_class: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """Test main handles authentication error."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.redmine_url = "https://redmine.test"
        mock_settings_instance.request_timeout = 30
        mock_settings_instance.batch_size = 25
        mock_settings.return_value = mock_settings_instance
        
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_issues.side_effect = AuthenticationError()
        mock_client_class.return_value = mock_client
        
        exit_code = main()
        
        assert exit_code == 1

    @patch("redmine_knowledge_agent.__main__.Settings")
    @patch("redmine_knowledge_agent.__main__.RedmineClient")
    def test_main_success(
        self,
        mock_client_class: MagicMock,
        mock_settings: MagicMock,
    ) -> None:
        """Test main runs successfully."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.redmine_url = "https://redmine.test"
        mock_settings_instance.request_timeout = 30
        mock_settings_instance.batch_size = 25
        mock_settings.return_value = mock_settings_instance
        
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.get_issues.return_value = IssueList(
            issues=[],
            total_count=0,
            offset=0,
            limit=25,
        )
        mock_client_class.return_value = mock_client
        
        exit_code = main()
        
        assert exit_code == 0
