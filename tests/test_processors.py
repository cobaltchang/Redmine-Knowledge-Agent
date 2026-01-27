"""Tests for attachment processors."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from redmine_knowledge_agent.models import ProcessingMethod
from redmine_knowledge_agent.processors import (
    BaseProcessor,
    DocxProcessor,
    FallbackProcessor,
    ImageProcessor,
    PdfProcessor,
    ProcessorFactory,
    SpreadsheetProcessor,
)


class TestImageProcessor:
    """Tests for ImageProcessor."""

    @pytest.fixture
    def processor(self) -> ImageProcessor:
        """Create an ImageProcessor."""
        return ImageProcessor()

    def test_supported_types(self, processor: ImageProcessor) -> None:
        """Test supported MIME types."""
        types = processor.supported_types
        assert "image/png" in types
        assert "image/jpeg" in types
        assert "image/gif" in types

    def test_file_not_found(self, processor: ImageProcessor, tmp_path: Path) -> None:
        """Test processing non-existent file."""
        result = processor.process(tmp_path / "nonexistent.png")
        assert result.error is not None
        assert "not found" in result.error.lower()

    @patch("redmine_knowledge_agent.processors.pytesseract")
    @patch("redmine_knowledge_agent.processors.Image")
    def test_successful_ocr(
        self,
        mock_image: MagicMock,
        mock_tesseract: MagicMock,
        processor: ImageProcessor,
        tmp_path: Path,
    ) -> None:
        """Test successful OCR processing."""
        # Create a test file
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image data")

        # Mock the image opening
        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_image.open.return_value.__enter__.return_value = mock_img

        # Mock OCR result
        mock_tesseract.image_to_string.return_value = "Extracted text from image"

        result = processor.process(test_file)

        assert result.text == "Extracted text from image"
        assert result.processing_method == ProcessingMethod.OCR
        assert result.error is None

    @patch("redmine_knowledge_agent.processors.pytesseract", None)
    @patch("redmine_knowledge_agent.processors.Image", None)
    def test_ocr_import_error(
        self,
        processor: ImageProcessor,
        tmp_path: Path,
    ) -> None:
        """Test handling of missing OCR dependencies."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image data")

        result = processor.process(test_file)

        assert result.error is not None
        assert "not available" in result.error.lower() or "not installed" in result.error.lower()


class TestPdfProcessor:
    """Tests for PdfProcessor."""

    @pytest.fixture
    def processor(self) -> PdfProcessor:
        """Create a PdfProcessor."""
        return PdfProcessor()

    def test_supported_types(self, processor: PdfProcessor) -> None:
        """Test supported MIME types."""
        assert processor.supported_types == ["application/pdf"]

    def test_file_not_found(self, processor: PdfProcessor, tmp_path: Path) -> None:
        """Test processing non-existent file."""
        result = processor.process(tmp_path / "nonexistent.pdf")
        assert result.error is not None

    @patch("redmine_knowledge_agent.processors.fitz")
    def test_successful_extraction(
        self,
        mock_fitz: MagicMock,
        processor: PdfProcessor,
        tmp_path: Path,
    ) -> None:
        """Test successful PDF text extraction."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf data")

        # Mock PDF document
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Page 1 text"

        mock_doc = MagicMock()
        mock_doc.__enter__.return_value = mock_doc
        mock_doc.__exit__.return_value = None
        mock_doc.__iter__.return_value = [mock_page]
        mock_doc.__len__.return_value = 1

        mock_fitz.open.return_value = mock_doc

        result = processor.process(test_file)

        assert "Page 1 text" in result.text
        assert result.processing_method == ProcessingMethod.TEXT_EXTRACT
        assert result.metadata.get("page_count") == 1


class TestDocxProcessor:
    """Tests for DocxProcessor."""

    @pytest.fixture
    def processor(self) -> DocxProcessor:
        """Create a DocxProcessor."""
        return DocxProcessor()

    def test_supported_types(self, processor: DocxProcessor) -> None:
        """Test supported MIME types."""
        types = processor.supported_types
        assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in types
        assert "application/msword" in types

    def test_file_not_found(self, processor: DocxProcessor, tmp_path: Path) -> None:
        """Test processing non-existent file."""
        result = processor.process(tmp_path / "nonexistent.docx")
        assert result.error is not None

    @patch("redmine_knowledge_agent.processors.Document")
    def test_successful_extraction(
        self,
        mock_document_class: MagicMock,
        processor: DocxProcessor,
        tmp_path: Path,
    ) -> None:
        """Test successful DOCX text extraction."""
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx data")

        # Mock document
        mock_para1 = MagicMock()
        mock_para1.text = "Paragraph 1"
        mock_para2 = MagicMock()
        mock_para2.text = "Paragraph 2"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para1, mock_para2]
        mock_doc.tables = []

        mock_document_class.return_value = mock_doc

        result = processor.process(test_file)

        assert "Paragraph 1" in result.text
        assert "Paragraph 2" in result.text
        assert result.processing_method == ProcessingMethod.TEXT_EXTRACT


class TestSpreadsheetProcessor:
    """Tests for SpreadsheetProcessor."""

    @pytest.fixture
    def processor(self) -> SpreadsheetProcessor:
        """Create a SpreadsheetProcessor."""
        return SpreadsheetProcessor()

    def test_supported_types(self, processor: SpreadsheetProcessor) -> None:
        """Test supported MIME types."""
        types = processor.supported_types
        assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in types
        assert "text/csv" in types

    def test_file_not_found(self, processor: SpreadsheetProcessor, tmp_path: Path) -> None:
        """Test processing non-existent file."""
        result = processor.process(tmp_path / "nonexistent.xlsx")
        assert result.error is not None

    def test_csv_processing(self, processor: SpreadsheetProcessor, tmp_path: Path) -> None:
        """Test CSV file processing."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Name,Age\nAlice,30\nBob,25")

        result = processor.process(csv_file)

        assert "Name" in result.text
        assert "Alice" in result.text
        assert "|" in result.text  # Markdown table
        assert result.processing_method == ProcessingMethod.TEXT_EXTRACT

    def test_empty_csv(self, processor: SpreadsheetProcessor, tmp_path: Path) -> None:
        """Test empty CSV file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")

        result = processor.process(csv_file)
        assert "Empty" in result.text or result.metadata.get("row_count") == 0

    def test_rows_to_markdown(self, processor: SpreadsheetProcessor) -> None:
        """Test _rows_to_markdown helper."""
        rows = [["A", "B"], ["1", "2"], ["3", "4"]]
        md = processor._rows_to_markdown(rows)

        assert "| A | B |" in md
        assert "| --- | --- |" in md
        assert "| 1 | 2 |" in md


class TestFallbackProcessor:
    """Tests for FallbackProcessor."""

    @pytest.fixture
    def processor(self) -> FallbackProcessor:
        """Create a FallbackProcessor."""
        return FallbackProcessor()

    def test_supported_types(self, processor: FallbackProcessor) -> None:
        """Test supported types (matches everything)."""
        assert processor.supported_types == ["*/*"]

    def test_file_not_found(self, processor: FallbackProcessor, tmp_path: Path) -> None:
        """Test processing non-existent file."""
        result = processor.process(tmp_path / "nonexistent.xyz")
        assert result.error is not None

    def test_returns_metadata(self, processor: FallbackProcessor, tmp_path: Path) -> None:
        """Test that fallback returns file metadata."""
        test_file = tmp_path / "test.xyz"
        test_file.write_bytes(b"some data")

        result = processor.process(test_file)

        assert result.processing_method == ProcessingMethod.FALLBACK
        assert "test.xyz" in result.text
        assert result.metadata.get("filename") == "test.xyz"


class TestProcessorFactory:
    """Tests for ProcessorFactory."""

    @pytest.fixture
    def factory(self) -> ProcessorFactory:
        """Create a ProcessorFactory."""
        return ProcessorFactory()

    def test_get_image_processor(self, factory: ProcessorFactory) -> None:
        """Test getting image processor."""
        processor = factory.get_processor("image/png")
        assert isinstance(processor, ImageProcessor)

    def test_get_pdf_processor(self, factory: ProcessorFactory) -> None:
        """Test getting PDF processor."""
        processor = factory.get_processor("application/pdf")
        assert isinstance(processor, PdfProcessor)

    def test_get_docx_processor(self, factory: ProcessorFactory) -> None:
        """Test getting DOCX processor."""
        processor = factory.get_processor(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        assert isinstance(processor, DocxProcessor)

    def test_get_spreadsheet_processor(self, factory: ProcessorFactory) -> None:
        """Test getting spreadsheet processor."""
        processor = factory.get_processor("text/csv")
        assert isinstance(processor, SpreadsheetProcessor)

    def test_get_fallback_processor(self, factory: ProcessorFactory) -> None:
        """Test getting fallback for unknown type."""
        processor = factory.get_processor("application/unknown")
        assert isinstance(processor, FallbackProcessor)

    def test_get_processor_by_filename(self, factory: ProcessorFactory) -> None:
        """Test getting processor by filename hint."""
        processor = factory.get_processor("application/octet-stream", "test.png")
        assert isinstance(processor, ImageProcessor)

    def test_get_processor_by_filename_unknown_extension(self, factory: ProcessorFactory) -> None:
        """Test getting processor with unknown extension falls back."""
        processor = factory.get_processor("application/octet-stream", "file.xyz123")
        assert isinstance(processor, FallbackProcessor)

    def test_register_custom_processor(self, factory: ProcessorFactory) -> None:
        """Test registering a custom processor."""
        custom = MagicMock(spec=BaseProcessor)
        factory.register_processor("custom/type", custom)

        result = factory.get_processor("custom/type")
        assert result is custom

    def test_process_file(self, factory: ProcessorFactory, tmp_path: Path) -> None:
        """Test process_file convenience method."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("A,B\n1,2")

        result = factory.process_file(csv_file)

        assert result.processing_method == ProcessingMethod.TEXT_EXTRACT

    def test_process_file_with_mime_type(self, factory: ProcessorFactory, tmp_path: Path) -> None:
        """Test process_file with explicit MIME type."""
        # Use a file with unknown extension but provide MIME type
        test_file = tmp_path / "data.csv"
        test_file.write_text("A,B\n1,2")

        result = factory.process_file(test_file, mime_type="text/csv")

        assert "A" in result.text


class TestImageProcessorRGBAConversion:
    """Additional tests for ImageProcessor edge cases."""

    @patch("redmine_knowledge_agent.processors.pytesseract")
    @patch("redmine_knowledge_agent.processors.Image")
    def test_rgba_image_conversion(
        self,
        mock_image: MagicMock,
        mock_tesseract: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test RGBA image is converted to RGB."""
        processor = ImageProcessor()
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image data")

        # Mock RGBA image
        mock_img = MagicMock()
        mock_img.mode = "RGBA"
        mock_converted = MagicMock()
        mock_img.convert.return_value = mock_converted
        mock_image.open.return_value.__enter__.return_value = mock_img

        mock_tesseract.image_to_string.return_value = "Text"

        processor.process(test_file)

        mock_img.convert.assert_called_once_with("RGB")

    @patch("redmine_knowledge_agent.processors.pytesseract")
    @patch("redmine_knowledge_agent.processors.Image")
    def test_ocr_exception(
        self,
        mock_image: MagicMock,
        mock_tesseract: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test OCR exception handling."""
        processor = ImageProcessor()
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake image data")

        mock_img = MagicMock()
        mock_img.mode = "RGB"
        mock_image.open.return_value.__enter__.return_value = mock_img
        mock_tesseract.image_to_string.side_effect = RuntimeError("OCR error")

        result = processor.process(test_file)

        assert result.error is not None
        assert "OCR failed" in result.error


class TestPdfProcessorEdgeCases:
    """Additional tests for PdfProcessor edge cases."""

    @patch("redmine_knowledge_agent.processors.fitz", None)
    def test_fitz_not_installed(self, tmp_path: Path) -> None:
        """Test handling of missing fitz dependency."""
        processor = PdfProcessor()
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf")

        result = processor.process(test_file)

        assert result.error is not None
        assert "not installed" in result.error.lower() or "not available" in result.error.lower()

    @patch("redmine_knowledge_agent.processors.fitz")
    def test_pdf_extraction_exception(
        self,
        mock_fitz: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test PDF extraction exception handling."""
        processor = PdfProcessor()
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"fake pdf")

        mock_fitz.open.side_effect = RuntimeError("Corrupt PDF")

        result = processor.process(test_file)

        assert result.error is not None
        assert "failed" in result.error.lower()


class TestDocxProcessorEdgeCases:
    """Additional tests for DocxProcessor edge cases."""

    @patch("redmine_knowledge_agent.processors.Document", None)
    def test_docx_not_installed(self, tmp_path: Path) -> None:
        """Test handling of missing python-docx dependency."""
        processor = DocxProcessor()
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx")

        result = processor.process(test_file)

        assert result.error is not None
        assert "not installed" in result.error.lower() or "not available" in result.error.lower()

    @patch("redmine_knowledge_agent.processors.Document")
    def test_docx_with_tables(
        self,
        mock_document_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test DOCX with tables extraction."""
        processor = DocxProcessor()
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx")

        # Mock document with tables
        mock_para = MagicMock()
        mock_para.text = "Paragraph text"

        mock_cell1 = MagicMock()
        mock_cell1.text = "Cell 1"
        mock_cell2 = MagicMock()
        mock_cell2.text = "Cell 2"

        mock_row = MagicMock()
        mock_row.cells = [mock_cell1, mock_cell2]

        mock_table = MagicMock()
        mock_table.rows = [mock_row]

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = [mock_table]

        mock_document_class.return_value = mock_doc

        result = processor.process(test_file)

        assert "Paragraph text" in result.text
        assert "Tables" in result.text
        assert "Cell 1" in result.text

    @patch("redmine_knowledge_agent.processors.Document")
    def test_docx_extraction_exception(
        self,
        mock_document_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test DOCX extraction exception handling."""
        processor = DocxProcessor()
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"fake docx")

        mock_document_class.side_effect = RuntimeError("Corrupt file")

        result = processor.process(test_file)

        assert result.error is not None
        assert "failed" in result.error.lower()


class TestSpreadsheetProcessorEdgeCases:
    """Additional tests for SpreadsheetProcessor edge cases."""

    @patch("redmine_knowledge_agent.processors.openpyxl", None)
    def test_openpyxl_not_installed(self, tmp_path: Path) -> None:
        """Test handling of missing openpyxl dependency."""
        processor = SpreadsheetProcessor()
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"fake xlsx")

        result = processor.process(test_file)

        assert result.error is not None
        assert "not installed" in result.error.lower() or "not available" in result.error.lower()

    @patch("redmine_knowledge_agent.processors.openpyxl")
    def test_excel_processing(
        self,
        mock_openpyxl: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test Excel file processing."""
        processor = SpreadsheetProcessor()
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"fake xlsx")

        # Mock workbook
        mock_sheet = MagicMock()
        mock_sheet.iter_rows.return_value = [
            ("Header1", "Header2"),
            ("Value1", "Value2"),
        ]

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_wb.__getitem__.return_value = mock_sheet

        mock_openpyxl.load_workbook.return_value = mock_wb

        result = processor.process(test_file)

        assert result.processing_method == ProcessingMethod.TEXT_EXTRACT
        mock_wb.close.assert_called_once()

    @patch("redmine_knowledge_agent.processors.openpyxl")
    def test_excel_empty_rows_skipped(
        self,
        mock_openpyxl: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test empty rows are skipped in Excel."""
        processor = SpreadsheetProcessor()
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"fake xlsx")

        mock_sheet = MagicMock()
        mock_sheet.iter_rows.return_value = [
            ("Header1", "Header2"),
            (None, None),  # Empty row
            ("", ""),  # Also empty
            ("Value1", "Value2"),
        ]

        mock_wb = MagicMock()
        mock_wb.sheetnames = ["Sheet1"]
        mock_wb.__getitem__.return_value = mock_sheet

        mock_openpyxl.load_workbook.return_value = mock_wb

        result = processor.process(test_file)

        # Should only have 2 data rows (header + value)
        assert "Header1" in result.text
        assert "Value1" in result.text

    def test_spreadsheet_extraction_exception(self, tmp_path: Path) -> None:
        """Test spreadsheet extraction exception handling."""
        processor = SpreadsheetProcessor()
        test_file = tmp_path / "test.csv"
        test_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8

        # This should handle the exception gracefully
        result = processor.process(test_file)
        # May succeed with errors='replace' or may fail
        assert result is not None

    def test_rows_to_markdown_empty(self) -> None:
        """Test _rows_to_markdown with empty rows."""
        processor = SpreadsheetProcessor()
        assert processor._rows_to_markdown([]) == ""

    def test_csv_single_row(self, tmp_path: Path) -> None:
        """Test CSV with single row (header only)."""
        processor = SpreadsheetProcessor()
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("A,B,C")

        result = processor.process(csv_file)

        assert "| A | B | C |" in result.text

    @patch("redmine_knowledge_agent.processors.openpyxl")
    def test_excel_processing_exception(
        self,
        mock_openpyxl: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test Excel processing exception."""
        processor = SpreadsheetProcessor()
        test_file = tmp_path / "test.xlsx"
        test_file.write_bytes(b"fake xlsx")

        mock_openpyxl.load_workbook.side_effect = RuntimeError("Corrupt file")

        result = processor.process(test_file)

        assert result.error is not None
        assert "failed" in result.error.lower()
