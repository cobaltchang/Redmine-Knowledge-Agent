"""Main entry point for Redmine Knowledge Agent.

This module provides the CLI interface and main execution logic.
"""

import sys
from typing import Optional

import structlog

from redmine_knowledge_agent.client import RedmineClient
from redmine_knowledge_agent.config import Settings, RedmineConfig
from redmine_knowledge_agent.exceptions import (
    RedmineKnowledgeAgentError,
    ConfigurationError,
)
from redmine_knowledge_agent.models import IssueList


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


def fetch_all_issues(
    client: RedmineClient,
    project_id: Optional[int] = None,
    status_id: Optional[str] = "open",
    batch_size: int = 25,
) -> list:
    """Fetch all issues with pagination.
    
    Args:
        client: The Redmine client to use.
        project_id: Optional project ID filter.
        status_id: Status filter (default: "open").
        batch_size: Number of issues per request.
        
    Returns:
        List of all matching issues.
    """
    all_issues = []
    offset = 0
    
    while True:
        logger.info(
            "Fetching issues",
            offset=offset,
            limit=batch_size,
            project_id=project_id,
        )
        
        issue_list = client.get_issues(
            project_id=project_id,
            status_id=status_id,
            offset=offset,
            limit=batch_size,
        )
        
        all_issues.extend(issue_list.issues)
        
        logger.info(
            "Fetched issues batch",
            count=len(issue_list.issues),
            total_so_far=len(all_issues),
            total_available=issue_list.total_count,
        )
        
        if not issue_list.has_more:
            break
        
        offset = issue_list.next_offset
    
    return all_issues


def print_issues_summary(issues: list) -> None:
    """Print a summary of fetched issues.
    
    Args:
        issues: List of Issue objects to summarize.
    """
    print("\n" + "=" * 60)
    print(f"擷取到 {len(issues)} 個 Issues")
    print("=" * 60 + "\n")
    
    for issue in issues:
        print(f"#{issue.id}: {issue.subject}")
        print(f"  專案: {issue.project.name}")
        print(f"  狀態: {issue.status.name}")
        print(f"  優先級: {issue.priority.name}")
        print(f"  建立者: {issue.author.name}")
        if issue.assigned_to:
            print(f"  指派給: {issue.assigned_to.name}")
        if issue.attachments:
            print(f"  附件數: {len(issue.attachments)}")
        print()


def main() -> int:
    """Main entry point for the application.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        # Load settings from environment
        logger.info("Loading configuration...")
        settings = Settings()
        
        # Create Redmine client
        config = settings.create_redmine_config()
        
        logger.info(
            "Connecting to Redmine",
            url=str(settings.redmine_url),
        )
        
        with RedmineClient(config, timeout=settings.request_timeout) as client:
            # Fetch all open issues
            issues = fetch_all_issues(
                client,
                batch_size=settings.batch_size,
            )
            
            # Print summary
            print_issues_summary(issues)
            
        logger.info("Completed successfully")
        return 0
        
    except ConfigurationError as e:
        logger.error("Configuration error", error=str(e))
        print(f"\n錯誤: 設定錯誤 - {e}", file=sys.stderr)
        print("請確認 .env 檔案已正確設定。", file=sys.stderr)
        return 1
        
    except RedmineKnowledgeAgentError as e:
        logger.error("Application error", error=str(e), error_code=e.error_code)
        print(f"\n錯誤: {e}", file=sys.stderr)
        return 1
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print("\n已取消執行。", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
