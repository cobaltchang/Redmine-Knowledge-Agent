"""Textile to Markdown converter.

Converts Redmine Textile markup to Markdown format.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from re import Match


class TextileConverter:
    """Converts Textile markup to Markdown.

    Handles common Textile syntax used in Redmine, including:
    - Headers (h1., h2., etc.)
    - Bold, italic, underline, strikethrough
    - Links and images
    - Lists (ordered and unordered)
    - Code blocks and inline code
    - Tables
    - Blockquotes
    """

    def __init__(self, attachment_path_prefix: str = "./attachments") -> None:
        """Initialize the converter.

        Args:
            attachment_path_prefix: Path prefix for attachment references.

        """
        self.attachment_path_prefix = attachment_path_prefix

    def convert(self, textile: str | None) -> str:
        """Convert Textile markup to Markdown.

        Args:
            textile: Textile formatted text.

        Returns:
            Markdown formatted text.

        """
        if not textile:
            return ""

        text = textile

        # Apply conversions in order
        # NOTE: Order matters!
        # - Tables must be BEFORE italic (_.header uses underscore)
        # - Ordered lists must be BEFORE headers (both use #, but Textile headers use h1.)
        # - Code blocks should be first to protect code content
        conversions: list[Callable[[str], str]] = [
            self._convert_code_blocks,
            self._convert_tables,  # BEFORE italic - _.header uses underscore
            self._convert_ordered_lists,  # BEFORE headers - converts # list items
            self._convert_headers,  # Converts h1., h2., etc.
            self._convert_bold,
            self._convert_italic,
            self._convert_underline,
            self._convert_strikethrough,
            self._convert_inline_code,
            self._convert_links,
            self._convert_images,
            self._convert_unordered_lists,
            self._convert_blockquotes,
            self._convert_horizontal_rules,
            self._cleanup,
        ]

        for conversion in conversions:
            text = conversion(text)

        return text.strip()

    def _convert_headers(self, text: str) -> str:
        """Convert Textile headers to Markdown.

        h1. Title -> # Title
        h2. Title -> ## Title

        Note: This must run before _convert_ordered_lists to avoid conflicts.
        """
        for level in range(1, 7):
            pattern = rf"^h{level}\.\s+(.+)$"
            replacement = "#" * level + r" \1"
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        return text

    def _convert_bold(self, text: str) -> str:
        """Convert Textile bold to Markdown.

        *bold* -> **bold**
        """
        # Textile uses single asterisks for bold, Markdown uses double
        # Be careful not to match list items
        return re.sub(r"(?<!\*)\*(?!\*)(\S.*?\S|\S)\*(?!\*)", r"**\1**", text)

    def _convert_italic(self, text: str) -> str:
        """Convert Textile italic to Markdown.

        _italic_ -> *italic*
        """
        return re.sub(r"(?<!_)_(?!_)(\S.*?\S|\S)_(?!_)", r"*\1*", text)

    def _convert_underline(self, text: str) -> str:
        """Convert Textile underline to Markdown (using HTML).

        +underline+ -> <u>underline</u>
        """
        return re.sub(r"\+([^+]+)\+", r"<u>\1</u>", text)

    def _convert_strikethrough(self, text: str) -> str:
        """Convert Textile strikethrough to Markdown.

        -deleted- -> ~~deleted~~
        """
        # Avoid matching horizontal rules and list items
        return re.sub(r"(?<!-)-(?!-)(\S.*?\S|\S)-(?!-)", r"~~\1~~", text)

    def _convert_inline_code(self, text: str) -> str:
        """Convert Textile inline code to Markdown.

        @code@ -> `code`
        """
        return re.sub(r"@([^@\n]+)@", r"`\1`", text)

    def _convert_code_blocks(self, text: str) -> str:
        """Convert Textile code blocks to Markdown.

        <pre><code class="python">
        code
        </code></pre>

        ->

        ```python
        code
        ```

        Also handles:
        <pre>
        code
        </pre>
        """

        # Code blocks with language
        def replace_with_lang(match: Match[str]) -> str:
            lang = match.group(1) or ""
            code = match.group(2)
            return f"```{lang}\n{code.strip()}\n```"

        text = re.sub(
            r"<pre><code(?:\s+class=[\"']?(\w+)[\"']?)?>(.*?)</code></pre>",
            replace_with_lang,
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Plain pre blocks
        return re.sub(
            r"<pre>(.*?)</pre>",
            r"```\n\1\n```",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def _convert_links(self, text: str) -> str:
        """Convert Textile links to Markdown.

        "link text":http://example.com -> [link text](http://example.com)
        [[wiki_page]] -> [wiki_page](wiki_page)
        [[wiki_page|display text]] -> [display text](wiki_page)
        """
        # External links: "text":url
        text = re.sub(
            r'"([^"]+)":(\S+)',
            r"[\1](\2)",
            text,
        )

        # Wiki links with display text: [[page|text]]
        text = re.sub(
            r"\[\[([^\]|]+)\|([^\]]+)\]\]",
            r"[\2](\1)",
            text,
        )

        # Wiki links: [[page]]
        return re.sub(
            r"\[\[([^\]]+)\]\]",
            r"[\1](\1)",
            text,
        )

    def _convert_images(self, text: str) -> str:
        """Convert Textile images to Markdown.

        !image.png! -> ![image.png](./attachments/image.png)
        !image.png(alt text)! -> ![alt text](./attachments/image.png)
        !http://example.com/image.png! -> ![image](http://example.com/image.png)
        """

        def replace_image_with_alt(match: Match[str]) -> str:
            src = match.group(1)
            alt = match.group(2)

            # Check if it's a URL
            if src.startswith(("http://", "https://")):
                return f"![{alt}]({src})"

            # Local attachment
            return f"![{alt}]({self.attachment_path_prefix}/{src})"

        def replace_image_simple(match: Match[str]) -> str:
            src = match.group(1)

            # Check if it's a URL
            if src.startswith(("http://", "https://")):
                return f"![image]({src})"

            # Local attachment
            return f"![{src}]({self.attachment_path_prefix}/{src})"

        # Image with alt text: !image.png(alt)!
        text = re.sub(
            r"!([^!\(\)]+)\(([^)]+)\)!",
            replace_image_with_alt,
            text,
        )

        # Image without alt text: !image.png!
        return re.sub(
            r"!([^!\s]+)!",
            replace_image_simple,
            text,
        )

    def _convert_unordered_lists(self, text: str) -> str:
        """Convert Textile unordered lists to Markdown.

        * item -> - item
        ** nested -> - nested (with indentation)
        """
        lines = text.split("\n")
        result: list[str] = []

        for line in lines:
            match = re.match(r"^(\*+)\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                content = match.group(2)
                indent = "  " * (level - 1)
                result.append(f"{indent}- {content}")
            else:
                result.append(line)

        return "\n".join(result)

    def _convert_ordered_lists(self, text: str) -> str:
        """Convert Textile ordered lists to Markdown.

        # item -> 1. item
        ## nested -> (indented) 1. nested

        Note: This runs BEFORE headers are converted, so Textile ordered lists
        (# item) are processed here. Textile headers use h1., h2., etc.
        """
        lines = text.split("\n")
        result: list[str] = []

        for line in lines:
            # Match Textile ordered list: # item, ## nested item, etc.
            match = re.match(r"^(#+)\s+(.+)$", line)
            if match:
                hashes = match.group(1)
                content = match.group(2)
                level = len(hashes)
                indent = "  " * (level - 1)
                result.append(f"{indent}1. {content}")
            else:
                result.append(line)

        return "\n".join(result)

    def _convert_blockquotes(self, text: str) -> str:
        """Convert Textile blockquotes to Markdown.

        bq. quote -> > quote
        """
        return re.sub(r"^bq\.\s+(.+)$", r"> \1", text, flags=re.MULTILINE)

    def _convert_tables(self, text: str) -> str:
        """Convert Textile tables to Markdown.

        |_.header|_.header|
        |cell|cell|

        ->

        | header | header |
        | --- | --- |
        | cell | cell |
        """
        lines = text.split("\n")
        result: list[str] = []
        in_table = False
        header_added = False

        for line in lines:
            if re.match(r"^\|", line):
                # Process table row
                cells = re.split(r"\|", line.strip("|"))
                cells = [c.strip() for c in cells]

                # Check if header row (starts with _.)
                is_header = any(c.startswith("_.") for c in cells)

                if is_header:
                    # Remove _. prefix
                    cells = [c[2:].strip() if c.startswith("_.") else c for c in cells]
                    result.append("| " + " | ".join(cells) + " |")
                    result.append("| " + " | ".join(["---"] * len(cells)) + " |")
                    header_added = True
                else:
                    if not in_table and not header_added:
                        # Add a dummy header if table starts without headers
                        result.append("| " + " | ".join(["---"] * len(cells)) + " |")
                        result.append("| " + " | ".join(["---"] * len(cells)) + " |")
                    result.append("| " + " | ".join(cells) + " |")

                in_table = True
            else:
                in_table = False
                header_added = False
                result.append(line)

        return "\n".join(result)

    def _convert_horizontal_rules(self, text: str) -> str:
        """Convert Textile horizontal rules to Markdown.

        --- -> ---
        """
        # Textile uses ---, Markdown also uses ---
        # Just ensure it's on its own line
        return re.sub(r"^---+$", "---", text, flags=re.MULTILINE)

    def _cleanup(self, text: str) -> str:
        """Clean up extra whitespace and formatting issues."""
        # Remove excessive blank lines
        return re.sub(r"\n{3,}", "\n\n", text)


def textile_to_markdown(
    textile: str,
    attachment_path_prefix: str = "./attachments",
) -> str:
    """Convert Textile markup to Markdown.

    This is a convenience function for simple conversions.

    Args:
        textile: Textile formatted text.
        attachment_path_prefix: Path prefix for attachment references.

    Returns:
        Markdown formatted text.

    """
    converter = TextileConverter(attachment_path_prefix)
    return converter.convert(textile)
