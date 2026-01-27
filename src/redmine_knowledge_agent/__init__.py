"""Redmine Knowledge Agent - Extract knowledge from Redmine to Markdown.

This package provides tools for fetching Issues and Wiki pages from Redmine,
processing attachments (OCR, PDF extraction), converting Textile to Markdown,
and generating structured Markdown files for RAG applications.
"""

__version__ = "2.0.0"

from .client import RedmineClient
from .config import AppConfig, OutputConfig, RedmineConfig
from .converter import TextileConverter, textile_to_markdown
from .generator import MarkdownGenerator
from .models import (
    AttachmentInfo,
    ExtractedContent,
    IssueMetadata,
    JournalEntry,
    ProcessingMethod,
    WikiPageMetadata,
)
from .processors import (
    BaseProcessor,
    DocxProcessor,
    FallbackProcessor,
    ImageProcessor,
    PdfProcessor,
    ProcessorFactory,
    SpreadsheetProcessor,
)

__all__ = [
    "AppConfig",
    "AttachmentInfo",
    "BaseProcessor",
    "DocxProcessor",
    "ExtractedContent",
    "FallbackProcessor",
    "ImageProcessor",
    "IssueMetadata",
    "JournalEntry",
    "MarkdownGenerator",
    "OutputConfig",
    "PdfProcessor",
    "ProcessingMethod",
    "ProcessorFactory",
    "RedmineClient",
    "RedmineConfig",
    "SpreadsheetProcessor",
    "TextileConverter",
    "WikiPageMetadata",
    "__version__",
    "textile_to_markdown",
]
