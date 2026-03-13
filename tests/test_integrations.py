"""Tests for all integration connectors."""

import json
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


# ── Slack ───────────────────────────────────────────────────────────────

class TestSlackIntegration:
    @pytest.fixture
    def slack(self, env_secrets):
        with patch("integrations.slack.WebClient") as MockClient:
            from integrations.slack import SlackIntegration
            instance = SlackIntegration()
            instance._client = MockClient.return_value
            return instance

    def test_send_message(self, slack):
        slack._client.chat_postMessage.return_value = {"ts": "123", "channel": "C1", "ok": True}
        result = slack.send_message("#general", "hello")
        assert result["ok"] is True
        assert result["ts"] == "123"
        slack._client.chat_postMessage.assert_called_once_with(channel="#general", text="hello")

    def test_read_channel_history(self, slack):
        slack._client.conversations_history.return_value = {
            "messages": [
                {"ts": "1", "user": "U1", "text": "hi", "type": "message"},
                {"ts": "2", "user": "U2", "text": "hey"},
            ]
        }
        result = slack.read_channel_history("C123", limit=10)
        assert len(result) == 2
        assert result[0]["text"] == "hi"
        slack._client.conversations_history.assert_called_once_with(channel="C123", limit=10)

    def test_respond_to_command(self, slack):
        with patch("integrations.slack.httpx.Client") as MockHttp:
            mock_resp = MagicMock()
            mock_resp.is_success = True
            mock_resp.status_code = 200
            MockHttp.return_value.__enter__ = MagicMock(return_value=MagicMock(post=MagicMock(return_value=mock_resp)))
            MockHttp.return_value.__exit__ = MagicMock(return_value=False)
            result = slack.respond_to_command("https://hooks.slack.com/response", "OK")
            assert result["ok"] is True


# ── GitHub ──────────────────────────────────────────────────────────────

class TestGitHubIntegration:
    @pytest.fixture
    def github(self, env_secrets):
        with patch("integrations.github_integration.Github") as MockGithub:
            from integrations.github_integration import GitHubIntegration
            instance = GitHubIntegration()
            instance._client = MockGithub.return_value
            return instance

    def test_create_issue(self, github):
        mock_repo = MagicMock()
        mock_issue = MagicMock(number=42, html_url="https://github.com/org/repo/issues/42", title="Bug")
        mock_repo.create_issue.return_value = mock_issue
        github._client.get_repo.return_value = mock_repo

        result = github.create_issue("org/repo", "Bug", "description")
        assert result["number"] == 42
        assert result["title"] == "Bug"
        mock_repo.create_issue.assert_called_once_with(title="Bug", body="description")

    def test_summarize_pull_request(self, github):
        mock_repo = MagicMock()
        mock_pr = MagicMock(
            title="Feature", body="Adds X", changed_files=5,
            additions=100, deletions=20, html_url="https://...", state="open",
        )
        mock_repo.get_pull.return_value = mock_pr
        github._client.get_repo.return_value = mock_repo

        result = github.summarize_pull_request("org/repo", 1)
        assert result["title"] == "Feature"
        assert result["changed_files_count"] == 5
        assert result["additions"] == 100

    def test_comment_on_pr(self, github):
        mock_repo = MagicMock()
        mock_pr = MagicMock()
        mock_comment = MagicMock(html_url="https://...", id=99)
        mock_pr.create_issue_comment.return_value = mock_comment
        mock_repo.get_pull.return_value = mock_pr
        github._client.get_repo.return_value = mock_repo

        result = github.comment_on_pr("org/repo", 1, "LGTM")
        assert result["id"] == 99

    def test_create_branch(self, github):
        mock_repo = MagicMock()
        mock_repo.html_url = "https://github.com/org/repo"
        mock_branch = MagicMock()
        mock_branch.commit.sha = "abc123"
        mock_repo.get_branch.return_value = mock_branch
        mock_ref = MagicMock(ref="refs/heads/feature-x")
        mock_repo.create_git_ref.return_value = mock_ref
        github._client.get_repo.return_value = mock_repo

        result = github.create_branch("org/repo", "feature-x")
        assert result["ref"] == "refs/heads/feature-x"
        assert "feature-x" in result["url"]


# ── Jira ────────────────────────────────────────────────────────────────

class TestJiraIntegration:
    @pytest.fixture
    def jira(self, env_secrets):
        with patch("integrations.jira_integration.JIRA") as MockJIRA:
            from integrations.jira_integration import JiraIntegration
            instance = JiraIntegration()
            instance._client = MockJIRA.return_value
            instance._client.server_url = "https://test.atlassian.net"
            return instance

    def test_create_ticket(self, jira):
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-1"
        mock_issue.fields.summary = "Bug report"
        jira._client.create_issue.return_value = mock_issue

        result = jira.create_ticket("PROJ", "Bug report", "Details here")
        assert result["key"] == "PROJ-1"
        assert "Bug report" in result["summary"]

    def test_update_ticket(self, jira):
        mock_issue = MagicMock()
        jira._client.issue.return_value = mock_issue
        result = jira.update_ticket("PROJ-1", summary="Updated")
        assert result["updated"] is True
        mock_issue.update.assert_called_once()

    def test_link_github_issue(self, jira):
        result = jira.link_github_issue("PROJ-1", "https://github.com/org/repo/issues/1")
        assert result["linked"] is True
        jira._client.add_simple_link.assert_called_once()

    def test_get_ticket_details(self, jira):
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-1"
        mock_issue.fields.summary = "Test"
        mock_issue.fields.status = MagicMock(__str__=lambda s: "Open")
        mock_issue.fields.assignee = MagicMock(displayName="Alice")
        mock_issue.fields.description = "Details"
        jira._client.issue.return_value = mock_issue

        result = jira.get_ticket_details("PROJ-1")
        assert result["key"] == "PROJ-1"
        assert result["assignee"] == "Alice"


# ── Confluence ──────────────────────────────────────────────────────────

class TestConfluenceIntegration:
    @pytest.fixture
    def confluence(self, env_secrets):
        with patch("integrations.confluence.Confluence") as MockConf:
            from integrations.confluence import ConfluenceIntegration
            instance = ConfluenceIntegration()
            instance._client = MockConf.return_value
            instance._client.url = "https://test.atlassian.net/wiki"
            return instance

    def test_search_docs(self, confluence):
        confluence._client.cql.return_value = {
            "results": [
                {"content": {"title": "Deploy Guide", "id": "123"}},
                {"content": {"title": "API Docs", "id": "456"}},
            ]
        }
        results = confluence.search_docs("deploy", limit=5)
        assert len(results) == 2
        assert results[0]["title"] == "Deploy Guide"

    def test_summarize_page(self, confluence):
        confluence._client.get_page_by_id.return_value = {
            "title": "My Page",
            "body": {"storage": {"value": "<p>Hello <b>world</b></p>"}},
        }
        result = confluence.summarize_page("123")
        assert result["title"] == "My Page"
        assert "Hello" in result["content_preview"]
        assert "<p>" not in result["content_preview"]

    def test_create_page(self, confluence):
        confluence._client.create_page.return_value = {"id": "789", "title": "New Page"}
        result = confluence.create_page("SPACE", "New Page", "<p>Content</p>")
        assert result["id"] == "789"


# ── Jenkins ─────────────────────────────────────────────────────────────

class TestJenkinsIntegration:
    @pytest.fixture
    def jenkins(self, env_secrets):
        with patch("integrations.jenkins.jenkins.Jenkins") as MockJenkins:
            from integrations.jenkins import JenkinsIntegration
            instance = JenkinsIntegration()
            instance._client = MockJenkins.return_value
            return instance

    def test_trigger_build(self, jenkins):
        jenkins._client.build_job.return_value = 42
        result = jenkins.trigger_build("my-job")
        assert result["job"] == "my-job"
        assert result["queue_id"] == 42

    def test_trigger_build_with_params(self, jenkins):
        jenkins._client.build_job.return_value = 99
        result = jenkins.trigger_build("my-job", parameters={"BRANCH": "main"})
        assert result["queue_id"] == 99

    def test_get_build_status_latest(self, jenkins):
        jenkins._client.get_job_info.return_value = {"lastBuild": {"number": 10}}
        jenkins._client.get_build_info.return_value = {
            "number": 10, "result": "SUCCESS", "url": "http://...", "duration": 5000,
        }
        result = jenkins.get_build_status("my-job")
        assert result["number"] == 10
        assert result["status"] == "SUCCESS"

    def test_get_build_status_specific(self, jenkins):
        jenkins._client.get_build_info.return_value = {
            "number": 5, "result": "FAILURE", "url": "http://...", "duration": 3000,
        }
        result = jenkins.get_build_status("my-job", build_number=5)
        assert result["status"] == "FAILURE"

    def test_get_build_status_no_builds(self, jenkins):
        jenkins._client.get_job_info.return_value = {"lastBuild": None}
        result = jenkins.get_build_status("my-job")
        assert result["status"] == "unknown"

    def test_fetch_build_logs(self, jenkins):
        jenkins._client.get_job_info.return_value = {"lastBuild": {"number": 10}}
        jenkins._client.get_build_console_output.return_value = "Line1\nLine2\nDone"
        result = jenkins.fetch_build_logs("my-job")
        assert "Line1" in result["log_tail"]

    def test_fetch_build_logs_truncates(self, jenkins):
        jenkins._client.get_job_info.return_value = {"lastBuild": {"number": 1}}
        jenkins._client.get_build_console_output.return_value = "x" * 10000
        result = jenkins.fetch_build_logs("my-job")
        assert len(result["log_tail"]) == 5000


# ── Gmail ───────────────────────────────────────────────────────────────

class TestGmailIntegration:
    @pytest.fixture
    def gmail(self, env_secrets):
        with patch("integrations.gmail.os.path.exists", return_value=False):
            from integrations.gmail import GmailIntegration
            instance = GmailIntegration()
            return instance

    def test_not_configured_read_emails(self, gmail):
        result = gmail.read_emails()
        assert len(result) == 1
        assert result[0]["ok"] is False
        assert "not configured" in result[0]["error"].lower()

    def test_not_configured_summarize_thread(self, gmail):
        result = gmail.summarize_thread("thread123")
        assert result["ok"] is False

    def test_not_configured_send_email(self, gmail):
        result = gmail.send_email("to@test.com", "Subject", "Body")
        assert result["ok"] is False

    def test_not_configured_extract_action_items(self, gmail):
        result = gmail.extract_action_items("thread123")
        assert result["ok"] is False

    def test_with_service_read_emails(self, env_secrets):
        with patch("integrations.gmail.os.path.exists", return_value=False):
            from integrations.gmail import GmailIntegration
            gmail = GmailIntegration()

        mock_service = MagicMock()
        gmail._service = mock_service

        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "msg1"}]
        }
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "msg1",
            "snippet": "Test email",
            "payload": {"headers": [
                {"name": "Subject", "value": "Hello"},
                {"name": "From", "value": "sender@test.com"},
                {"name": "Date", "value": "2025-01-01"},
            ]},
        }
        result = gmail.read_emails("is:unread", max_results=1)
        assert len(result) == 1
        assert result[0]["subject"] == "Hello"
        assert result[0]["from"] == "sender@test.com"
