"""Additional tests to increase coverage for uncovered branches."""

from datetime import datetime, timezone
import httpx

import pytest

from redmine_knowledge_agent.__main__ import print_issues_summary
from redmine_knowledge_agent.logging import create_logger
from redmine_knowledge_agent.models import (
    Issue,
    Project,
    Tracker,
    Status,
    Priority,
    User,
    Attachment,
)
from redmine_knowledge_agent.client import RedmineClient
from redmine_knowledge_agent.config import Settings, RedmineConfig
from redmine_knowledge_agent.exceptions import ConnectionError


def test_print_issues_summary_with_attachments(capsys: pytest.CaptureFixture) -> None:
    """Print summary when issue has attachments and assigned_to."""
    issue = Issue(
        id=10,
        subject="Issue with attachment",
        description="desc",
        project=Project(id=1, name="P"),
        tracker=Tracker(id=1, name="Bug"),
        status=Status(id=1, name="Open"),
        priority=Priority(id=1, name="High"),
        author=User(id=1, name="Alice"),
        assigned_to=User(id=2, name="Bob"),
        created_on=datetime.now(tz=timezone.utc),
        updated_on=datetime.now(tz=timezone.utc),
        attachments=[
            Attachment(
                id=1,
                filename="a.pdf",
                filesize=100,
                content_type="application/pdf",
                content_url="https://redmine.local/attachments/1/a.pdf",
                created_on=datetime.now(tz=timezone.utc),
                author=User(id=1, name="Alice"),
            )
        ],
    )

    print_issues_summary([issue])
    out = capsys.readouterr().out
    assert "指派給" in out
    assert "附件數" in out


def test_create_logger_returns_logger() -> None:
    logger = create_logger("test")
    assert logger is not None


def test_get_issues_with_tracker_param(respx_mock, sample_issues_list_response):
    config = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(config)

    route = respx_mock.get("https://redmine.test.local/issues.json").mock(
        return_value=httpx.Response(200, json={"issues": [], "total_count": 0, "offset": 0, "limit": 25})
    )

    client.get_issues(tracker_id=5)
    assert route.called
    assert "tracker_id=5" in str(route.calls[0].request.url)


def test_get_issue_connection_error(respx_mock):
    config = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(config)

    respx_mock.get("https://redmine.test.local/issues/123.json").mock(side_effect=httpx.ConnectError("conn refused"))

    with pytest.raises(ConnectionError):
        client.get_issue(123)


def test_handle_response_raises_http_error():
    config = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(config)

    req = httpx.Request("GET", "https://redmine.test.local/issues.json")
    resp = httpx.Response(500, request=req)

    with pytest.raises(httpx.HTTPStatusError):
        client._handle_response_error(resp)


def test_settings_api_key_validator(monkeypatch):
    # provide required url but invalid api key
    monkeypatch.setenv("REDMINE_URL", "https://redmine.test.local")
    monkeypatch.setenv("REDMINE_API_KEY", "invalid!@#")
    with pytest.raises(ValueError):
        Settings()
