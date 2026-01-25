"""Tests for data models."""

from datetime import datetime, timezone
import pytest

from redmine_knowledge_agent.models import (
    Project,
    Tracker,
    Status,
    Priority,
    User,
    Attachment,
    Issue,
    IssueList,
)


class TestProject:
    """Tests for Project model."""

    def test_create_project(self) -> None:
        """Test creating a Project instance."""
        project = Project(id=1, name="Test Project")
        assert project.id == 1
        assert project.name == "Test Project"

    def test_project_from_dict(self) -> None:
        """Test creating Project from dictionary."""
        data = {"id": 1, "name": "Test Project"}
        project = Project.model_validate(data)
        assert project.id == 1
        assert project.name == "Test Project"

    def test_project_id_must_be_positive(self) -> None:
        """Test that project ID must be positive."""
        with pytest.raises(ValueError):
            Project(id=0, name="Test")

    def test_project_name_not_empty(self) -> None:
        """Test that project name cannot be empty."""
        with pytest.raises(ValueError):
            Project(id=1, name="")


class TestTracker:
    """Tests for Tracker model."""

    def test_create_tracker(self) -> None:
        """Test creating a Tracker instance."""
        tracker = Tracker(id=1, name="Bug")
        assert tracker.id == 1
        assert tracker.name == "Bug"


class TestStatus:
    """Tests for Status model."""

    def test_create_status(self) -> None:
        """Test creating a Status instance."""
        status = Status(id=1, name="New")
        assert status.id == 1
        assert status.name == "New"


class TestPriority:
    """Tests for Priority model."""

    def test_create_priority(self) -> None:
        """Test creating a Priority instance."""
        priority = Priority(id=2, name="Normal")
        assert priority.id == 2
        assert priority.name == "Normal"


class TestUser:
    """Tests for User model."""

    def test_create_user(self) -> None:
        """Test creating a User instance."""
        user = User(id=1, name="John Doe")
        assert user.id == 1
        assert user.name == "John Doe"


class TestAttachment:
    """Tests for Attachment model."""

    def test_create_attachment(self) -> None:
        """Test creating an Attachment instance."""
        attachment = Attachment(
            id=1,
            filename="test.pdf",
            filesize=1024,
            content_type="application/pdf",
            content_url="https://redmine.local/attachments/download/1/test.pdf",
            created_on=datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        assert attachment.id == 1
        assert attachment.filename == "test.pdf"
        assert attachment.filesize == 1024
        assert attachment.content_type == "application/pdf"

    def test_attachment_is_image(self) -> None:
        """Test checking if attachment is an image."""
        image = Attachment(
            id=1,
            filename="test.png",
            filesize=1024,
            content_type="image/png",
            content_url="https://redmine.local/attachments/download/1/test.png",
            created_on=datetime.now(tz=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        assert image.is_image is True

        pdf = Attachment(
            id=2,
            filename="test.pdf",
            filesize=1024,
            content_type="application/pdf",
            content_url="https://redmine.local/attachments/download/2/test.pdf",
            created_on=datetime.now(tz=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        assert pdf.is_image is False

    def test_attachment_is_pdf(self) -> None:
        """Test checking if attachment is a PDF."""
        pdf = Attachment(
            id=1,
            filename="test.pdf",
            filesize=1024,
            content_type="application/pdf",
            content_url="https://redmine.local/attachments/download/1/test.pdf",
            created_on=datetime.now(tz=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        assert pdf.is_pdf is True

        image = Attachment(
            id=2,
            filename="test.png",
            filesize=1024,
            content_type="image/png",
            content_url="https://redmine.local/attachments/download/2/test.png",
            created_on=datetime.now(tz=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        assert image.is_pdf is False


class TestIssue:
    """Tests for Issue model."""

    def test_create_issue(self) -> None:
        """Test creating an Issue instance."""
        issue = Issue(
            id=1,
            subject="Test Issue",
            description="Test description",
            project=Project(id=1, name="Test Project"),
            tracker=Tracker(id=1, name="Bug"),
            status=Status(id=1, name="New"),
            priority=Priority(id=2, name="Normal"),
            author=User(id=1, name="Test User"),
            created_on=datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc),
            updated_on=datetime(2026, 1, 26, 10, 0, 0, tzinfo=timezone.utc),
        )
        assert issue.id == 1
        assert issue.subject == "Test Issue"

    def test_issue_with_optional_fields(self) -> None:
        """Test Issue with optional fields."""
        issue = Issue(
            id=1,
            subject="Test Issue",
            description=None,
            project=Project(id=1, name="Test Project"),
            tracker=Tracker(id=1, name="Bug"),
            status=Status(id=1, name="New"),
            priority=Priority(id=2, name="Normal"),
            author=User(id=1, name="Test User"),
            assigned_to=None,
            created_on=datetime.now(tz=timezone.utc),
            updated_on=datetime.now(tz=timezone.utc),
            attachments=[],
        )
        assert issue.description is None
        assert issue.assigned_to is None
        assert issue.attachments == []

    def test_issue_with_attachments(self) -> None:
        """Test Issue with attachments list."""
        attachment = Attachment(
            id=1,
            filename="test.pdf",
            filesize=1024,
            content_type="application/pdf",
            content_url="https://redmine.local/attachments/download/1/test.pdf",
            created_on=datetime.now(tz=timezone.utc),
            author=User(id=1, name="Test User"),
        )
        issue = Issue(
            id=1,
            subject="Test Issue",
            description="Test",
            project=Project(id=1, name="Test Project"),
            tracker=Tracker(id=1, name="Bug"),
            status=Status(id=1, name="New"),
            priority=Priority(id=2, name="Normal"),
            author=User(id=1, name="Test User"),
            created_on=datetime.now(tz=timezone.utc),
            updated_on=datetime.now(tz=timezone.utc),
            attachments=[attachment],
        )
        assert len(issue.attachments) == 1
        assert issue.attachments[0].filename == "test.pdf"

    def test_issue_from_api_response(self, sample_issue_response: dict) -> None:
        """Test creating Issue from API response."""
        issue = Issue.from_api_response(sample_issue_response)
        assert issue.id == 1
        assert issue.subject == "Test Issue"
        assert issue.project.name == "Test Project"
        assert issue.tracker.name == "Bug"

    def test_issue_id_must_be_positive(self) -> None:
        """Test that issue ID must be positive."""
        with pytest.raises(ValueError):
            Issue(
                id=0,
                subject="Test",
                description=None,
                project=Project(id=1, name="Test"),
                tracker=Tracker(id=1, name="Bug"),
                status=Status(id=1, name="New"),
                priority=Priority(id=2, name="Normal"),
                author=User(id=1, name="Test"),
                created_on=datetime.now(tz=timezone.utc),
                updated_on=datetime.now(tz=timezone.utc),
            )

    def test_issue_subject_not_empty(self) -> None:
        """Test that issue subject cannot be empty."""
        with pytest.raises(ValueError):
            Issue(
                id=1,
                subject="",
                description=None,
                project=Project(id=1, name="Test"),
                tracker=Tracker(id=1, name="Bug"),
                status=Status(id=1, name="New"),
                priority=Priority(id=2, name="Normal"),
                author=User(id=1, name="Test"),
                created_on=datetime.now(tz=timezone.utc),
                updated_on=datetime.now(tz=timezone.utc),
            )


class TestIssueList:
    """Tests for IssueList model."""

    def test_create_issue_list(self) -> None:
        """Test creating an IssueList instance."""
        issue_list = IssueList(
            issues=[],
            total_count=0,
            offset=0,
            limit=25,
        )
        assert issue_list.issues == []
        assert issue_list.total_count == 0

    def test_issue_list_from_api_response(
        self, sample_issues_list_response: dict
    ) -> None:
        """Test creating IssueList from API response."""
        issue_list = IssueList.from_api_response(sample_issues_list_response)
        assert len(issue_list.issues) == 2
        assert issue_list.total_count == 2
        assert issue_list.offset == 0
        assert issue_list.limit == 25

    def test_issue_list_has_more(self) -> None:
        """Test has_more property for pagination."""
        # Has more pages
        list_with_more = IssueList(
            issues=[],
            total_count=100,
            offset=0,
            limit=25,
        )
        assert list_with_more.has_more is True

        # Last page
        list_last_page = IssueList(
            issues=[],
            total_count=50,
            offset=25,
            limit=25,
        )
        assert list_last_page.has_more is False

    def test_issue_list_next_offset(self) -> None:
        """Test next_offset property for pagination."""
        issue_list = IssueList(
            issues=[],
            total_count=100,
            offset=0,
            limit=25,
        )
        assert issue_list.next_offset == 25

    def test_issue_list_iteration(self, sample_issues_list_response: dict) -> None:
        """Test that IssueList is iterable."""
        issue_list = IssueList.from_api_response(sample_issues_list_response)
        issues = list(issue_list)
        assert len(issues) == 2

    def test_issue_list_length(self, sample_issues_list_response: dict) -> None:
        """Test len() on IssueList."""
        issue_list = IssueList.from_api_response(sample_issues_list_response)
        assert len(issue_list) == 2
