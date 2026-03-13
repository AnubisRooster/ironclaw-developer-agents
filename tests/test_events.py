"""Tests for events/types.py and events/bus.py."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from events.types import AgentEvent, EventSource


class TestAgentEvent:
    def test_create_event(self):
        event = AgentEvent(
            event_type="github.pull_request.opened",
            source=EventSource.GITHUB,
            payload={"pr": 123},
        )
        assert event.event_type == "github.pull_request.opened"
        assert event.source == EventSource.GITHUB
        assert event.payload == {"pr": 123}
        assert event.id  # auto-generated
        assert event.timestamp  # auto-generated

    def test_event_str(self):
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)
        s = str(event)
        assert "system" in s
        assert "test.event" in s

    def test_event_metadata(self):
        event = AgentEvent(
            event_type="test", source=EventSource.CLI, metadata={"user": "test"}
        )
        assert event.metadata["user"] == "test"

    def test_all_event_sources(self):
        sources = [s.value for s in EventSource]
        assert "github" in sources
        assert "jira" in sources
        assert "jenkins" in sources
        assert "slack" in sources
        assert "confluence" in sources
        assert "gmail" in sources
        assert "system" in sources
        assert "cli" in sources


class TestEventBus:
    @pytest.fixture
    def bus(self):
        from events.bus import EventBus
        return EventBus()

    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, bus):
        handler = AsyncMock()
        bus.subscribe("test.event", handler)

        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)
        with patch("events.bus.get_session") as mock_session:
            mock_session.return_value = MagicMock()
            await bus.publish(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_no_match(self, bus):
        handler = AsyncMock()
        bus.subscribe("other.event", handler)

        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)
        with patch("events.bus.get_session") as mock_session:
            mock_session.return_value = MagicMock()
            await bus.publish(event)

        handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_wildcard_subscribe(self, bus):
        handler = AsyncMock()
        bus.subscribe("github.*", handler)

        event = AgentEvent(event_type="github.pull_request.opened", source=EventSource.GITHUB)
        with patch("events.bus.get_session") as mock_session:
            mock_session.return_value = MagicMock()
            await bus.publish(event)

        handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_global_subscriber(self, bus):
        handler = AsyncMock()
        bus.subscribe_all(handler)

        event = AgentEvent(event_type="anything", source=EventSource.SYSTEM)
        with patch("events.bus.get_session") as mock_session:
            mock_session.return_value = MagicMock()
            await bus.publish(event)

        handler.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_handler_exception_does_not_crash(self, bus):
        handler = AsyncMock(side_effect=ValueError("boom"))
        bus.subscribe("test.event", handler)

        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)
        with patch("events.bus.get_session") as mock_session:
            mock_session.return_value = MagicMock()
            await bus.publish(event)  # should not raise

    @pytest.mark.asyncio
    async def test_persist_called(self, bus):
        event = AgentEvent(event_type="test.persist", source=EventSource.SYSTEM, payload={"key": "val"})
        with patch("events.bus.get_session") as mock_session:
            session = MagicMock()
            mock_session.return_value = session
            await bus.publish(event)
            session.add.assert_called_once()
            session.commit.assert_called_once()
