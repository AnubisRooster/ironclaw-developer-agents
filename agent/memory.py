"""Conversation memory module for maintaining chat history and context."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

logger = logging.getLogger("claw-agent.memory")


class ConversationMemory:
    """
    Stores conversation history for the agent and provides context retrieval.
    """

    def __init__(self) -> None:
        """Initialize empty conversation history."""
        self._history: list[dict[str, Any]] = []

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: Message role (e.g. 'user', 'assistant', 'system').
            content: Message content text.
        """
        self._history.append(
            {
                "role": role,
                "content": content,
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
            }
        )
        logger.debug("Added %s message (%d total)", role, len(self._history))

    def get_context(self, max_messages: int = 20) -> list[dict[str, Any]]:
        """
        Return the most recent messages for context.

        Args:
            max_messages: Maximum number of messages to return (default 20).

        Returns:
            List of message dicts with role, content, timestamp.
        """
        return self._history[-max_messages:]

    def get_summary(self) -> str:
        """
        Return a one-line summary of the conversation so far.

        Returns:
            Brief summary string of conversation topic and length.
        """
        if not self._history:
            return "No messages yet."
        roles = [m["role"] for m in self._history]
        count = len(self._history)
        user_count = roles.count("user")
        return f"Conversation: {count} messages ({user_count} from user)."

    def clear(self) -> None:
        """Clear all conversation history."""
        self._history.clear()
        logger.info("Conversation memory cleared")

    def to_llm_messages(self) -> list[dict[str, str]]:
        """
        Return messages in OpenAI-style format for API calls.

        Returns:
            List of dicts with only role and content keys.
        """
        return [{"role": m["role"], "content": m["content"]} for m in self._history]
