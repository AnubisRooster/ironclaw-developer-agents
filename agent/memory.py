"""Conversation memory module with optional PostgreSQL persistence."""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any
from uuid import uuid4

logger = logging.getLogger("claw-agent.memory")


class ConversationMemory:
    """Stores conversation history for the agent and provides context retrieval.

    In-memory by default; optionally persists to the ``agent_memory`` table
    via :pyfunc:`persist` / :pyfunc:`load`.
    """

    def __init__(self, session_id: str | None = None) -> None:
        self._session_id = session_id or uuid4().hex[:16]
        self._history: list[dict[str, Any]] = []

    @property
    def session_id(self) -> str:
        return self._session_id

    def add_message(self, role: str, content: str) -> None:
        """Append a message to the conversation history.

        Args:
            role: Message role (``user``, ``assistant``, ``system``).
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
        """Return the most recent messages for context.

        Args:
            max_messages: Maximum number of messages to return.
        """
        return self._history[-max_messages:]

    def get_summary(self) -> str:
        """Return a one-line summary of the conversation."""
        if not self._history:
            return "No messages yet."
        count = len(self._history)
        user_count = sum(1 for m in self._history if m["role"] == "user")
        return f"Conversation: {count} messages ({user_count} from user)."

    def clear(self) -> None:
        """Clear all conversation history."""
        self._history.clear()
        logger.info("Conversation memory cleared")

    def to_llm_messages(self) -> list[dict[str, str]]:
        """Return messages in ``[{role, content}]`` format for IronClaw."""
        return [{"role": m["role"], "content": m["content"]} for m in self._history]

    def persist(self) -> None:
        """Write current history to the ``agent_memory`` PostgreSQL table."""
        try:
            from database.postgres import session_scope
            from database.models import AgentMemory

            with session_scope() as session:
                for msg in self._history:
                    record = AgentMemory(
                        session_id=self._session_id,
                        role=msg["role"],
                        content=msg["content"],
                    )
                    session.add(record)
            logger.info("Persisted %d messages for session %s", len(self._history), self._session_id)
        except Exception as exc:
            logger.warning("Could not persist conversation memory: %s", exc)

    def load(self) -> None:
        """Load history from the ``agent_memory`` PostgreSQL table for this session."""
        try:
            from database.postgres import get_session
            from database.models import AgentMemory

            session = get_session()
            rows = (
                session.query(AgentMemory)
                .filter_by(session_id=self._session_id)
                .order_by(AgentMemory.id)
                .all()
            )
            session.close()
            self._history = [
                {
                    "role": r.role,
                    "content": r.content,
                    "timestamp": r.created_at.isoformat() if r.created_at else "",
                }
                for r in rows
            ]
            logger.info("Loaded %d messages for session %s", len(self._history), self._session_id)
        except Exception as exc:
            logger.warning("Could not load conversation memory: %s", exc)
