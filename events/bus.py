"""In-process async event bus with topic-based pub/sub."""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List

from database.models import Event as EventRow, get_session
from events.types import AgentEvent

logger = logging.getLogger("claw-agent.events")

Subscriber = Callable[[AgentEvent], Awaitable[None]]


class EventBus:
    """Simple topic-based publish/subscribe event bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Subscriber]] = defaultdict(list)
        self._global_subscribers: List[Subscriber] = []

    def subscribe(self, event_type: str, handler: Subscriber) -> None:
        """Register a handler for a specific event type."""
        self._subscribers[event_type].append(handler)
        logger.info("Subscribed %s to %s", getattr(handler, "__qualname__", repr(handler)), event_type)

    def subscribe_all(self, handler: Subscriber) -> None:
        """Register a handler that receives every event."""
        self._global_subscribers.append(handler)

    async def publish(self, event: AgentEvent) -> None:
        """Publish an event — persists to DB and dispatches to subscribers."""
        logger.info("Publishing event: %s", event)
        self._persist(event)

        handlers = list(self._global_subscribers) + list(
            self._subscribers.get(event.event_type, [])
        )
        # Also match wildcard prefixes (e.g. "github.*" matches "github.pull_request.opened")
        for pattern, subs in self._subscribers.items():
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if event.event_type.startswith(prefix) and pattern != event.event_type:
                    handlers.extend(subs)

        tasks = [asyncio.create_task(h(event)) for h in handlers]
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Handler %s failed for %s: %s",
                        getattr(handlers[i], "__qualname__", repr(handlers[i])),
                        event.event_type,
                        result,
                    )

    def _persist(self, event: AgentEvent) -> None:
        """Write event to the local SQLite database."""
        try:
            session = get_session()
            row = EventRow(
                event_type=event.event_type,
                source=event.source.value,
                payload=json.dumps(event.payload, default=str),
            )
            session.add(row)
            session.commit()
            session.close()
        except Exception:
            logger.exception("Failed to persist event %s", event.id)


event_bus = EventBus()
