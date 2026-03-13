"""Tests for database/models.py."""

import datetime as dt

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, CachedSummary, Event, ToolOutput, WorkflowRun


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


class TestCachedSummaryModel:
    def test_create_summary(self, db_session):
        summary = CachedSummary(key="pr:123", summary="This PR adds feature X")
        db_session.add(summary)
        db_session.commit()

        result = db_session.query(CachedSummary).filter_by(key="pr:123").first()
        assert result.summary == "This PR adds feature X"

    def test_unique_key_constraint(self, db_session):
        db_session.add(CachedSummary(key="unique-key", summary="first"))
        db_session.commit()
        db_session.add(CachedSummary(key="unique-key", summary="second"))
        with pytest.raises(Exception):
            db_session.commit()


class TestToolOutputModel:
    def test_create_tool_output(self, db_session):
        output = ToolOutput(
            tool_name="slack.send_message",
            input_data='{"channel": "#test"}',
            output_data='{"ok": true}',
        )
        db_session.add(output)
        db_session.commit()

        result = db_session.query(ToolOutput).first()
        assert result.tool_name == "slack.send_message"
        assert result.input_data == '{"channel": "#test"}'
        assert result.output_data == '{"ok": true}'

    def test_defaults(self, db_session):
        output = ToolOutput(tool_name="test.tool")
        db_session.add(output)
        db_session.commit()
        result = db_session.query(ToolOutput).first()
        assert result.input_data == ""
        assert result.output_data == ""
