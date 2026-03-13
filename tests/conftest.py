"""Shared fixtures for the test suite."""

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///")


@pytest.fixture(autouse=True)
def _reset_secrets_cache():
    """Clear the lru_cache on get_secrets between tests so env changes take effect."""
    from security.secrets import get_secrets
    get_secrets.cache_clear()
    yield
    get_secrets.cache_clear()


@pytest.fixture(autouse=True)
def _reset_db_singletons():
    """Reset the database singletons between tests."""
    import database.postgres as pg
    pg._engine = None
    pg._SessionLocal = None
    yield
    pg._engine = None
    pg._SessionLocal = None


@pytest.fixture
def env_secrets(monkeypatch):
    """Set a minimal .env-like set of secrets for testing."""
    vals = {
        "IRONCLAW_URL": "http://localhost:9090",
        "IRONCLAW_API_KEY": "test-ironclaw-key",
        "IRONCLAW_TIMEOUT": "120",
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_APP_TOKEN": "xapp-test-token",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        "GITHUB_TOKEN": "ghp_testtoken123",
        "GITHUB_WEBHOOK_SECRET": "gh-webhook-secret",
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_USER": "test@example.com",
        "JIRA_API_TOKEN": "jira-test-token",
        "JIRA_WEBHOOK_SECRET": "jira-webhook-secret",
        "CONFLUENCE_URL": "https://test.atlassian.net/wiki",
        "CONFLUENCE_USER": "test@example.com",
        "CONFLUENCE_API_TOKEN": "confluence-test-token",
        "JENKINS_URL": "https://jenkins.test.com",
        "JENKINS_USER": "admin",
        "JENKINS_API_TOKEN": "jenkins-test-token",
        "JENKINS_WEBHOOK_SECRET": "jenkins-webhook-secret",
        "GMAIL_CREDENTIALS_FILE": "credentials.json",
        "GMAIL_TOKEN_FILE": "token.json",
        "WEBHOOK_HOST": "127.0.0.1",
        "WEBHOOK_PORT": "8080",
        "DATABASE_URL": "sqlite:///",
    }
    for k, v in vals.items():
        monkeypatch.setenv(k, v)
    return vals
