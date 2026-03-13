"""Tests for workflows/loader.py and workflows/engine.py."""

import json
import tempfile
from pathlib import Path
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
        from workflows.engine import WorkflowEngine
        bus = EventBus()
        engine = WorkflowEngine(bus=bus, workflow_dir="workflows")
        return engine, bus

    def test_load_registers_triggers(self, engine):
        eng, bus = engine
        with patch("workflows.engine.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            eng.load()
        assert len(bus._subscribers) > 0

    def test_register_tool(self, engine):
        eng, _ = engine
        eng.register_tool("test", lambda: "ok")
        assert "test" in eng._tool_registry

    @pytest.mark.asyncio
    async def test_run_workflow(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, bus = engine
        eng.register_tool("step_a", lambda **kw: {"done": True})
        eng.register_tool("step_b", lambda **kw: {"also_done": True})

        wf = WorkflowDefinition(
            name="test_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="step_a", description="Step A"),
                WorkflowAction(tool="step_b", description="Step B"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_run_workflow_missing_tool_stops(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, _ = engine
        wf = WorkflowDefinition(
            name="fail_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="nonexistent", description="Missing"),
                WorkflowAction(tool="step_b", description="Never runs"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "failed"
        assert len(result["results"]) == 1

    @pytest.mark.asyncio
    async def test_run_workflow_continue_on_failure(self, engine):
        from events.types import AgentEvent, EventSource
        from workflows.loader import WorkflowAction, WorkflowDefinition

        eng, _ = engine
        eng.register_tool("good_step", lambda **kw: {"ok": True})

        wf = WorkflowDefinition(
            name="continue_wf",
            trigger="test.event",
            actions=[
                WorkflowAction(tool="missing_tool", description="Missing", on_failure="continue"),
                WorkflowAction(tool="good_step", description="Runs anyway"),
            ],
        )
        event = AgentEvent(event_type="test.event", source=EventSource.SYSTEM)

        with patch("workflows.engine.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            result = await eng.run_workflow(wf, event)

        assert result["status"] == "completed"
        assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_event_triggers_workflow(self, engine):
        from events.types import AgentEvent, EventSource
        eng, bus = engine
        eng.register_tool("github.summarize_pull_request", lambda **kw: {"title": "PR"})
        eng.register_tool("slack.send_message", lambda **kw: {"ok": True})
        eng.register_tool("jira.link_github_issue", lambda **kw: {"linked": True})

        with patch("workflows.engine.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            eng.load()

            event = AgentEvent(
                event_type="github.pull_request.opened",
                source=EventSource.GITHUB,
                payload={"repo": "org/repo", "pr_number": 1},
            )
            with patch("events.bus.get_session") as bus_gs:
                bus_gs.return_value = MagicMock()
                await bus.publish(event)
