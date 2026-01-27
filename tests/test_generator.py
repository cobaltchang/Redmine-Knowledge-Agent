"""Tests for Markdown generator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from redmine_knowledge_agent.generator import MarkdownGenerator
from redmine_knowledge_agent.models import (
    AttachmentInfo,
    ExtractedContent,
    IssueMetadata,
    JournalEntry,
    ProcessingMethod,
    WikiPageMetadata,
)


class TestMarkdownGenerator:
    """Tests for MarkdownGenerator."""

    @pytest.fixture
    def generator(self, tmp_output_dir: Path) -> MarkdownGenerator:
        """Create a MarkdownGenerator."""
        return MarkdownGenerator(tmp_output_dir)

    def test_generate_issue_markdown_basic(
        self,
        generator: MarkdownGenerator,
        sample_issue: IssueMetadata,
    ) -> None:
        """Test basic issue markdown generation."""
        md = generator.generate_issue_markdown(sample_issue)

        # Check front matter
        assert "---" in md
        assert "id: 12345" in md
        assert "project: test_project" in md
        assert "tracker: Bug" in md
        assert "status: In Progress" in md
        assert "priority: High" in md
        assert "target_version: v2.0.0" in md

        # Check title
        assert "# Issue #12345: Test Issue Subject" in md

        # Check description conversion
        assert "## Description" in md or "## 描述" in md

    def test_generate_issue_markdown_with_attachments(
        self,
        generator: MarkdownGenerator,
        sample_issue: IssueMetadata,
        sample_extracted_content: ExtractedContent,
    ) -> None:
        """Test issue markdown with attachment content."""
        extracted = {sample_issue.attachments[0].id: sample_extracted_content}
        md = generator.generate_issue_markdown(sample_issue, extracted)

        assert "test_image.png" in md
        assert "OCR" in md or "提取" in md

    def test_generate_issue_markdown_with_journals(
        self,
        generator: MarkdownGenerator,
        sample_issue: IssueMetadata,
    ) -> None:
        """Test issue markdown includes journals."""
        md = generator.generate_issue_markdown(sample_issue)

        # Should include journal/comment section
        assert "討論記錄" in md or "Discussion" in md
        assert "Test User" in md

    def test_generate_wiki_markdown_basic(
        self,
        generator: MarkdownGenerator,
        sample_wiki_page: WikiPageMetadata,
    ) -> None:
        """Test basic wiki page markdown generation."""
        md = generator.generate_wiki_markdown(sample_wiki_page)

        # Check front matter
        assert "---" in md
        assert "title: TestWikiPage" in md
        assert "project: test_project" in md
        assert "version: 3" in md

        # Check title
        assert "# TestWikiPage" in md

    def test_generate_wiki_markdown_with_attachments(
        self,
        generator: MarkdownGenerator,
        sample_wiki_page: WikiPageMetadata,
        sample_extracted_content: ExtractedContent,
    ) -> None:
        """Test wiki markdown with attachment content."""
        extracted = {sample_wiki_page.attachments[0].id: sample_extracted_content}
        md = generator.generate_wiki_markdown(sample_wiki_page, extracted)

        assert "test_image.png" in md

    def test_save_issue(
        self,
        generator: MarkdownGenerator,
        sample_issue: IssueMetadata,
    ) -> None:
        """Test saving issue to file."""
        path = generator.save_issue(sample_issue)

        assert path.exists()
        assert path.name == "12345.md"
        assert "issues" in str(path)

        content = path.read_text(encoding="utf-8")
        assert "Issue #12345" in content

    def test_save_wiki_page(
        self,
        generator: MarkdownGenerator,
        sample_wiki_page: WikiPageMetadata,
    ) -> None:
        """Test saving wiki page to file."""
        path = generator.save_wiki_page(sample_wiki_page)

        assert path.exists()
        assert path.name == "TestWikiPage.md"
        assert "wiki" in str(path)

        content = path.read_text(encoding="utf-8")
        assert "TestWikiPage" in content

    def test_sanitize_filename(self, generator: MarkdownGenerator) -> None:
        """Test filename sanitization."""
        assert generator._sanitize_filename("normal") == "normal"
        assert generator._sanitize_filename("with/slash") == "with_slash"
        assert generator._sanitize_filename("with:colon") == "with_colon"
        assert generator._sanitize_filename('with"quote') == "with_quote"

    def test_format_datetime(self, generator: MarkdownGenerator) -> None:
        """Test datetime formatting."""
        dt = datetime(2024, 1, 15, 14, 30, tzinfo=UTC)
        formatted = generator._format_datetime(dt)
        assert formatted == "2024-01-15 14:30"

    def test_build_attachment_section_with_error(
        self,
        generator: MarkdownGenerator,
        sample_attachment: AttachmentInfo,
    ) -> None:
        """Test attachment section when extraction failed."""
        extracted = ExtractedContent(
            text="",
            processing_method=ProcessingMethod.FALLBACK,
            error="Failed to process",
        )

        section = generator._build_attachment_section(sample_attachment, extracted)

        assert "test_image.png" in section
        assert "處理失敗" in section or "Failed" in section

    def test_build_journals_section_empty(self, generator: MarkdownGenerator) -> None:
        """Test journals section with empty journals."""
        # Journals with no notes
        journals = [
            JournalEntry(
                id=1,
                user="User",
                notes="",
                created_on=datetime.now(tz=UTC),
            ),
        ]

        section = generator._build_journals_section(journals)
        assert section == ""

    def test_issue_front_matter_optional_fields(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test front matter with optional fields."""
        issue = IssueMetadata(
            id=1,
            project="proj",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test",
            description_textile="",
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
            # No optional fields
        )

        fm = generator._build_issue_front_matter(issue)

        assert "target_version" not in fm
        assert "assigned_to" not in fm
        assert "parent_id" not in fm

    def test_issue_front_matter_all_fields(
        self,
        generator: MarkdownGenerator,
        sample_issue: IssueMetadata,
    ) -> None:
        """Test front matter includes all set fields."""
        sample_issue.custom_fields = {"Custom": "Value"}
        sample_issue.parent_id = 100

        fm = generator._build_issue_front_matter(sample_issue)

        assert "target_version" in fm
        assert "assigned_to" in fm
        assert "author" in fm
        assert "done_ratio" in fm
        assert "parent_id" in fm
        assert "custom_fields" in fm

    def test_attachment_section_image_preview(
        self,
        generator: MarkdownGenerator,
        sample_attachment: AttachmentInfo,
    ) -> None:
        """Test image attachment includes preview markdown."""
        section = generator._build_attachment_section(sample_attachment, None)

        # Should include image markdown
        assert "![test_image.png]" in section

    def test_attachment_section_non_image(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test non-image attachment doesn't include preview."""
        pdf_att = AttachmentInfo(
            id=1,
            filename="doc.pdf",
            content_type="application/pdf",
            filesize=1024,
            content_url="http://test/1",
        )

        section = generator._build_attachment_section(pdf_att, None)

        # Should not include image markdown
        assert "![doc.pdf]" not in section
        assert "doc.pdf" in section

    def test_extracted_content_truncation(
        self,
        generator: MarkdownGenerator,
        sample_attachment: AttachmentInfo,
    ) -> None:
        """Test long extracted content is truncated."""
        long_text = "A" * 3000  # More than 2000 chars
        extracted = ExtractedContent(
            text=long_text,
            processing_method=ProcessingMethod.TEXT_EXTRACT,
        )

        section = generator._build_attachment_section(sample_attachment, extracted)

        assert "截斷" in section or "truncat" in section.lower()

    def test_issue_without_description(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test issue without description."""
        issue = IssueMetadata(
            id=1,
            project="proj",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test",
            description_textile="",  # Empty description
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
        )

        md = generator.generate_issue_markdown(issue)

        # Should still generate valid markdown
        assert "# Issue #1" in md

    def test_wiki_page_without_text(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test wiki page without text."""
        wiki = WikiPageMetadata(
            title="EmptyPage",
            project="proj",
            text_textile="",  # Empty content
            version=1,
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
        )

        md = generator.generate_wiki_markdown(wiki)

        assert "# EmptyPage" in md

    def test_wiki_front_matter_with_parent(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test wiki front matter with parent title."""
        wiki = WikiPageMetadata(
            title="ChildPage",
            project="proj",
            text_textile="Content",
            version=1,
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
            parent_title="ParentPage",
            author="Author",
        )

        fm = generator._build_wiki_front_matter(wiki)

        assert "parent: ParentPage" in fm
        assert "author: Author" in fm

    def test_journals_section_with_multiple_entries(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test journals section with multiple entries."""
        journals = [
            JournalEntry(
                id=1,
                user="User A",
                notes="First comment",
                created_on=datetime(2024, 1, 10, 10, 0, tzinfo=UTC),
            ),
            JournalEntry(
                id=2,
                user="User B",
                notes="Second comment",
                created_on=datetime(2024, 1, 11, 11, 0, tzinfo=UTC),
            ),
        ]

        section = generator._build_journals_section(journals)

        assert "User A" in section
        assert "User B" in section
        assert "First comment" in section
        assert "Second comment" in section

    def test_attachment_description(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test attachment with description."""
        att = AttachmentInfo(
            id=1,
            filename="doc.pdf",
            content_type="application/pdf",
            filesize=2048,
            content_url="http://test/1",
            description="Important document",
        )

        section = generator._build_attachment_section(att, None)

        assert "Important document" in section

    def test_various_processing_methods(
        self,
        generator: MarkdownGenerator,
        sample_attachment: AttachmentInfo,
    ) -> None:
        """Test different processing method labels."""
        methods = [
            ProcessingMethod.OCR,
            ProcessingMethod.TEXT_EXTRACT,
            ProcessingMethod.LLM,
            ProcessingMethod.FALLBACK,
        ]

        for method in methods:
            extracted = ExtractedContent(
                text="Some text",
                processing_method=method,
            )
            section = generator._build_attachment_section(sample_attachment, extracted)
            # Just verify it doesn't crash
            assert sample_attachment.filename in section

    def test_issue_with_spent_hours(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test issue with spent hours in front matter."""
        issue = IssueMetadata(
            id=1,
            project="proj",
            tracker="Task",
            status="Done",
            priority="Normal",
            subject="Test",
            description_textile="",
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
            estimated_hours=8.0,
            spent_hours=6.5,
        )

        fm = generator._build_issue_front_matter(issue)

        assert "estimated_hours: 8.0" in fm
        assert "spent_hours: 6.5" in fm

    def test_attachment_section_empty_extracted_text(
        self,
        generator: MarkdownGenerator,
        sample_attachment: AttachmentInfo,
    ) -> None:
        """Test attachment section when extracted content has no text."""
        extracted = ExtractedContent(
            text="",  # Empty text, no error
            processing_method=ProcessingMethod.TEXT_EXTRACT,
        )

        section = generator._build_attachment_section(sample_attachment, extracted)

        # Should not include extracted content section
        assert "內容:" not in section
        assert sample_attachment.filename in section

    def test_journals_section_filters_empty_notes(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test journals with whitespace-only notes are filtered out."""
        journals = [
            JournalEntry(
                id=1,
                user="User A",
                notes="   ",  # Whitespace only
                created_on=datetime(2024, 1, 10, tzinfo=UTC),
            ),
            JournalEntry(
                id=2,
                user="User B",
                notes="Real comment",
                created_on=datetime(2024, 1, 11, tzinfo=UTC),
            ),
        ]

        section = generator._build_journals_section(journals)

        assert "User B" in section
        assert "Real comment" in section

    def test_issue_with_no_journals(
        self,
        generator: MarkdownGenerator,
    ) -> None:
        """Test issue without journals."""
        issue = IssueMetadata(
            id=1,
            project="proj",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test",
            description_textile="Desc",
            created_on=datetime.now(tz=UTC),
            updated_on=datetime.now(tz=UTC),
            journals=[],  # Empty journals
        )

        md = generator.generate_issue_markdown(issue)

        # Should not have discussion section
        assert "討論記錄" not in md
