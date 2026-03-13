"""Event type definitions for the internal event bus."""

from __future__ import annotations

import datetime as dt
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventSource(str, Enum):
    GITHUB = "github"
    JIRA = "jira"
    JENKINS = "jenkins"
    SLACK = "slack"
    CONFLUENCE = "confluence"
    GMAIL = "gmail"
    SYSTEM = "system"
    CLI = "cli"


class AgentEvent(BaseModel):
    """Canonical event that flows through the internal bus."""

    id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: str
    source: EventSource
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.source.value}] {self.event_type} @ {self.timestamp.isoformat()}"
