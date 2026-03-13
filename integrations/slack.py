"""Slack integration using slack_sdk WebClient."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.integrations.slack")


class SlackIntegration:
    """Slack integration for messaging and channel history."""

    def __init__(self) -> None:
        """Initialize Slack WebClient with token from secrets."""
        secrets = get_secrets()
        self._client = WebClient(token=secrets.slack_bot_token)
        self._logger = logger

    @retry(
        retry=retry_if_exception_type((SlackApiError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def send_message(self, channel: str, text: str) -> dict[str, Any]:
        """Post a message to a Slack channel.

        Args:
            channel: Channel ID or name (e.g. #general, C12345).
            text: Message text to post.

        Returns:
            Dict with ts, channel, ok, and optionally error.
        """
        self._logger.info("Sending message to channel %s", channel)
        response = self._client.chat_postMessage(channel=channel, text=text)
        return {
            "ts": response.get("ts"),
            "channel": response.get("channel"),
            "ok": response.get("ok", True),
        }

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def respond_to_command(
        self, response_url: str, text: str
    ) -> dict[str, Any]:
        """Respond to a slash command via response_url.

        Args:
            response_url: The response_url from the slash command payload.
            text: Response text to post.

        Returns:
            Dict with ok and status_code.
        """
        self._logger.info("Responding to command via response_url")
        with httpx.Client() as client:
            resp = client.post(
                response_url,
                json={"text": text},
                headers={"Content-Type": "application/json"},
            )
            return {
                "ok": resp.is_success,
                "status_code": resp.status_code,
            }

    @retry(
        retry=retry_if_exception_type((SlackApiError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    def read_channel_history(
        self, channel: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Read recent messages from a Slack channel.

        Args:
            channel: Channel ID (e.g. C12345).
            limit: Maximum number of messages to retrieve (default 50).

        Returns:
            List of message dicts with ts, user, text, etc.
        """
        self._logger.info("Reading channel history for %s (limit=%s)", channel, limit)
        response = self._client.conversations_history(channel=channel, limit=limit)
        messages = response.get("messages", [])
        return [
            {
                "ts": m.get("ts"),
                "user": m.get("user"),
                "text": m.get("text", ""),
                "type": m.get("type", "message"),
            }
            for m in messages
        ]
