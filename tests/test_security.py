"""Tests for security/secrets.py."""

import hashlib
import hmac
import logging

import pytest

from security.secrets import (
    AppSecrets,
    RedactingFilter,
    get_secrets,
    redact,
    verify_webhook_signature,
)


class TestAppSecrets:
    def test_defaults(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.delenv("IRONCLAW_URL", raising=False)
        monkeypatch.delenv("WEBHOOK_PORT", raising=False)
        secrets = AppSecrets()
        assert secrets.ironclaw_url == "http://localhost:9090"
        assert secrets.webhook_port == 8080
        assert secrets.database_url == "postgresql://claw:claw@localhost:5432/clawagent"

    def test_loads_from_env(self, env_secrets):
        secrets = get_secrets()
        assert secrets.ironclaw_url == "http://localhost:9090"
        assert secrets.ironclaw_api_key == "test-ironclaw-key"
        assert secrets.slack_bot_token == "xoxb-test-token"
        assert secrets.github_token == "ghp_testtoken123"
        assert secrets.jira_url == "https://test.atlassian.net"
        assert secrets.jenkins_url == "https://jenkins.test.com"
        assert secrets.webhook_port == 8080

    def test_get_secrets_returns_same_instance(self, env_secrets):
        s1 = get_secrets()
        s2 = get_secrets()
        assert s1 is s2


class TestRedact:
    def test_redacts_slack_bot_token(self):
        assert "<REDACTED>" in redact("token is xoxb-1234-abcd")

    def test_redacts_slack_app_token(self):
        assert "<REDACTED>" in redact("xapp-A1234-B5678")

    def test_redacts_github_token(self):
        assert "<REDACTED>" in redact("ghp_abcdef1234567890")

    def test_redacts_bearer(self):
        assert "<REDACTED>" in redact("Authorization: Bearer eyJhbGciOiJ")

    def test_redacts_sk_key(self):
        assert "<REDACTED>" in redact("sk-proj1234abcdef")

    def test_preserves_normal_text(self):
        normal = "This is a normal log line with no secrets"
        assert redact(normal) == normal


class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        secret = "my-secret"
        payload = b'{"hello": "world"}'
        mac = hmac.new(secret.encode(), payload, hashlib.sha256)
        signature = f"sha256={mac.hexdigest()}"
        assert verify_webhook_signature(payload, signature, secret) is True

    def test_invalid_signature(self):
        assert verify_webhook_signature(b"payload", "sha256=bad", "secret") is False

    def test_different_algorithm(self):
        secret = "my-secret"
        payload = b"test"
        mac = hmac.new(secret.encode(), payload, hashlib.sha1)
        signature = f"sha1={mac.hexdigest()}"
        assert verify_webhook_signature(payload, signature, secret, "sha1") is True


class TestRedactingFilter:
    def test_filter_redacts_msg(self):
        f = RedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Token is ghp_abc123xyz789", args=(), exc_info=None,
        )
        f.filter(record)
        assert "ghp_" not in record.msg
        assert "<REDACTED>" in record.msg

    def test_filter_redacts_args(self):
        f = RedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Key: %s", args=("xoxb-secret-token",), exc_info=None,
        )
        f.filter(record)
        assert "xoxb-" not in record.args[0]

    def test_filter_passes_clean_text(self):
        f = RedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="All good here", args=(), exc_info=None,
        )
        assert f.filter(record) is True
        assert record.msg == "All good here"
