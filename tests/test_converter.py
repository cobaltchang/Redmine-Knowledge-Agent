"""Tests for Textile to Markdown converter."""
from __future__ import annotations

import pytest

from redmine_knowledge_agent.converter import TextileConverter, textile_to_markdown


class TestTextileConverter:
    """Tests for TextileConverter."""
    
    @pytest.fixture
    def converter(self) -> TextileConverter:
        """Create a converter instance."""
        return TextileConverter()
    
    def test_empty_input(self, converter: TextileConverter) -> None:
        """Test with empty input."""
        assert converter.convert("") == ""
        assert converter.convert(None) == ""  # type: ignore
    
    def test_headers(self, converter: TextileConverter) -> None:
        """Test header conversion."""
        assert converter.convert("h1. Title") == "# Title"
        assert converter.convert("h2. Subtitle") == "## Subtitle"
        assert converter.convert("h3. Section") == "### Section"
        
        # Multiple headers
        text = "h1. Main\n\nh2. Sub"
        result = converter.convert(text)
        assert "# Main" in result
        assert "## Sub" in result
    
    def test_bold(self, converter: TextileConverter) -> None:
        """Test bold text conversion."""
        assert "**bold**" in converter.convert("This is *bold* text")
    
    def test_italic(self, converter: TextileConverter) -> None:
        """Test italic text conversion."""
        assert "*italic*" in converter.convert("This is _italic_ text")
    
    def test_underline(self, converter: TextileConverter) -> None:
        """Test underline conversion (to HTML)."""
        result = converter.convert("This is +underlined+ text")
        assert "<u>underlined</u>" in result
    
    def test_strikethrough(self, converter: TextileConverter) -> None:
        """Test strikethrough conversion."""
        result = converter.convert("This is -deleted- text")
        assert "~~deleted~~" in result
    
    def test_inline_code(self, converter: TextileConverter) -> None:
        """Test inline code conversion."""
        result = converter.convert("Use @code@ here")
        assert "`code`" in result
    
    def test_code_blocks(self, converter: TextileConverter) -> None:
        """Test code block conversion."""
        textile = '<pre><code class="python">print("hello")</code></pre>'
        result = converter.convert(textile)
        assert "```python" in result
        assert 'print("hello")' in result
        assert "```" in result
    
    def test_code_blocks_no_language(self, converter: TextileConverter) -> None:
        """Test code block without language."""
        textile = "<pre>some code</pre>"
        result = converter.convert(textile)
        assert "```" in result
        assert "some code" in result
    
    def test_links_external(self, converter: TextileConverter) -> None:
        """Test external link conversion."""
        result = converter.convert('"Google":https://google.com')
        assert "[Google](https://google.com)" in result
    
    def test_links_wiki(self, converter: TextileConverter) -> None:
        """Test wiki link conversion."""
        # Simple wiki link
        result = converter.convert("See [[WikiPage]]")
        assert "[WikiPage](WikiPage)" in result
        
        # Wiki link with display text
        result = converter.convert("See [[WikiPage|Display Text]]")
        assert "[Display Text](WikiPage)" in result
    
    def test_images_local(self, converter: TextileConverter) -> None:
        """Test local image conversion."""
        result = converter.convert("!image.png!")
        assert "![image.png](./attachments/image.png)" in result
    
    def test_images_with_alt(self, converter: TextileConverter) -> None:
        """Test image with alt text."""
        result = converter.convert("!image.png(Alt text)!")
        assert "![Alt text](./attachments/image.png)" in result
    
    def test_images_url(self, converter: TextileConverter) -> None:
        """Test external image URL."""
        result = converter.convert("!https://example.com/image.png!")
        assert "![image](https://example.com/image.png)" in result
    
    def test_custom_attachment_prefix(self) -> None:
        """Test custom attachment path prefix."""
        converter = TextileConverter(attachment_path_prefix="../assets")
        result = converter.convert("!photo.jpg!")
        assert "![photo.jpg](../assets/photo.jpg)" in result
    
    def test_unordered_lists(self, converter: TextileConverter) -> None:
        """Test unordered list conversion."""
        textile = "* Item 1\n* Item 2\n** Nested item"
        result = converter.convert(textile)
        assert "- Item 1" in result
        assert "- Item 2" in result
        assert "  - Nested item" in result
    
    def test_ordered_lists(self, converter: TextileConverter) -> None:
        """Test ordered list conversion."""
        textile = "# First\n# Second\n## Nested"
        result = converter.convert(textile)
        assert "1. First" in result
        assert "1. Second" in result
        assert "  1. Nested" in result
    
    def test_blockquotes(self, converter: TextileConverter) -> None:
        """Test blockquote conversion."""
        result = converter.convert("bq. This is a quote")
        assert "> This is a quote" in result
    
    def test_tables_with_headers(self, converter: TextileConverter) -> None:
        """Test table with headers."""
        textile = "|_.Header 1|_.Header 2|\n|Cell 1|Cell 2|"
        result = converter.convert(textile)
        assert "| Header 1 | Header 2 |" in result
        assert "| --- | --- |" in result
        assert "| Cell 1 | Cell 2 |" in result
    
    def test_tables_without_headers(self, converter: TextileConverter) -> None:
        """Test table without explicit headers."""
        textile = "|Cell 1|Cell 2|\n|Cell 3|Cell 4|"
        result = converter.convert(textile)
        assert "|" in result
    
    def test_horizontal_rules(self, converter: TextileConverter) -> None:
        """Test horizontal rule conversion."""
        result = converter.convert("---")
        assert "---" in result
    
    def test_complex_document(self, converter: TextileConverter) -> None:
        """Test a complex document with multiple elements."""
        textile = """h1. Document Title

h2. Introduction

This is a paragraph with *bold* and _italic_ text.

h2. Features

* Feature 1
* Feature 2
** Sub-feature

h2. Code Example

<pre><code class="python">
def hello():
    print("Hello, World!")
</code></pre>

h2. Links

See "our website":https://example.com for more info.
"""
        result = converter.convert(textile)
        
        assert "# Document Title" in result
        assert "## Introduction" in result
        assert "**bold**" in result
        assert "*italic*" in result
        assert "- Feature 1" in result
        assert "```python" in result
        assert "[our website](https://example.com)" in result
    
    def test_cleanup_excessive_newlines(self, converter: TextileConverter) -> None:
        """Test that excessive newlines are cleaned up."""
        textile = "Line 1\n\n\n\n\nLine 2"
        result = converter.convert(textile)
        assert "\n\n\n" not in result


class TestTextileToMarkdownFunction:
    """Tests for textile_to_markdown convenience function."""
    
    def test_basic_conversion(self) -> None:
        """Test basic conversion via function."""
        result = textile_to_markdown("h1. Title")
        assert "# Title" in result
    
    def test_custom_prefix(self) -> None:
        """Test custom attachment prefix."""
        result = textile_to_markdown("!img.png!", "./images")
        assert "![img.png](./images/img.png)" in result


class TestTextileConverterEdgeCases:
    """Additional edge case tests for TextileConverter."""
    
    @pytest.fixture
    def converter(self) -> TextileConverter:
        """Create a TextileConverter."""
        return TextileConverter()
    
    def test_convert_empty_string(self, converter: TextileConverter) -> None:
        """Test converting empty string."""
        result = converter.convert("")
        assert result == ""
    
    def test_image_with_url(self, converter: TextileConverter) -> None:
        """Test image with full URL is preserved."""
        textile = "!https://example.com/img.png!"
        result = converter.convert(textile)
        assert "![image](https://example.com/img.png)" in result
    
    def test_image_with_http_url(self, converter: TextileConverter) -> None:
        """Test image with http URL is preserved."""
        textile = "!http://example.com/img.png!"
        result = converter.convert(textile)
        assert "![image](http://example.com/img.png)" in result
    
    def test_image_with_alt_text_and_url(self, converter: TextileConverter) -> None:
        """Test image with alt text and URL."""
        textile = "!https://example.com/img.png(Alt text)!"
        result = converter.convert(textile)
        assert "![Alt text](https://example.com/img.png)" in result
