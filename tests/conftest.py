"""Pytest configuration and fixtures."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from redmine_knowledge_agent.config import (
    AppConfig,
    LoggingConfig,
    OutputConfig,
    ProcessingConfig,
    RedmineConfig,
    StateConfig,
)
from redmine_knowledge_agent.models import (
    AttachmentInfo,
    ExtractedContent,
    IssueMetadata,
    JournalEntry,
    ProcessingMethod,
    WikiPageMetadata,
)


@pytest.fixture
def sample_redmine_config() -> RedmineConfig:
    """Create a sample Redmine config."""
    return RedmineConfig(
        url="https://redmine.example.com",
        api_key="test_api_key_12345",
    )


@pytest.fixture
def sample_output_config() -> OutputConfig:
    """Create a sample output config."""
    return OutputConfig(
        path="./output/test",
        projects=["project_a", "project_b"],
        include_subprojects=False,
    )


@pytest.fixture
def sample_app_config(
    sample_redmine_config: RedmineConfig,
    sample_output_config: OutputConfig,
) -> AppConfig:
    """Create a sample app config."""
    return AppConfig(
        redmine=sample_redmine_config,
        outputs=[sample_output_config],
        processing=ProcessingConfig(),
        logging=LoggingConfig(),
        state=StateConfig(),
    )


@pytest.fixture
def sample_attachment() -> AttachmentInfo:
    """Create a sample attachment."""
    return AttachmentInfo(
        id=1,
        filename="test_image.png",
        content_type="image/png",
        filesize=1024,
        content_url="https://redmine.example.com/attachments/download/1/test_image.png",
        description="Test image attachment",
    )


@pytest.fixture
def sample_journal() -> JournalEntry:
    """Create a sample journal entry."""
    return JournalEntry(
        id=1,
        user="Test User",
        notes="This is a test comment with *bold* text.",
        created_on=datetime(2024, 1, 15, 10, 30),
        details=[],
    )


@pytest.fixture
def sample_issue(
    sample_attachment: AttachmentInfo,
    sample_journal: JournalEntry,
) -> IssueMetadata:
    """Create a sample issue."""
    return IssueMetadata(
        id=12345,
        project="test_project",
        tracker="Bug",
        status="In Progress",
        priority="High",
        subject="Test Issue Subject",
        description_textile="h2. Description\n\nThis is a *test* issue with _formatting_.",
        created_on=datetime(2024, 1, 10, 9, 0),
        updated_on=datetime(2024, 1, 20, 14, 30),
        target_version="v2.0.0",
        assigned_to="Test User",
        author="Author Name",
        done_ratio=50,
        attachments=[sample_attachment],
        journals=[sample_journal],
    )


@pytest.fixture
def sample_wiki_page(sample_attachment: AttachmentInfo) -> WikiPageMetadata:
    """Create a sample wiki page."""
    return WikiPageMetadata(
        title="TestWikiPage",
        project="test_project",
        version=3,
        created_on=datetime(2024, 1, 1, 8, 0),
        updated_on=datetime(2024, 1, 25, 16, 45),
        text_textile="h1. Wiki Page Title\n\nThis is the wiki content.",
        author="Wiki Author",
        attachments=[sample_attachment],
    )


@pytest.fixture
def sample_extracted_content() -> ExtractedContent:
    """Create a sample extracted content."""
    return ExtractedContent(
        text="This is extracted text from an image or PDF.",
        metadata={"filename": "test.png", "size": 1024},
        processing_method=ProcessingMethod.OCR,
    )


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.fixture
def mock_redmine_issue() -> MagicMock:
    """Create a mock Redmine issue object."""
    issue = MagicMock()
    issue.id = 12345
    issue.subject = "Mock Issue Subject"
    issue.description = "h2. Mock Description\n\nTest content."
    issue.created_on = datetime(2024, 1, 10, 9, 0)
    issue.updated_on = datetime(2024, 1, 20, 14, 30)
    issue.done_ratio = 25
    issue.estimated_hours = 8.0
    issue.spent_hours = 4.0
    
    # Project
    issue.project = MagicMock()
    issue.project.identifier = "mock_project"
    
    # Tracker, Status, Priority
    issue.tracker = MagicMock()
    issue.tracker.name = "Feature"
    issue.status = MagicMock()
    issue.status.name = "New"
    issue.priority = MagicMock()
    issue.priority.name = "Normal"
    
    # Optional fields
    issue.fixed_version = MagicMock()
    issue.fixed_version.name = "v1.0.0"
    issue.assigned_to = MagicMock()
    issue.assigned_to.name = "Assigned User"
    issue.author = MagicMock()
    issue.author.name = "Author User"
    
    # Attachments
    att = MagicMock()
    att.id = 1
    att.filename = "mock_file.pdf"
    att.content_type = "application/pdf"
    att.filesize = 2048
    att.content_url = "https://redmine.example.com/attachments/download/1/mock_file.pdf"
    att.description = "Mock attachment"
    issue.attachments = [att]
    
    # Journals
    journal = MagicMock()
    journal.id = 1
    journal.user = MagicMock()
    journal.user.name = "Commenter"
    journal.notes = "This is a journal note."
    journal.created_on = datetime(2024, 1, 15, 12, 0)
    journal.details = []
    issue.journals = [journal]
    
    # Custom fields
    cf = MagicMock()
    cf.name = "Custom Field"
    cf.value = "Custom Value"
    issue.custom_fields = [cf]
    
    # Parent
    issue.parent = MagicMock()
    issue.parent.id = 12344
    
    return issue


@pytest.fixture
def mock_redmine_wiki_page() -> MagicMock:
    """Create a mock Redmine wiki page object."""
    page = MagicMock()
    page.title = "MockWikiPage"
    page.text = "h1. Mock Wiki\n\nThis is mock wiki content."
    page.version = 2
    page.created_on = datetime(2024, 1, 5, 10, 0)
    page.updated_on = datetime(2024, 1, 22, 11, 30)
    
    page.author = MagicMock()
    page.author.name = "Wiki Author"
    page.comments = "Updated content"
    
    page.parent = MagicMock()
    page.parent.title = "ParentPage"
    
    # Attachments
    att = MagicMock()
    att.id = 2
    att.filename = "wiki_image.png"
    att.content_type = "image/png"
    att.filesize = 512
    att.content_url = "https://redmine.example.com/attachments/download/2/wiki_image.png"
    att.description = ""
    page.attachments = [att]
    
    return page
