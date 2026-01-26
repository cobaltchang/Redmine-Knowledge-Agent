"""Markdown generator for Issues and Wiki pages.

Generates structured Markdown files from Redmine data.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from .converter import TextileConverter
from .models import (
    AttachmentInfo,
    ExtractedContent,
    IssueMetadata,
    JournalEntry,
    WikiPageMetadata,
)


class MarkdownGenerator:
    """Generates Markdown files from Redmine data."""
    
    def __init__(
        self,
        output_dir: Path,
        attachment_path_prefix: str = "./attachments",
    ) -> None:
        """Initialize the generator.
        
        Args:
            output_dir: Base output directory.
            attachment_path_prefix: Relative path prefix for attachments.
        """
        self.output_dir = output_dir
        self.attachment_path_prefix = attachment_path_prefix
        self.converter = TextileConverter(attachment_path_prefix)
    
    def generate_issue_markdown(
        self,
        issue: IssueMetadata,
        extracted_contents: dict[int, ExtractedContent] | None = None,
    ) -> str:
        """Generate Markdown content for an issue.
        
        Args:
            issue: Issue metadata.
            extracted_contents: Optional dict mapping attachment ID to extracted content.
            
        Returns:
            Markdown formatted string.
        """
        extracted_contents = extracted_contents or {}
        
        # Build front matter
        front_matter = self._build_issue_front_matter(issue)
        
        # Build content sections
        sections: list[str] = []
        
        # Title
        sections.append(f"# Issue #{issue.id}: {issue.subject}\n")
        
        # Description
        if issue.description_textile:
            sections.append("## 描述\n")
            md_description = self.converter.convert(issue.description_textile)
            sections.append(md_description + "\n")
        
        # Attachments
        if issue.attachments:
            sections.append("## 附件分析\n")
            for att in issue.attachments:
                att_section = self._build_attachment_section(
                    att, 
                    extracted_contents.get(att.id),
                )
                sections.append(att_section)
        
        # Journals (comments/changes)
        if issue.journals:
            journal_section = self._build_journals_section(issue.journals)
            if journal_section:  # pragma: no branch
                sections.append(journal_section)
        
        # Combine all parts
        content = front_matter + "\n" + "\n".join(sections)
        return content.strip() + "\n"
    
    def generate_wiki_markdown(
        self,
        wiki_page: WikiPageMetadata,
        extracted_contents: dict[int, ExtractedContent] | None = None,
    ) -> str:
        """Generate Markdown content for a wiki page.
        
        Args:
            wiki_page: Wiki page metadata.
            extracted_contents: Optional dict mapping attachment ID to extracted content.
            
        Returns:
            Markdown formatted string.
        """
        extracted_contents = extracted_contents or {}
        
        # Build front matter
        front_matter = self._build_wiki_front_matter(wiki_page)
        
        # Build content sections
        sections: list[str] = []
        
        # Title
        sections.append(f"# {wiki_page.title}\n")
        
        # Content
        if wiki_page.text_textile:
            md_content = self.converter.convert(wiki_page.text_textile)
            sections.append(md_content + "\n")
        
        # Attachments
        if wiki_page.attachments:
            sections.append("## 附件\n")
            for att in wiki_page.attachments:
                att_section = self._build_attachment_section(
                    att,
                    extracted_contents.get(att.id),
                )
                sections.append(att_section)
        
        # Combine all parts
        content = front_matter + "\n" + "\n".join(sections)
        return content.strip() + "\n"
    
    def _build_issue_front_matter(self, issue: IssueMetadata) -> str:
        """Build YAML front matter for an issue."""
        data: dict[str, Any] = {
            "id": issue.id,
            "project": issue.project,
            "tracker": issue.tracker,
            "status": issue.status,
            "priority": issue.priority,
            "subject": issue.subject,
            "created_on": self._format_datetime(issue.created_on),
            "updated_on": self._format_datetime(issue.updated_on),
        }
        
        # Optional fields
        if issue.target_version:
            data["target_version"] = issue.target_version
        if issue.assigned_to:
            data["assigned_to"] = issue.assigned_to
        if issue.author:
            data["author"] = issue.author
        if issue.done_ratio > 0:
            data["done_ratio"] = issue.done_ratio
        if issue.estimated_hours:
            data["estimated_hours"] = issue.estimated_hours
        if issue.spent_hours > 0:
            data["spent_hours"] = issue.spent_hours
        if issue.parent_id:
            data["parent_id"] = issue.parent_id
        if issue.custom_fields:
            data["custom_fields"] = issue.custom_fields
        
        return "---\n" + yaml.dump(data, allow_unicode=True, sort_keys=False) + "---\n"
    
    def _build_wiki_front_matter(self, wiki_page: WikiPageMetadata) -> str:
        """Build YAML front matter for a wiki page."""
        data: dict[str, Any] = {
            "title": wiki_page.title,
            "project": wiki_page.project,
            "version": wiki_page.version,
            "created_on": self._format_datetime(wiki_page.created_on),
            "updated_on": self._format_datetime(wiki_page.updated_on),
        }
        
        if wiki_page.author:
            data["author"] = wiki_page.author
        if wiki_page.parent_title:
            data["parent"] = wiki_page.parent_title
        
        return "---\n" + yaml.dump(data, allow_unicode=True, sort_keys=False) + "---\n"
    
    def _build_attachment_section(
        self,
        attachment: AttachmentInfo,
        extracted: ExtractedContent | None,
    ) -> str:
        """Build a section for an attachment."""
        lines: list[str] = []
        
        # Attachment header
        lines.append(f"### {attachment.filename}\n")
        
        # Image preview if applicable
        if attachment.is_image:
            lines.append(f"![{attachment.filename}]({self.attachment_path_prefix}/{attachment.filename})\n")
        
        # File info
        size_kb = attachment.filesize / 1024
        lines.append(f"*檔案大小: {size_kb:.1f} KB, 類型: {attachment.content_type}*\n")
        
        # Description
        if attachment.description:
            lines.append(f"*描述: {attachment.description}*\n")
        
        # Extracted content
        if extracted:
            if extracted.error:
                lines.append(f"> ⚠️ 處理失敗: {extracted.error}\n")
            elif extracted.text:
                method_label = {
                    "ocr": "OCR 提取",
                    "text_extract": "文字提取",
                    "llm": "AI 分析",
                    "fallback": "基本資訊",
                }.get(extracted.processing_method.value, "提取")
                
                lines.append(f"**{method_label}內容:**\n")
                lines.append(f"```\n{extracted.text[:2000]}")
                if len(extracted.text) > 2000:
                    lines.append("\n... (內容已截斷)")
                lines.append("\n```\n")
        
        return "\n".join(lines)
    
    def _build_journals_section(self, journals: list[JournalEntry]) -> str:
        """Build a section for journal entries (comments/changes)."""
        # Filter to only include journals with notes
        journals_with_notes = [j for j in journals if j.notes and j.notes.strip()]
        
        if not journals_with_notes:
            return ""
        
        lines: list[str] = ["## 討論記錄\n"]
        
        for journal in journals_with_notes:
            date_str = self._format_datetime(journal.created_on)
            md_notes = self.converter.convert(journal.notes)
            lines.append(f"### {date_str} - {journal.user}\n")
            lines.append(f"{md_notes}\n")
        
        return "\n".join(lines)
    
    def _format_datetime(self, dt: datetime) -> str:
        """Format a datetime for display."""
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def save_issue(
        self,
        issue: IssueMetadata,
        extracted_contents: dict[int, ExtractedContent] | None = None,
    ) -> Path:
        """Generate and save an issue Markdown file.
        
        Args:
            issue: Issue metadata.
            extracted_contents: Optional dict mapping attachment ID to extracted content.
            
        Returns:
            Path to the saved file.
        """
        content = self.generate_issue_markdown(issue, extracted_contents)
        
        # Create output path
        issues_dir = self.output_dir / issue.project / "issues"
        issues_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = issues_dir / f"{issue.id:05d}.md"
        file_path.write_text(content, encoding="utf-8")
        
        return file_path
    
    def save_wiki_page(
        self,
        wiki_page: WikiPageMetadata,
        extracted_contents: dict[int, ExtractedContent] | None = None,
    ) -> Path:
        """Generate and save a wiki page Markdown file.
        
        Args:
            wiki_page: Wiki page metadata.
            extracted_contents: Optional dict mapping attachment ID to extracted content.
            
        Returns:
            Path to the saved file.
        """
        content = self.generate_wiki_markdown(wiki_page, extracted_contents)
        
        # Create output path
        wiki_dir = self.output_dir / wiki_page.project / "wiki"
        wiki_dir.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename
        safe_title = self._sanitize_filename(wiki_page.title)
        file_path = wiki_dir / f"{safe_title}.md"
        file_path.write_text(content, encoding="utf-8")
        
        return file_path
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a string for use as a filename."""
        # Replace problematic characters
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            name = name.replace(char, '_')
        return name
