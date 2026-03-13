"""Tests for workflows/loader.py and workflows/engine.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workflows.loader import WorkflowAction, WorkflowDefinition, load_all_workflows, load_workflow


# ── Loader ──────────────────────────────────────────────────────────────

class TestWorkflowAction:
    def test_defaults(self):
        action = WorkflowAction(tool="slack.send_message")
        assert action.args == {}
        assert action.on_failure == "stop"

    def test_with_args(self):
        action = WorkflowAction(tool="slack.send_message", args={"channel": "#test"}, description="Post")
        assert action.args["channel"] == "#test"


class TestWorkflowDefinition:
    def test_basic(self):
        wf = WorkflowDefinition(
            name="test_wf",
            trigger="github.pull_request.opened",
            actions=[WorkflowAction(tool="slack.send_message")],
        )
        assert wf.name == "test_wf"
        assert wf.enabled is True


class TestLoadWorkflow:
    def test_load_valid_yaml(self, tmp_path):
        yaml_content = """
name: test_workflow
trigger: github.pull_request.opened
description: Test workflow
enabled: true
actions:
  - tool: github.summarize_pull_request
    description: Summarize PR
  - tool: slack.send_message
    args:
      channel: "#dev"
    on_failure: continue
"""
        f = tmp_path / "test.yaml"
        f.write_text(yaml_content)
        wf = load_workflow(f)
        assert wf.name == "test_workflow"
        assert wf.trigger == "github.pull_request.opened"
        assert len(wf.actions) == 2
        assert wf.actions[1].args["channel"] == "#dev"
        assert wf.actions[1].on_failure == "continue"

    def test_load_minimal_yaml(self, tmp_path):
        yaml_content = """
trigger: jira.issue.created
actions:
  - tool: slack.send_message
"""
        f = tmp_path / "minimal.yaml"
        f.write_text(yaml_content)
        wf = load_workflow(f)
        assert wf.name == "minimal"
        assert wf.trigger == "jira.issue.created"


class TestLoadAllWorkflows:
    def test_loads_yaml_files(self, tmp_path):
        for name, trigger in [("a", "event.a"), ("b", "event.b")]:
            (tmp_path / f"{name}.yaml").write_text(f"trigger: {trigger}\nactions:\n  - tool: test\n")
        workflows = load_all_workflows(str(tmp_path))
        assert len(workflows) == 2
        assert "event.a" in workflows
        assert "event.b" in workflows

    def test_skips_disabled(self, tmp_path):
        (tmp_path / "disabled.yaml").write_text("trigger: skip\nenabled: false\nactions:\n  - tool: noop\n")
        workflows = load_all_workflows(str(tmp_path))
        assert len(workflows) == 0

    def test_empty_dir(self, tmp_path):
        workflows = load_all_workflows(str(tmp_path))
        assert len(workflows) == 0

    def test_nonexistent_dir(self):
        workflows = load_all_workflows("/nonexistent/path")
        assert len(workflows) == 0

    def test_loads_real_project_workflows(self):
        wfs = load_all_workflows("workflows")
        assert len(wfs) >= 3
        assert "github.pull_request.opened" in wfs
        assert "jenkins.build.failed" in wfs
        assert "jira.issue.created" in wfs


# ── Engine ──────────────────────────────────────────────────────────────

class TestWorkflowEngine:
    @pytest.fixture
    def engine(self):
        from events.bus import EventBus
        from tools.registry import ToolSchemaRegistry
        from workflows.engine import WorkflowEngine
        bus = EventBus()
        registry = ToolSchemaRegistry()
        engine = WorkflowEngine(bus=bus, workflow_dir="workflows", registry=registry)
        return engine, bus, registry

    def test_load_registers_triggers(self, engine):
        eng, bus, registry = engine
        with patch("workflows.engine.session_scope") as mock_scope:
            session = MagicMock()
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            eng.load()
        assert len(bus._subscribers) > 0

    @pytest.mark.asyncio
    async def test_run_workflow(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, bus, registry = engine
        registry.register_tool("step_a", "Step A", {"type": "object", "properties": {}}, lambda **kw: {"done": True})
        registry.register_tool("step_b", "Step B", {"type": "object", "properties": {}}, lambda **kw: {"also_done": True})

        wf = WorkflowDefinition(
            name="test_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="step_a", description="Step A"),
                WorkflowAction(tool="step_b", description="Step B"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.session_scope") as mock_scope:
            session = MagicMock()
            run_obj = MagicMock()
            run_obj.id = 1
            session.flush = MagicMock()
            session.get = MagicMock(return_value=run_obj)
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_run_workflow_missing_tool_stops(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, _, registry = engine
        wf = WorkflowDefinition(
            name="fail_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="nonexistent", description="Missing"),
                WorkflowAction(tool="step_b", description="Never runs"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.session_scope") as mock_scope:
            session = MagicMock()
            run_obj = MagicMock()
            run_obj.id = 1
            session.flush = MagicMock()
            session.get = MagicMock(return_value=run_obj)
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "failed"
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_run_workflow_continue_on_failure(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, _, registry = engine
        registry.register_tool("good_step", "Good step", {"type": "object", "properties": {}}, lambda **kw: {"ok": True})

        wf = WorkflowDefinition(
            name="continue_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="missing_tool", description="Missing", on_failure="continue"),
                WorkflowAction(tool="good_step", description="Runs anyway"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.session_scope") as mock_scope:
            session = MagicMock()
            run_obj = MagicMock()
            run_obj.id = 1
            session.flush = MagicMock()
            session.get = MagicMock(return_value=run_obj)
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_event_triggers_workflow(self, engine):
        from events.types import AgentEvent, EventSource
        eng, bus, registry = engine

        registry.register_tool("github.summarize_pull_request", "Summarize PR", {"type": "object", "properties": {}}, lambda **kw: {"title": "PR"})
        registry.register_tool("slack.send_message", "Send Slack", {"type": "object", "properties": {}}, lambda **kw: {"ok": True})
        registry.register_tool("jira.link_github_issue", "Link Jira", {"type": "object", "properties": {}}, lambda **kw: {"linked": True})

        with patch("workflows.engine.session_scope") as mock_scope:
            session = MagicMock()
            run_obj = MagicMock()
            run_obj.id = 1
            session.flush = MagicMock()
            session.get = MagicMock(return_value=run_obj)
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            eng.load()

            event = AgentEvent(
                event_type="github.pull_request.opened",
                source=EventSource.GITHUB,
                payload={"repo": "org/repo", "pr_number": 1},
            )
            with patch("events.bus.session_scope") as bus_scope:
                bus_session = MagicMock()
                bus_scope.return_value.__enter__ = MagicMock(return_value=bus_session)
                bus_scope.return_value.__exit__ = MagicMock(return_value=False)
                await bus.publish(event)
