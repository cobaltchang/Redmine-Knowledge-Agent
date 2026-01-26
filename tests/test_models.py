"""Tests for data models."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from redmine_knowledge_agent.models import (
    AttachmentInfo,
    ExtractedContent,
    IssueMetadata,
    JournalEntry,
    ProcessingMethod,
    ProcessingState,
    WikiPageMetadata,
)


class TestAttachmentInfo:
    """Tests for AttachmentInfo."""
    
    def test_is_image(self) -> None:
        """Test is_image property."""
        png = AttachmentInfo(
            id=1, filename="test.png", content_type="image/png",
            filesize=100, content_url="http://test/1",
        )
        assert png.is_image is True
        
        pdf = AttachmentInfo(
            id=2, filename="test.pdf", content_type="application/pdf",
            filesize=100, content_url="http://test/2",
        )
        assert pdf.is_image is False
    
    def test_is_pdf(self) -> None:
        """Test is_pdf property."""
        pdf = AttachmentInfo(
            id=1, filename="test.pdf", content_type="application/pdf",
            filesize=100, content_url="http://test/1",
        )
        assert pdf.is_pdf is True
        
        png = AttachmentInfo(
            id=2, filename="test.png", content_type="image/png",
            filesize=100, content_url="http://test/2",
        )
        assert png.is_pdf is False
    
    def test_is_docx(self) -> None:
        """Test is_docx property."""
        docx = AttachmentInfo(
            id=1, filename="test.docx",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filesize=100, content_url="http://test/1",
        )
        assert docx.is_docx is True
        
        doc = AttachmentInfo(
            id=2, filename="test.doc", content_type="application/msword",
            filesize=100, content_url="http://test/2",
        )
        assert doc.is_docx is True
        
        pdf = AttachmentInfo(
            id=3, filename="test.pdf", content_type="application/pdf",
            filesize=100, content_url="http://test/3",
        )
        assert pdf.is_docx is False
    
    def test_is_spreadsheet(self) -> None:
        """Test is_spreadsheet property."""
        xlsx = AttachmentInfo(
            id=1, filename="test.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filesize=100, content_url="http://test/1",
        )
        assert xlsx.is_spreadsheet is True
        
        csv = AttachmentInfo(
            id=2, filename="test.csv", content_type="text/csv",
            filesize=100, content_url="http://test/2",
        )
        assert csv.is_spreadsheet is True
        
        pdf = AttachmentInfo(
            id=3, filename="test.pdf", content_type="application/pdf",
            filesize=100, content_url="http://test/3",
        )
        assert pdf.is_spreadsheet is False


class TestExtractedContent:
    """Tests for ExtractedContent."""
    
    def test_is_successful_with_text(self) -> None:
        """Test is_successful returns True when text exists."""
        content = ExtractedContent(
            text="Extracted text",
            processing_method=ProcessingMethod.OCR,
        )
        assert content.is_successful is True
    
    def test_is_successful_with_error(self) -> None:
        """Test is_successful returns False when error exists."""
        content = ExtractedContent(
            text="",
            processing_method=ProcessingMethod.FALLBACK,
            error="Processing failed",
        )
        assert content.is_successful is False
    
    def test_is_successful_empty_text(self) -> None:
        """Test is_successful returns False with empty text."""
        content = ExtractedContent(
            text="   ",  # whitespace only
            processing_method=ProcessingMethod.TEXT_EXTRACT,
        )
        assert content.is_successful is False
    
    def test_processing_method_enum(self) -> None:
        """Test ProcessingMethod enum values."""
        assert ProcessingMethod.OCR.value == "ocr"
        assert ProcessingMethod.TEXT_EXTRACT.value == "text_extract"
        assert ProcessingMethod.LLM.value == "llm"
        assert ProcessingMethod.FALLBACK.value == "fallback"


class TestJournalEntry:
    """Tests for JournalEntry."""
    
    def test_creation(self) -> None:
        """Test basic journal entry creation."""
        journal = JournalEntry(
            id=1,
            user="Test User",
            notes="Test notes",
            created_on=datetime(2024, 1, 15),
        )
        assert journal.id == 1
        assert journal.user == "Test User"
        assert journal.notes == "Test notes"
        assert journal.details == []


class TestIssueMetadata:
    """Tests for IssueMetadata."""
    
    def test_from_redmine_issue(self, mock_redmine_issue: MagicMock) -> None:
        """Test creating IssueMetadata from Redmine issue."""
        metadata = IssueMetadata.from_redmine_issue(mock_redmine_issue)
        
        assert metadata.id == 12345
        assert metadata.project == "mock_project"
        assert metadata.tracker == "Feature"
        assert metadata.status == "New"
        assert metadata.priority == "Normal"
        assert metadata.subject == "Mock Issue Subject"
        assert metadata.target_version == "v1.0.0"
        assert metadata.assigned_to == "Assigned User"
        assert metadata.author == "Author User"
        assert metadata.done_ratio == 25
        assert metadata.estimated_hours == 8.0
        assert metadata.spent_hours == 4.0
        assert metadata.parent_id == 12344
        assert len(metadata.attachments) == 1
        assert len(metadata.journals) == 1
        assert "Custom Field" in metadata.custom_fields
    
    def test_from_redmine_issue_minimal(self) -> None:
        """Test creating IssueMetadata with minimal fields."""
        issue = MagicMock()
        issue.id = 1
        issue.subject = "Minimal Issue"
        issue.description = ""
        issue.created_on = datetime(2024, 1, 1)
        issue.updated_on = datetime(2024, 1, 2)
        issue.done_ratio = 0
        
        issue.project = MagicMock()
        issue.project.identifier = "proj"
        issue.tracker = MagicMock()
        issue.tracker.name = "Bug"
        issue.status = MagicMock()
        issue.status.name = "Open"
        issue.priority = MagicMock()
        issue.priority.name = "Low"
        
        # No optional fields
        del issue.fixed_version
        del issue.assigned_to
        del issue.author
        del issue.attachments
        del issue.journals
        del issue.custom_fields
        del issue.parent
        del issue.estimated_hours
        del issue.spent_hours
        
        metadata = IssueMetadata.from_redmine_issue(issue)
        
        assert metadata.id == 1
        assert metadata.target_version is None
        assert metadata.assigned_to is None
        assert metadata.author is None
        assert metadata.attachments == []
        assert metadata.journals == []
        assert metadata.custom_fields == {}
        assert metadata.parent_id is None


class TestWikiPageMetadata:
    """Tests for WikiPageMetadata."""
    
    def test_from_redmine_wiki(self, mock_redmine_wiki_page: MagicMock) -> None:
        """Test creating WikiPageMetadata from Redmine wiki page."""
        metadata = WikiPageMetadata.from_redmine_wiki(
            mock_redmine_wiki_page,
            "test_project",
        )
        
        assert metadata.title == "MockWikiPage"
        assert metadata.project == "test_project"
        assert metadata.version == 2
        assert metadata.author == "Wiki Author"
        assert metadata.comments == "Updated content"
        assert metadata.parent_title == "ParentPage"
        assert len(metadata.attachments) == 1
    
    def test_from_redmine_wiki_minimal(self) -> None:
        """Test creating WikiPageMetadata with minimal fields."""
        page = MagicMock()
        page.title = "MinimalPage"
        page.text = "Content"
        page.version = 1
        page.created_on = datetime(2024, 1, 1)
        page.updated_on = datetime(2024, 1, 2)
        
        del page.author
        del page.comments
        del page.parent
        del page.attachments
        
        metadata = WikiPageMetadata.from_redmine_wiki(page, "proj")
        
        assert metadata.title == "MinimalPage"
        assert metadata.author is None
        assert metadata.parent_title is None
        assert metadata.attachments == []


class TestProcessingState:
    """Tests for ProcessingState."""
    
    def test_defaults(self) -> None:
        """Test default values."""
        state = ProcessingState(project="test")
        
        assert state.project == "test"
        assert state.last_issue_updated is None
        assert state.last_wiki_updated is None
        assert state.issues_processed == 0
        assert state.wiki_pages_processed == 0
        assert state.last_run is None
    
    def test_with_values(self) -> None:
        """Test with actual values."""
        now = datetime.now()
        state = ProcessingState(
            project="test",
            last_issue_updated=now,
            issues_processed=100,
            last_run=now,
        )
        
        assert state.last_issue_updated == now
        assert state.issues_processed == 100
