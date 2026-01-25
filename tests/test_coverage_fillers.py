import httpx
import pytest
import types

from redmine_knowledge_agent import __main__ as main_mod
from redmine_knowledge_agent.client import RedmineClient
from redmine_knowledge_agent.config import RedmineConfig, Settings
from redmine_knowledge_agent.exceptions import ConfigurationError
from redmine_knowledge_agent.models import Project, Issue, IssueList, Attachment, User, Tracker, Status, Priority


def test_project_name_validator_empty():
    with pytest.raises(ValueError):
        Project(id=1, name="   ")


def test_issue_from_api_response_with_attachment_and_assigned():
    data = {
        "id": 10,
        "subject": "Subj",
        "description": "Desc",
        "project": {"id": 1, "name": "P"},
        "tracker": {"id": 2, "name": "Bug"},
        "status": {"id": 3, "name": "New"},
        "priority": {"id": 4, "name": "High"},
        "author": {"id": 5, "name": "Alice"},
        "assigned_to": {"id": 6, "name": "Bob"},
        "created_on": "2020-01-01T00:00:00Z",
        "updated_on": "2020-01-02T00:00:00Z",
        "attachments": [
            {
                "id": 100,
                "filename": "img.png",
                "filesize": 1234,
                "content_type": "image/png",
                "content_url": "https://ex/1",
                "created_on": "2020-01-01T00:00:00Z",
                "author": {"id": 5, "name": "Alice"},
            }
        ],
    }

    issue = Issue.from_api_response(data)
    assert issue.assigned_to is not None
    assert len(issue.attachments) == 1
    att = issue.attachments[0]
    assert att.is_image
    assert not att.is_pdf


def test_issue_list_iteration_and_len():
    # create two simple issues from the same structure
    data = {
        "issues": [
            {"id": 1, "subject": "A", "project": {"id":1,"name":"P"}, "tracker": {"id":1,"name":"T"}, "status": {"id":1,"name":"S"}, "priority": {"id":1,"name":"Low"}, "author": {"id":1,"name":"A"}, "created_on":"2020-01-01T00:00:00Z", "updated_on":"2020-01-01T00:00:00Z"},
            {"id": 2, "subject": "B", "project": {"id":1,"name":"P"}, "tracker": {"id":1,"name":"T"}, "status": {"id":1,"name":"S"}, "priority": {"id":1,"name":"Low"}, "author": {"id":1,"name":"A"}, "created_on":"2020-01-01T00:00:00Z", "updated_on":"2020-01-01T00:00:00Z"},
        ],
        "total_count": 2,
        "offset": 0,
        "limit": 25,
    }

    il = IssueList.from_api_response(data)
    assert len(il) == 2
    ids = [i.id for i in il]
    assert ids == [1, 2]


def test_client_handle_response_raises_on_500():
    cfg = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(cfg)

    resp = httpx.Response(500, request=httpx.Request("GET", "https://redmine.test.local/issues.json"))
    with pytest.raises(httpx.HTTPStatusError):
        client._handle_response_error(resp)


def test_settings_required_fields_raise(monkeypatch):
    # Ensure env is clean so that before-model validator raises ConfigurationError
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        Settings()


def test_main_handles_configuration_error(monkeypatch, capsys):
    # Make Settings constructor raise ConfigurationError
    def fake_Settings():
        raise ConfigurationError("missing")

    monkeypatch.setattr(main_mod, "Settings", fake_Settings)
    rc = main_mod.main()
    assert rc == 1


def test_main_handles_keyboard_interrupt(monkeypatch):
    class FakeSettings:
        def __init__(self):
            self.redmine_url = "https://redmine.test.local"
            self.request_timeout = 1
            self.batch_size = 10

        def create_redmine_config(self):
            return RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            raise KeyboardInterrupt()

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(main_mod, "Settings", FakeSettings)
    monkeypatch.setattr(main_mod, "RedmineClient", FakeClient)

    rc = main_mod.main()
    assert rc == 130


def test_main_handles_application_error(monkeypatch):
    class FakeSettings:
        def __init__(self):
            self.redmine_url = "https://redmine.test.local"
            self.request_timeout = 1
            self.batch_size = 10

        def create_redmine_config(self):
            return RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get_issues(self, *a, **k):
            from redmine_knowledge_agent.exceptions import RedmineKnowledgeAgentError

            raise RedmineKnowledgeAgentError("boom")

    monkeypatch.setattr(main_mod, "Settings", FakeSettings)
    monkeypatch.setattr(main_mod, "RedmineClient", FakeClient)

    rc = main_mod.main()
    assert rc == 1


def test_print_issues_summary_with_assigned_and_attachments(capsys):
    # Build minimal issue with assigned_to and attachments
    issue = Issue(
        id=1,
        subject="s",
        project=Project(id=1, name="P"),
        tracker=Tracker(id=1, name="T"),
        status=Status(id=1, name="S"),
        priority=Priority(id=1, name="Low"),
        author=User(id=1, name="A"),
        assigned_to=User(id=2, name="B"),
        created_on="2020-01-01T00:00:00Z",
        updated_on="2020-01-01T00:00:00Z",
        attachments=[
            Attachment(id=1, filename="f", filesize=1, content_type="application/pdf", content_url="u", created_on="2020-01-01T00:00:00Z", author=User(id=1, name="A"))
        ],
    )

    main_mod.print_issues_summary([issue])
    out = capsys.readouterr().out
    assert "指派給" in out
    assert "附件數" in out


def test_settings_api_key_invalid_raises_valueerror():
    with pytest.raises(ValueError):
        Settings.validate_api_key_format("bad key!")


def test_issue_from_api_response_without_assigned_to():
    data = {
        "id": 11,
        "subject": "NoAssign",
        "project": {"id": 1, "name": "P"},
        "tracker": {"id": 2, "name": "Bug"},
        "status": {"id": 3, "name": "New"},
        "priority": {"id": 4, "name": "High"},
        "author": {"id": 5, "name": "Alice"},
        "created_on": "2020-01-01T00:00:00Z",
        "updated_on": "2020-01-02T00:00:00Z",
    }

    issue = Issue.from_api_response(data)
    assert issue.assigned_to is None


def test_print_issues_summary_empty(capsys):
    main_mod.print_issues_summary([])
    out = capsys.readouterr().out
    assert "擷取到 0 個 Issues" in out


def test_settings_missing_api_key_only(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "https://redmine.test.local")
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        Settings()


def test_attachment_is_pdf_property():
    att = Attachment(id=1, filename="a.pdf", filesize=10, content_type="application/pdf", content_url="u", created_on="2020-01-01T00:00:00Z", author=User(id=1, name="A"))
    assert att.is_pdf and not att.is_image


def test_get_issue_with_includes_param(respx_mock):
    cfg = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(cfg)

    body = {
        "issue": {
            "id": 42,
            "subject": "s",
            "project": {"id":1,"name":"P"},
            "tracker": {"id":1,"name":"T"},
            "status": {"id":1,"name":"S"},
            "priority": {"id":1,"name":"Low"},
            "author": {"id":1,"name":"A"},
            "created_on": "2020-01-01T00:00:00Z",
            "updated_on": "2020-01-01T00:00:00Z",
        }
    }

    route = respx_mock.get("https://redmine.test.local/issues/42.json").mock(return_value=httpx.Response(200, json=body))

    client.get_issue(42, include_attachments=True)
    assert route.called
    assert "include=attachments" in str(route.calls[0].request.url)


def test_get_issue_with_journals_includes(respx_mock):
    cfg = RedmineConfig(url="https://redmine.test.local", api_key="x" * 24)
    client = RedmineClient(cfg)

    body = {
        "issue": {
            "id": 43,
            "subject": "s",
            "project": {"id":1,"name":"P"},
            "tracker": {"id":1,"name":"T"},
            "status": {"id":1,"name":"S"},
            "priority": {"id":1,"name":"Low"},
            "author": {"id":1,"name":"A"},
            "created_on": "2020-01-01T00:00:00Z",
            "updated_on": "2020-01-01T00:00:00Z",
        }
    }

    route = respx_mock.get("https://redmine.test.local/issues/43.json").mock(return_value=httpx.Response(200, json=body))

    client.get_issue(43, include_journals=True)
    assert route.called
    assert "include=journals" in str(route.calls[0].request.url)


def test_issue_subject_not_empty_validator():
    with pytest.raises(ValueError):
        Issue(id=1, subject="   ", project=Project(id=1,name="P"), tracker=Tracker(id=1,name="T"), status=Status(id=1,name="S"), priority=Priority(id=1,name="Low"), author=User(id=1,name="A"), created_on="2020-01-01T00:00:00Z", updated_on="2020-01-01T00:00:00Z")


def test_print_issues_summary_no_assigned_no_attachments(capsys):
    issue = Issue(id=2, subject="s2", project=Project(id=1,name="P"), tracker=Tracker(id=1,name="T"), status=Status(id=1,name="S"), priority=Priority(id=1,name="Low"), author=User(id=1,name="A"), assigned_to=None, created_on="2020-01-01T00:00:00Z", updated_on="2020-01-01T00:00:00Z", attachments=[])
    main_mod.print_issues_summary([issue])
    out = capsys.readouterr().out
    assert "指派給" not in out
    assert "附件數" not in out


def test_exec_main_module_runs(monkeypatch):
    import runpy, sys

    # prevent actual sys.exit from killing the test runner
    monkeypatch.setattr(sys, "exit", lambda code=0: None)
    # Running the module as __main__ should execute the guard line
    runpy.run_module("redmine_knowledge_agent.__main__", run_name="__main__")
