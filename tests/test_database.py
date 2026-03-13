"""Tests for database/models.py."""

import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import AgentMemory, Base, Event, ToolResult, WorkflowRun


@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestEventModel:
    def test_create_event(self, db_session):
        event = Event(event_type="github.pull_request.opened", source="github", payload='{"pr": 1}')
        db_session.add(event)
        db_session.commit()

        result = db_session.query(Event).first()
        assert result is not None
        assert result.event_type == "github.pull_request.opened"
        assert result.source == "github"
        assert result.payload == '{"pr": 1}'
        assert result.id is not None

    def test_multiple_events(self, db_session):
        for i in range(5):
            db_session.add(Event(event_type=f"event.{i}", source="test"))
        db_session.commit()
        assert db_session.query(Event).count() == 5


class TestWorkflowRunModel:
    def test_create_workflow_run(self, db_session):
        run = WorkflowRun(
            workflow_name="pr_opened",
            trigger_event="github.pull_request.opened",
            status="completed",
            result='{"ok": true}',
        )
        db_session.add(run)
        db_session.commit()

        result = db_session.query(WorkflowRun).first()
        assert result.workflow_name == "pr_opened"
        assert result.status == "completed"

    def test_default_status(self, db_session):
        run = WorkflowRun(
            workflow_name="test", trigger_event="test.event", status="pending"
        )
        db_session.add(run)
        db_session.commit()
        assert db_session.query(WorkflowRun).first().status == "pending"


class TestToolResultModel:
    def test_create_tool_result(self, db_session):
        output = ToolResult(
            tool_name="slack.send_message",
            input_data='{"channel": "#test"}',
            output_data='{"ok": true}',
        )
        db_session.add(output)
        db_session.commit()

        result = db_session.query(ToolResult).first()
        assert result.tool_name == "slack.send_message"
        assert result.input_data == '{"channel": "#test"}'
        assert result.output_data == '{"ok": true}'

    def test_defaults(self, db_session):
        output = ToolResult(tool_name="test.tool")
        db_session.add(output)
        db_session.commit()
        result = db_session.query(ToolResult).first()
        assert result.input_data == ""
        assert result.output_data == ""


class TestAgentMemoryModel:
    def test_create_memory(self, db_session):
        mem = AgentMemory(session_id="sess123", role="user", content="hello world")
        db_session.add(mem)
        db_session.commit()

        result = db_session.query(AgentMemory).first()
        assert result.session_id == "sess123"
        assert result.role == "user"
        assert result.content == "hello world"

    def test_multiple_messages_same_session(self, db_session):
        for i in range(3):
            db_session.add(AgentMemory(session_id="s1", role="user", content=f"msg {i}"))
        db_session.commit()
        assert db_session.query(AgentMemory).filter_by(session_id="s1").count() == 3

    def test_multiple_sessions(self, db_session):
        db_session.add(AgentMemory(session_id="s1", role="user", content="a"))
        db_session.add(AgentMemory(session_id="s2", role="user", content="b"))
        db_session.commit()
        assert db_session.query(AgentMemory).count() == 2
