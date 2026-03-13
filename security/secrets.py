"""Secure credential loading and redaction utilities."""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

logger = logging.getLogger("claw-agent.security")

_REDACT_PATTERNS: list[re.Pattern] = [
    re.compile(r"(xoxb-[A-Za-z0-9\-]+)", re.I),
    re.compile(r"(xapp-[A-Za-z0-9\-]+)", re.I),
    re.compile(r"(ghp_[A-Za-z0-9]+)", re.I),
    re.compile(r"(gho_[A-Za-z0-9]+)", re.I),
    re.compile(r"(sk-[A-Za-z0-9]+)", re.I),
    re.compile(r"(Bearer\s+[A-Za-z0-9\-._~+/]+=*)", re.I),
    re.compile(r"(token[\"']?\s*[:=]\s*[\"'][^\"']+[\"'])", re.I),
]


class AppSecrets(BaseSettings):
    """Central secrets model — all values loaded from env vars / .env."""

    # IronClaw Runtime
    ironclaw_url: str = "http://localhost:9090"
    ironclaw_api_key: str = ""
    ironclaw_timeout: int = 120

    # Slack
    slack_bot_token: str = ""
    slack_app_token: str = ""
    slack_signing_secret: str = ""

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = ""

    # Jira
    jira_url: str = ""
    jira_user: str = ""
    jira_api_token: str = ""
    jira_webhook_secret: str = ""

    # Confluence
    confluence_url: str = ""
    confluence_user: str = ""
    confluence_api_token: str = ""

    # Jenkins
    jenkins_url: str = ""
    jenkins_user: str = ""
    jenkins_api_token: str = ""
    jenkins_webhook_secret: str = ""

    # Gmail
    gmail_credentials_file: str = "credentials.json"
    gmail_token_file: str = "token.json"

    # Server
    webhook_host: str = "0.0.0.0"
    webhook_port: int = Field(default=8080)

    # Database (PostgreSQL)
    database_url: str = "postgresql://claw:claw@localhost:5432/clawagent"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_secrets() -> AppSecrets:
    """Return the singleton secrets instance."""
    return AppSecrets()


def redact(text: str) -> str:
    """Replace known secret patterns with <REDACTED>."""
    result = text
    for pattern in _REDACT_PATTERNS:
        result = pattern.sub("<REDACTED>", result)
    return result


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    algorithm: str = "sha256",
) -> bool:
    """Validate an HMAC webhook signature."""
    mac = hmac.new(secret.encode(), payload, getattr(hashlib, algorithm))
    expected = f"{algorithm}={mac.hexdigest()}"
    return hmac.compare_digest(expected, signature)


class RedactingFilter(logging.Filter):
    """Logging filter that scrubs sensitive patterns from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)
        if record.args:
            record.args = tuple(
                redact(a) if isinstance(a, str) else a for a in record.args
            )
        return True
