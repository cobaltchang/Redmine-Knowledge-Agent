"""Tests for CLI module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from redmine_knowledge_agent.__main__ import app, setup_logging, FetchMode


runner = CliRunner()


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_setup_logging_console(self) -> None:
        """Test logging setup with console format."""
        setup_logging(level="DEBUG", format="console")
        # Should not raise
    
    def test_setup_logging_json(self) -> None:
        """Test logging setup with JSON format."""
        setup_logging(level="INFO", format="json")
        # Should not raise


class TestFetchMode:
    """Tests for FetchMode enum."""
    
    def test_values(self) -> None:
        """Test FetchMode values."""
        assert FetchMode.FULL.value == "full"
        assert FetchMode.INCREMENTAL.value == "incremental"


class TestListProjectsCommand:
    """Tests for list-projects command."""
    
    def test_list_projects(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test list-projects command."""
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        # Create config file
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [{"path": "./output", "projects": ["proj"]}],
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Mock the client
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.list_projects.return_value = [
                {"identifier": "proj_a", "name": "Project A", "description": "Desc A"},
                {"identifier": "proj_b", "name": "Project B", "description": ""},
            ]
            mock_client_class.return_value = mock_client
            
            result = runner.invoke(app, ["list-projects", "--config", str(config_file)])
            
            assert result.exit_code == 0
            assert "proj_a" in result.stdout
            assert "Project A" in result.stdout
    
    def test_list_projects_config_not_found(self, tmp_path: Path) -> None:
        """Test list-projects with missing config."""
        result = runner.invoke(app, ["list-projects", "--config", str(tmp_path / "missing.yaml")])
        
        assert result.exit_code != 0


class TestFetchCommand:
    """Tests for fetch command."""
    
    @pytest.fixture
    def config_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a test config file."""
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": str(tmp_path / "output"),
                    "projects": ["proj_a"],
                    "include_subprojects": False,
                }
            ],
            "logging": {"level": "WARNING", "format": "console"},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        return config_file
    
    def test_fetch_full(self, config_file: Path) -> None:
        """Test fetch command in full mode."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.return_value = iter([])
                mock_client.get_project_wiki_pages.return_value = iter([])
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                
                assert result.exit_code == 0
                assert "完成" in result.stdout
    
    def test_fetch_skip_attachments(self, config_file: Path) -> None:
        """Test fetch with --skip-attachments."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.return_value = iter([])
                mock_client.get_project_wiki_pages.return_value = iter([])
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, [
                    "fetch",
                    "--config", str(config_file),
                    "--skip-attachments",
                ])
                
                assert result.exit_code == 0
    
    def test_fetch_skip_wiki(self, config_file: Path) -> None:
        """Test fetch with --skip-wiki."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.return_value = iter([])
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, [
                    "fetch",
                    "--config", str(config_file),
                    "--skip-wiki",
                ])
                
                assert result.exit_code == 0
                # Wiki pages should not be fetched
                mock_client.get_project_wiki_pages.assert_not_called()
    
    def test_fetch_specific_projects(self, config_file: Path) -> None:
        """Test fetch with --projects filter."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.return_value = iter([])
                mock_client.get_project_wiki_pages.return_value = iter([])
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, [
                    "fetch",
                    "--config", str(config_file),
                    "--projects", "proj_a",
                ])
                
                assert result.exit_code == 0


class TestConvertTextileCommand:
    """Tests for convert-textile command."""
    
    def test_convert_textile_to_stdout(self, tmp_path: Path) -> None:
        """Test converting textile and printing to stdout."""
        input_file = tmp_path / "input.textile"
        input_file.write_text("h1. Title\n\nThis is *bold* text.")
        
        result = runner.invoke(app, ["convert-textile", str(input_file)])
        
        assert result.exit_code == 0
        assert "# Title" in result.stdout
    
    def test_convert_textile_to_file(self, tmp_path: Path) -> None:
        """Test converting textile and saving to file."""
        input_file = tmp_path / "input.textile"
        input_file.write_text("h2. Section\n\nParagraph text.")
        
        output_file = tmp_path / "output.md"
        
        result = runner.invoke(app, [
            "convert-textile",
            str(input_file),
            "--output", str(output_file),
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "## Section" in content


class TestFetchCommandWithIssues:
    """Tests for fetch command processing issues and wikis."""
    
    @pytest.fixture
    def config_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        """Create a test config file."""
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": str(tmp_path / "output"),
                    "projects": ["proj_a"],
                    "include_subprojects": True,
                }
            ],
            "logging": {"level": "WARNING", "format": "console"},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        return config_file
    
    def test_fetch_with_issues_and_attachments(
        self,
        config_file: Path,
        sample_issue: "IssueMetadata",
        tmp_path: Path,
    ) -> None:
        """Test fetch processes issues with attachments."""
        from redmine_knowledge_agent.models import IssueMetadata, AttachmentInfo, ExtractedContent, ProcessingMethod
        from datetime import datetime
        
        # Create issue with attachment
        issue = IssueMetadata(
            id=1,
            project="proj_a",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test Issue",
            description_textile="Description",
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=100,
                    filename="test.txt",
                    content_type="text/plain",
                    filesize=100,
                    content_url="https://test/att/100",
                )
            ],
        )
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory") as mock_factory_class:
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([issue])
                    mock_client.get_project_wiki_pages.return_value = iter([])
                    mock_client_class.return_value = mock_client
                    
                    mock_factory = MagicMock()
                    mock_factory.process_file.return_value = ExtractedContent(
                        text="Extracted text",
                        processing_method=ProcessingMethod.TEXT_EXTRACT,
                    )
                    mock_factory_class.return_value = mock_factory
                    
                    mock_gen = MagicMock()
                    mock_gen.save_issue.return_value = tmp_path / "1.md"
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    assert result.exit_code == 0
                    mock_client.download_attachment.assert_called()
    
    def test_fetch_attachment_processing_error(
        self,
        config_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test fetch handles attachment processing errors gracefully."""
        from redmine_knowledge_agent.models import IssueMetadata, AttachmentInfo
        from datetime import datetime
        
        issue = IssueMetadata(
            id=2,
            project="proj_a",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test Issue",
            description_textile="Desc",
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=101,
                    filename="test.pdf",
                    content_type="application/pdf",
                    filesize=100,
                    content_url="https://test/att/101",
                )
            ],
        )
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory") as mock_factory_class:
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([issue])
                    mock_client.get_project_wiki_pages.return_value = iter([])
                    # Simulate download error
                    mock_client.download_attachment.side_effect = Exception("Download failed")
                    mock_client_class.return_value = mock_client
                    
                    mock_factory_class.return_value = MagicMock()
                    
                    mock_gen = MagicMock()
                    mock_gen.save_issue.return_value = tmp_path / "2.md"
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    # Should continue despite error
                    assert result.exit_code == 0
    
    def test_fetch_issue_processing_error(
        self,
        config_file: Path,
    ) -> None:
        """Test fetch handles issue processing errors."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.side_effect = Exception("API error")
                mock_client.get_project_wiki_pages.return_value = iter([])
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                
                # Should handle error and continue
                assert "失敗" in result.stdout or result.exit_code == 0
    
    def test_fetch_with_wiki_pages(
        self,
        config_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test fetch processes wiki pages."""
        from redmine_knowledge_agent.models import WikiPageMetadata, AttachmentInfo
        from datetime import datetime
        
        wiki_page = WikiPageMetadata(
            title="TestPage",
            project="proj_a",
            text_textile="h1. Test\n\nContent",
            version=1,
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=200,
                    filename="wiki_att.png",
                    content_type="image/png",
                    filesize=500,
                    content_url="https://test/att/200",
                )
            ],
        )
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory") as mock_factory_class:
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([])
                    mock_client.get_project_wiki_pages.return_value = iter([wiki_page])
                    mock_client_class.return_value = mock_client
                    
                    from redmine_knowledge_agent.models import ExtractedContent, ProcessingMethod
                    mock_factory = MagicMock()
                    mock_factory.process_file.return_value = ExtractedContent(
                        text="OCR text",
                        processing_method=ProcessingMethod.OCR,
                    )
                    mock_factory_class.return_value = mock_factory
                    
                    mock_gen = MagicMock()
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    assert result.exit_code == 0
                    mock_gen.save_wiki_page.assert_called()
    
    def test_fetch_wiki_attachment_error(
        self,
        config_file: Path,
        tmp_path: Path,
    ) -> None:
        """Test fetch handles wiki attachment errors."""
        from redmine_knowledge_agent.models import WikiPageMetadata, AttachmentInfo
        from datetime import datetime
        
        wiki_page = WikiPageMetadata(
            title="TestPage",
            project="proj_a",
            text_textile="Content",
            version=1,
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=201,
                    filename="error.pdf",
                    content_type="application/pdf",
                    filesize=100,
                    content_url="https://test/att/201",
                )
            ],
        )
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([])
                    mock_client.get_project_wiki_pages.return_value = iter([wiki_page])
                    mock_client.download_attachment.side_effect = Exception("Download error")
                    mock_client_class.return_value = mock_client
                    
                    mock_gen = MagicMock()
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    # Should continue despite attachment error
                    assert result.exit_code == 0
    
    def test_fetch_wiki_error(
        self,
        config_file: Path,
    ) -> None:
        """Test fetch handles wiki processing errors."""
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                mock_client = MagicMock()
                mock_client.get_project_issues.return_value = iter([])
                mock_client.get_project_wiki_pages.side_effect = Exception("Wiki error")
                mock_client_class.return_value = mock_client
                
                result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                
                # Should handle wiki error gracefully
                assert result.exit_code == 0


class TestMainEntryPoint:
    """Tests for main entry point."""
    
    def test_main_function(self) -> None:
        """Test main() function exists and is callable."""
        from redmine_knowledge_agent.__main__ import main
        
        # Just verify it's callable
        assert callable(main)
    
    def test_progress_output_every_10_issues(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test progress output is shown every 10 issues."""
        from redmine_knowledge_agent.models import IssueMetadata
        from datetime import datetime
        
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": str(tmp_path / "output"),
                    "projects": ["proj"],
                }
            ],
            "logging": {"level": "WARNING"},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Create 11 issues
        issues = []
        for i in range(11):
            issues.append(IssueMetadata(
                id=i + 1,
                project="proj",
                tracker="Bug",
                status="Open",
                priority="Normal",
                subject=f"Issue {i + 1}",
                description_textile="",
                created_on=datetime.now(),
                updated_on=datetime.now(),
            ))
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory"):
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter(issues)
                    mock_client.get_project_wiki_pages.return_value = iter([])
                    mock_client_class.return_value = mock_client
                    
                    mock_gen = MagicMock()
                    mock_gen.save_issue.return_value = tmp_path / "1.md"
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    assert result.exit_code == 0
                    # Should have progress message for 10 issues
                    assert "已處理 10 個 issues" in result.stdout
    
    def test_attachment_already_exists_skips_download(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that existing attachments are not re-downloaded."""
        from redmine_knowledge_agent.models import IssueMetadata, AttachmentInfo, ExtractedContent, ProcessingMethod
        from datetime import datetime
        
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        output_dir = tmp_path / "output"
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": str(output_dir),
                    "projects": ["proj"],
                }
            ],
            "logging": {"level": "WARNING"},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Create issue with attachment
        issue = IssueMetadata(
            id=1,
            project="proj",
            tracker="Bug",
            status="Open",
            priority="Normal",
            subject="Test",
            description_textile="",
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=100,
                    filename="existing.txt",
                    content_type="text/plain",
                    filesize=100,
                    content_url="https://test/100",
                )
            ],
        )
        
        # Pre-create the attachment file
        att_dir = output_dir / "proj" / "issues" / "attachments" / "00001"
        att_dir.mkdir(parents=True)
        existing_file = att_dir / "existing.txt"
        existing_file.write_text("Already exists")
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory") as mock_factory_class:
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([issue])
                    mock_client.get_project_wiki_pages.return_value = iter([])
                    mock_client_class.return_value = mock_client
                    
                    mock_factory = MagicMock()
                    mock_factory.process_file.return_value = ExtractedContent(
                        text="text",
                        processing_method=ProcessingMethod.TEXT_EXTRACT,
                    )
                    mock_factory_class.return_value = mock_factory
                    
                    mock_gen = MagicMock()
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    assert result.exit_code == 0
                    # Download should NOT be called since file exists
                    mock_client.download_attachment.assert_not_called()
    
    def test_wiki_attachment_already_exists_skips_download(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that existing wiki attachments are not re-downloaded."""
        from redmine_knowledge_agent.models import WikiPageMetadata, AttachmentInfo, ExtractedContent, ProcessingMethod
        from datetime import datetime
        
        monkeypatch.setenv("TEST_API_KEY", "test_key")
        
        output_dir = tmp_path / "output"
        config_data = {
            "redmine": {
                "url": "https://test.redmine.com",
                "api_key": "${TEST_API_KEY}",
            },
            "outputs": [
                {
                    "path": str(output_dir),
                    "projects": ["proj"],
                }
            ],
            "logging": {"level": "WARNING"},
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Create wiki page with attachment
        wiki_page = WikiPageMetadata(
            title="TestPage",
            project="proj",
            text_textile="Content",
            version=1,
            created_on=datetime.now(),
            updated_on=datetime.now(),
            attachments=[
                AttachmentInfo(
                    id=200,
                    filename="existing_wiki.txt",
                    content_type="text/plain",
                    filesize=100,
                    content_url="https://test/200",
                )
            ],
        )
        
        # Pre-create the attachment file
        att_dir = output_dir / "proj" / "wiki" / "attachments"
        att_dir.mkdir(parents=True)
        existing_file = att_dir / "existing_wiki.txt"
        existing_file.write_text("Already exists")
        
        with patch("redmine_knowledge_agent.__main__.RedmineClient") as mock_client_class:
            with patch("redmine_knowledge_agent.__main__.ProcessorFactory") as mock_factory_class:
                with patch("redmine_knowledge_agent.__main__.MarkdownGenerator") as mock_gen_class:
                    mock_client = MagicMock()
                    mock_client.get_project_issues.return_value = iter([])
                    mock_client.get_project_wiki_pages.return_value = iter([wiki_page])
                    mock_client_class.return_value = mock_client
                    
                    mock_factory = MagicMock()
                    mock_factory.process_file.return_value = ExtractedContent(
                        text="text",
                        processing_method=ProcessingMethod.TEXT_EXTRACT,
                    )
                    mock_factory_class.return_value = mock_factory
                    
                    mock_gen = MagicMock()
                    mock_gen_class.return_value = mock_gen
                    
                    result = runner.invoke(app, ["fetch", "--config", str(config_file)])
                    
                    assert result.exit_code == 0
                    # Download should NOT be called since file exists
                    mock_client.download_attachment.assert_not_called()
