"""CLI entry point for Redmine Knowledge Agent.

Provides commands for fetching issues, wiki pages, and listing projects.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

import structlog
import typer

from .client import RedmineClient
from .config import AppConfig
from .generator import MarkdownGenerator
from .processors import ProcessorFactory

if TYPE_CHECKING:
    from .models import ExtractedContent

# Constants
DESCRIPTION_TRUNCATE_LENGTH = 60

app = typer.Typer(
    name="redmine-ka",
    help="Redmine Knowledge Agent - Extract knowledge from Redmine to Markdown",
)

logger = structlog.get_logger(__name__)


class FetchMode(str, Enum):
    """Fetch mode for the fetch command."""

    FULL = "full"
    INCREMENTAL = "incremental"


def setup_logging(level: str = "INFO", log_format: str = "console") -> None:
    """Configure structlog logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        log_format: Output format (json or console).

    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
    )

    processors: list[Callable[..., Any]] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


@app.command()
def list_projects(
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ],
) -> None:
    """List all accessible Redmine projects."""
    app_config = AppConfig.from_yaml(config)
    setup_logging(app_config.logging.level, app_config.logging.format)

    client = RedmineClient(app_config.redmine)
    projects = client.list_projects()

    typer.echo(f"\n找到 {len(projects)} 個專案:\n")
    for proj in projects:
        typer.echo(f"  [{proj['identifier']}] {proj['name']}")
        if proj.get("description"):
            desc = (
                proj["description"][:DESCRIPTION_TRUNCATE_LENGTH] + "..."
                if len(proj["description"]) > DESCRIPTION_TRUNCATE_LENGTH
                else proj["description"]
            )
            typer.echo(f"      {desc}")


@app.command()
def fetch(  # noqa: PLR0912 - complexity justified by CLI command workflow
    config: Annotated[
        Path,
        typer.Option("--config", "-c", help="Path to config YAML file"),
    ],
    mode: Annotated[  # noqa: ARG001 - reserved for incremental mode (not yet implemented)
        FetchMode,
        typer.Option("--mode", "-m", help="Fetch mode"),
    ] = FetchMode.FULL,
    projects: Annotated[
        str | None,
        typer.Option("--projects", "-p", help="Comma-separated project identifiers"),
    ] = None,
    skip_attachments: Annotated[
        bool,
        typer.Option("--skip-attachments", help="Skip attachment processing"),
    ] = False,
    skip_wiki: Annotated[
        bool,
        typer.Option("--skip-wiki", help="Skip wiki page fetching"),
    ] = False,
) -> None:
    """Fetch issues and wiki pages from Redmine and generate Markdown files."""
    app_config = AppConfig.from_yaml(config)
    setup_logging(app_config.logging.level, app_config.logging.format)

    client = RedmineClient(app_config.redmine)
    processor_factory = ProcessorFactory(app_config.processing)

    # Filter outputs if specific projects requested
    outputs_to_process = app_config.outputs
    if projects:
        project_list = [p.strip() for p in projects.split(",")]
        outputs_to_process = [
            out for out in app_config.outputs if any(p in project_list for p in out.projects)
        ]

    total_issues = 0
    total_wiki = 0

    for output_config in outputs_to_process:
        output_path = output_config.get_output_path()
        generator = MarkdownGenerator(output_path)

        for project_id in output_config.projects:
            typer.echo(f"\n處理專案: {project_id}")

            # Fetch issues
            try:
                issue_count = 0
                for issue in client.get_project_issues(
                    project_id,
                    include_subprojects=output_config.include_subprojects,
                ):
                    # Process attachments
                    extracted_contents: dict[int, ExtractedContent] = {}

                    if not skip_attachments and issue.attachments:
                        for att in issue.attachments:
                            try:
                                # Download attachment
                                att_dir = (
                                    output_path
                                    / project_id
                                    / "issues"
                                    / "attachments"
                                    / f"{issue.id:05d}"
                                )
                                att_path = att_dir / att.filename

                                if not att_path.exists():
                                    client.download_attachment(att.content_url, att_path)

                                # Process attachment
                                extracted = processor_factory.process_file(
                                    att_path,
                                    att.content_type,
                                )
                                extracted_contents[att.id] = extracted

                            except (OSError, ValueError) as e:
                                logger.warning(
                                    "Failed to process attachment",
                                    issue_id=issue.id,
                                    filename=att.filename,
                                    error=str(e),
                                )

                    # Generate markdown
                    generator.save_issue(issue, extracted_contents)
                    issue_count += 1

                    if issue_count % 10 == 0:
                        typer.echo(f"  已處理 {issue_count} 個 issues...")

                total_issues += issue_count
                typer.echo(f"  完成: {issue_count} 個 issues")

            except (OSError, RuntimeError) as e:
                logger.exception(
                    "Failed to process project issues", project=project_id, error=str(e)
                )
                typer.echo(f"  ❌ 處理 issues 失敗: {e}", err=True)

            # Fetch wiki pages
            if not skip_wiki:
                try:
                    wiki_count = 0
                    for wiki_page in client.get_project_wiki_pages(project_id):
                        # Process attachments
                        extracted_contents = {}

                        if not skip_attachments and wiki_page.attachments:  # pragma: no branch
                            for att in wiki_page.attachments:
                                try:
                                    att_dir = output_path / project_id / "wiki" / "attachments"
                                    att_path = att_dir / att.filename

                                    if not att_path.exists():  # pragma: no branch
                                        client.download_attachment(att.content_url, att_path)

                                    extracted = processor_factory.process_file(
                                        att_path,
                                        att.content_type,
                                    )
                                    extracted_contents[att.id] = extracted

                                except (OSError, ValueError) as e:
                                    logger.warning(
                                        "Failed to process wiki attachment",
                                        page=wiki_page.title,
                                        filename=att.filename,
                                        error=str(e),
                                    )

                        generator.save_wiki_page(wiki_page, extracted_contents)
                        wiki_count += 1

                    total_wiki += wiki_count
                    typer.echo(f"  完成: {wiki_count} 個 wiki 頁面")

                except (OSError, RuntimeError) as e:
                    logger.exception("Failed to process wiki", project=project_id, error=str(e))

    typer.echo(f"\n✅ 完成! 共處理 {total_issues} 個 issues, {total_wiki} 個 wiki 頁面")


@app.command()
def convert_textile(
    input_file: Annotated[
        Path,
        typer.Argument(help="Input file with Textile content"),
    ],
    output_file: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Output file (default: stdout)"),
    ] = None,
) -> None:
    """Convert a Textile file to Markdown."""
    from .converter import textile_to_markdown  # noqa: PLC0415 - deferred import for CLI perf

    content = input_file.read_text(encoding="utf-8")
    markdown = textile_to_markdown(content)

    if output_file:
        output_file.write_text(markdown, encoding="utf-8")
        typer.echo(f"已轉換並儲存至: {output_file}")
    else:
        typer.echo(markdown)


def main() -> None:  # pragma: no cover
    """Main entry point."""
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
