"""Data models for Redmine Knowledge Agent.

These models represent the data structures used throughout the application.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class ProcessingMethod(str, Enum):
    """Method used to extract content from attachments."""

    OCR = "ocr"
    TEXT_EXTRACT = "text_extract"
    LLM = "llm"
    FALLBACK = "fallback"


@dataclass
class AttachmentInfo:
    """Information about an attachment."""

    id: int
    filename: str
    content_type: str
    filesize: int
    content_url: str
    description: str = ""

    @property
    def is_image(self) -> bool:
        """Check if the attachment is an image."""
        return self.content_type.startswith("image/")

    @property
    def is_pdf(self) -> bool:
        """Check if the attachment is a PDF."""
        return self.content_type == "application/pdf"

    @property
    def is_docx(self) -> bool:
        """Check if the attachment is a Word document."""
        return self.content_type in (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        )

    @property
    def is_spreadsheet(self) -> bool:
        """Check if the attachment is a spreadsheet."""
        return self.content_type in (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
            "text/csv",
        )


@dataclass
class ExtractedContent:
    """Content extracted from an attachment."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    processing_method: ProcessingMethod = ProcessingMethod.FALLBACK
    error: str | None = None

    @property
    def is_successful(self) -> bool:
        """Check if content extraction was successful."""
        return self.error is None and bool(self.text.strip())


@dataclass
class JournalEntry:
    """A journal entry (comment/change) on an issue."""

    id: int
    user: str
    notes: str
    created_on: datetime
    details: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class IssueMetadata:
    """Metadata for a Redmine issue."""

    id: int
    project: str
    tracker: str
    status: str
    priority: str
    subject: str
    description_textile: str
    created_on: datetime
    updated_on: datetime
    target_version: str | None = None
    assigned_to: str | None = None
    author: str | None = None
    done_ratio: int = 0
    estimated_hours: float | None = None
    spent_hours: float = 0.0
    attachments: list[AttachmentInfo] = field(default_factory=list)
    journals: list[JournalEntry] = field(default_factory=list)
    custom_fields: dict[str, Any] = field(default_factory=dict)
    parent_id: int | None = None

    @classmethod
    def from_redmine_issue(cls, issue: Any) -> IssueMetadata:
        """Create IssueMetadata from a python-redmine Issue object.

        Args:
            issue: A python-redmine Issue resource.

        Returns:
            IssueMetadata instance.

        """
        # Extract attachments
        attachments: list[AttachmentInfo] = []
        if hasattr(issue, "attachments"):
            attachments.extend(
                AttachmentInfo(
                    id=att.id,
                    filename=att.filename,
                    content_type=getattr(att, "content_type", "application/octet-stream"),
                    filesize=getattr(att, "filesize", 0),
                    content_url=att.content_url,
                    description=getattr(att, "description", "") or "",
                )
                for att in issue.attachments
            )

        # Extract journals
        journals: list[JournalEntry] = []
        if hasattr(issue, "journals"):
            journals.extend(
                JournalEntry(
                    id=journal.id,
                    user=getattr(journal.user, "name", "Unknown")
                    if hasattr(journal, "user")
                    else "Unknown",
                    notes=getattr(journal, "notes", "") or "",
                    created_on=journal.created_on
                    if hasattr(journal, "created_on")
                    else datetime.now(tz=UTC),
                    details=list(getattr(journal, "details", [])),
                )
                for journal in issue.journals
            )

        # Extract custom fields
        custom_fields = {}
        if hasattr(issue, "custom_fields"):
            for cf in issue.custom_fields:
                custom_fields[cf.name] = getattr(cf, "value", "")

        return cls(
            id=issue.id,
            project=issue.project.identifier
            if hasattr(issue.project, "identifier")
            else str(issue.project),
            tracker=issue.tracker.name if hasattr(issue, "tracker") else "Unknown",
            status=issue.status.name if hasattr(issue, "status") else "Unknown",
            priority=issue.priority.name if hasattr(issue, "priority") else "Normal",
            subject=issue.subject,
            description_textile=getattr(issue, "description", "") or "",
            created_on=issue.created_on,
            updated_on=issue.updated_on,
            target_version=getattr(issue.fixed_version, "name", None)
            if hasattr(issue, "fixed_version")
            else None,
            assigned_to=getattr(issue.assigned_to, "name", None)
            if hasattr(issue, "assigned_to")
            else None,
            author=getattr(issue.author, "name", None) if hasattr(issue, "author") else None,
            done_ratio=getattr(issue, "done_ratio", 0),
            estimated_hours=getattr(issue, "estimated_hours", None),
            spent_hours=getattr(issue, "spent_hours", 0.0) or 0.0,
            attachments=attachments,
            journals=journals,
            custom_fields=custom_fields,
            parent_id=getattr(issue.parent, "id", None) if hasattr(issue, "parent") else None,
        )


@dataclass
class WikiPageMetadata:
    """Metadata for a Redmine wiki page."""

    title: str
    project: str
    version: int
    created_on: datetime
    updated_on: datetime
    text_textile: str
    author: str | None = None
    comments: str = ""
    parent_title: str | None = None
    attachments: list[AttachmentInfo] = field(default_factory=list)

    @classmethod
    def from_redmine_wiki(cls, wiki_page: Any, project_id: str) -> WikiPageMetadata:
        """Create WikiPageMetadata from a python-redmine WikiPage object.

        Args:
            wiki_page: A python-redmine WikiPage resource.
            project_id: The project identifier.

        Returns:
            WikiPageMetadata instance.

        """
        attachments: list[AttachmentInfo] = []
        if hasattr(wiki_page, "attachments"):
            attachments.extend(
                AttachmentInfo(
                    id=att.id,
                    filename=att.filename,
                    content_type=getattr(att, "content_type", "application/octet-stream"),
                    filesize=getattr(att, "filesize", 0),
                    content_url=att.content_url,
                    description=getattr(att, "description", "") or "",
                )
                for att in wiki_page.attachments
            )

        return cls(
            title=wiki_page.title,
            project=project_id,
            version=getattr(wiki_page, "version", 1),
            created_on=getattr(wiki_page, "created_on", datetime.now(tz=UTC)),
            updated_on=getattr(wiki_page, "updated_on", datetime.now(tz=UTC)),
            text_textile=getattr(wiki_page, "text", "") or "",
            author=getattr(wiki_page.author, "name", None)
            if hasattr(wiki_page, "author")
            else None,
            comments=getattr(wiki_page, "comments", "") or "",
            parent_title=getattr(wiki_page.parent, "title", None)
            if hasattr(wiki_page, "parent")
            else None,
            attachments=attachments,
        )


@dataclass
class ProcessingState:
    """State for tracking processing progress."""

    project: str
    last_issue_updated: datetime | None = None
    last_wiki_updated: datetime | None = None
    issues_processed: int = 0
    wiki_pages_processed: int = 0
    last_run: datetime | None = None
