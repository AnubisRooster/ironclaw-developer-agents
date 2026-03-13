"""Tests for webhooks/server.py — FastAPI endpoint validation."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(env_secrets):
    with patch("webhooks.server.event_bus") as mock_bus:
        mock_bus.publish = AsyncMock()
        from webhooks.server import app
        yield TestClient(app), mock_bus


class TestHealthEndpoint:
    def test_health(self, client):
        tc, _ = client
        resp = tc.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestGitHubWebhook:
    def test_valid_request_no_secret(self, client, monkeypatch):
        tc, mock_bus = client
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()

        payload = {"action": "opened", "pull_request": {"number": 1}}
        resp = tc.post(
            "/webhooks/github",
            json=payload,
            headers={"x-github-event": "pull_request"},
        )
        assert resp.status_code == 200
        assert resp.json()["event_type"] == "github.pull_request.opened"

    def test_valid_signature(self, client):
        tc, mock_bus = client
        payload = json.dumps({"action": "opened"}).encode()
        secret = "gh-webhook-secret"
        sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        resp = tc.post(
            "/webhooks/github",
            content=payload,
            headers={
                "x-github-event": "pull_request",
                "x-hub-signature-256": sig,
                "content-type": "application/json",
            },
        )
        assert resp.status_code == 200

    def test_invalid_signature(self, client):
        tc, _ = client
        resp = tc.post(
            "/webhooks/github",
            json={"action": "opened"},
            headers={
                "x-github-event": "push",
                "x-hub-signature-256": "sha256=invalid",
            },
        )
        assert resp.status_code == 403

    def test_missing_signature_when_required(self, client):
        tc, _ = client
        resp = tc.post(
            "/webhooks/github",
            json={"action": "opened"},
            headers={"x-github-event": "push"},
        )
        assert resp.status_code == 401


class TestJiraWebhook:
    def test_valid_request(self, client, monkeypatch):
        tc, mock_bus = client
        monkeypatch.setenv("JIRA_WEBHOOK_SECRET", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()

        payload = {"webhookEvent": "jira:issue_created", "issue": {"key": "PROJ-1"}}
        resp = tc.post("/webhooks/jira", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "jira" in data["event_type"]


class TestJenkinsWebhook:
    def test_valid_request(self, client, monkeypatch):
        tc, mock_bus = client
        monkeypatch.setenv("JENKINS_WEBHOOK_SECRET", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()

        payload = {
            "name": "my-job",
            "build": {"phase": "COMPLETED", "status": "FAILURE", "number": 42},
        }
        resp = tc.post("/webhooks/jenkins", json=payload)
        assert resp.status_code == 200
        assert "jenkins.build" in resp.json()["event_type"]


class TestSlackWebhook:
    def test_url_verification(self, client, monkeypatch):
        tc, _ = client
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()

        payload = {"type": "url_verification", "challenge": "abc123"}
        resp = tc.post("/webhooks/slack", json=payload)
        assert resp.status_code == 200
        assert resp.json()["challenge"] == "abc123"

    def test_event_callback(self, client, monkeypatch):
        tc, mock_bus = client
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()

        payload = {"type": "event_callback", "event": {"type": "message", "text": "hello"}}
        resp = tc.post("/webhooks/slack", json=payload)
        assert resp.status_code == 200
        assert "slack" in resp.json()["event_type"]
