"""Tests for agent/memory.py, agent/planner.py, agent/ironclaw_client.py, and agent/orchestrator.py."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.memory import ConversationMemory
from agent.planner import ActionPlan, PlanStep, Planner


# ── Memory ──────────────────────────────────────────────────────────────

class TestConversationMemory:
    def test_add_and_get(self):
        mem = ConversationMemory()
        mem.add_message("user", "hello")
        mem.add_message("assistant", "hi there")
        ctx = mem.get_context()
        assert len(ctx) == 2
        assert ctx[0]["role"] == "user"
        assert ctx[1]["content"] == "hi there"

    def test_get_context_limit(self):
        mem = ConversationMemory()
        for i in range(30):
            mem.add_message("user", f"msg {i}")
        assert len(mem.get_context(max_messages=10)) == 10
        assert len(mem.get_context()) == 20

    def test_clear(self):
        mem = ConversationMemory()
        mem.add_message("user", "test")
        mem.clear()
        assert len(mem.get_context()) == 0

    def test_get_summary_empty(self):
        mem = ConversationMemory()
        assert "No messages" in mem.get_summary()

    def test_get_summary_with_messages(self):
        mem = ConversationMemory()
        mem.add_message("user", "hi")
        mem.add_message("assistant", "hello")
        mem.add_message("user", "help")
        summary = mem.get_summary()
        assert "3 messages" in summary
        assert "2 from user" in summary

    def test_to_llm_messages(self):
        mem = ConversationMemory()
        mem.add_message("user", "hello")
        mem.add_message("assistant", "hi")
        msgs = mem.to_llm_messages()
        assert len(msgs) == 2
        assert msgs[0] == {"role": "user", "content": "hello"}
        assert "timestamp" not in msgs[0]

    def test_timestamp_present(self):
        mem = ConversationMemory()
        mem.add_message("user", "test")
        assert "timestamp" in mem.get_context()[0]

    def test_session_id_auto_generated(self):
        mem = ConversationMemory()
        assert len(mem.session_id) == 16

    def test_session_id_custom(self):
        mem = ConversationMemory(session_id="custom-session")
        assert mem.session_id == "custom-session"


# ── Planner ─────────────────────────────────────────────────────────────

class TestPlanModels:
    def test_plan_step(self):
        step = PlanStep(tool_name="slack.send_message", tool_args={"channel": "#test"}, description="send msg")
        assert step.tool_name == "slack.send_message"
        assert step.depends_on == []

    def test_action_plan(self):
        plan = ActionPlan(
            goal="Summarize PR",
            reasoning="User asked for a PR summary",
            steps=[PlanStep(tool_name="github.summarize_pr", tool_args={"repo": "org/repo", "pr_number": 42})],
        )
        assert len(plan.steps) == 1
        assert plan.goal == "Summarize PR"


class TestPlanner:
    @pytest.mark.asyncio
    async def test_create_plan_from_ironclaw(self):
        mock_ironclaw = AsyncMock()
        mock_ironclaw.plan = AsyncMock(return_value={
            "goal": "Summarize PR",
            "reasoning": "User wants PR summary",
            "actions": [
                {"tool": "github.summarize_pr", "parameters": {"repo": "org/repo", "pr_number": 42}, "description": "get PR", "depends_on": []}
            ],
        })
        planner = Planner(mock_ironclaw)
        plan = await planner.create_plan("Summarize PR 42", [{"name": "github.summarize_pr"}])
        assert isinstance(plan, ActionPlan)
        assert plan.goal == "Summarize PR"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "github.summarize_pr"

    @pytest.mark.asyncio
    async def test_create_plan_with_steps_key(self):
        mock_ironclaw = AsyncMock()
        mock_ironclaw.plan = AsyncMock(return_value={
            "goal": "test",
            "reasoning": "",
            "steps": [
                {"tool_name": "a.tool", "tool_args": {}, "description": "step a"},
            ],
        })
        planner = Planner(mock_ironclaw)
        plan = await planner.create_plan("test", [])
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "a.tool"

    @pytest.mark.asyncio
    async def test_create_plan_invalid_structure_raises(self):
        mock_ironclaw = AsyncMock()
        mock_ironclaw.plan = AsyncMock(return_value={"invalid": True})
        planner = Planner(mock_ironclaw)
        plan = await planner.create_plan("test", [])
        assert len(plan.steps) == 0


# ── IronClaw Client ────────────────────────────────────────────────────

class TestIronClawClient:
    def test_init_from_secrets(self, env_secrets):
        from agent.ironclaw_client import IronClawClient
        client = IronClawClient()
        assert client._base_url == "http://localhost:9090"

    def test_init_with_custom_url(self, env_secrets):
        from agent.ironclaw_client import IronClawClient
        client = IronClawClient(base_url="http://custom:8080")
        assert client._base_url == "http://custom:8080"

    @pytest.mark.asyncio
    async def test_chat_sends_request(self, env_secrets):
        from agent.ironclaw_client import IronClawClient

        mock_response = MagicMock()
        mock_response.json.return_value = {"content": "Hello!", "actions": None}
        mock_response.raise_for_status = MagicMock()

        with patch("agent.ironclaw_client.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            client = IronClawClient()
            result = await client.chat(messages=[{"role": "user", "content": "hi"}])
            assert result["content"] == "Hello!"

    @pytest.mark.asyncio
    async def test_summarize(self, env_secrets):
        from agent.ironclaw_client import IronClawClient

        mock_response = MagicMock()
        mock_response.json.return_value = {"summary": "Build failed due to null pointer."}
        mock_response.raise_for_status = MagicMock()

        with patch("agent.ironclaw_client.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.post = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            client = IronClawClient()
            result = await client.summarize("ERROR: NullPointerException at line 42")
            assert "null pointer" in result.lower()

    @pytest.mark.asyncio
    async def test_health(self, env_secrets):
        from agent.ironclaw_client import IronClawClient

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()

        with patch("agent.ironclaw_client.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            MockClient.return_value.__aenter__ = AsyncMock(return_value=client_instance)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)

            client = IronClawClient()
            result = await client.health()
            assert result["status"] == "ok"


# ── Orchestrator ────────────────────────────────────────────────────────

class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self, env_secrets):
        from agent.orchestrator import Orchestrator
        mock_ironclaw = AsyncMock()
        orch = Orchestrator(ironclaw=mock_ironclaw)
        return orch

    def test_register_tool(self, orchestrator):
        orchestrator.register_tool(
            "test.tool", "A test", {"type": "object", "properties": {}}, lambda: "ok"
        )
        assert "test.tool" in orchestrator._registry.list_tool_names()

    @pytest.mark.asyncio
    async def test_handle_message_no_tool_call(self, orchestrator):
        orchestrator._ironclaw.chat = AsyncMock(return_value={
            "content": "Here is your answer.",
            "actions": None,
        })
        response = await orchestrator.handle_message("What is 2+2?")
        assert response == "Here is your answer."

    @pytest.mark.asyncio
    async def test_handle_message_with_tool_call(self, orchestrator):
        tool_mock = MagicMock(return_value={"result": "done"})
        orchestrator.register_tool(
            "test.tool", "Test tool",
            {"type": "object", "properties": {"key": {"type": "string"}}},
            tool_mock,
        )

        orchestrator._ironclaw.chat = AsyncMock(side_effect=[
            {
                "content": "Let me call a tool.",
                "actions": [{"tool": "test.tool", "parameters": {"key": "val"}}],
            },
            {
                "content": "Done! The tool returned success.",
                "actions": None,
            },
        ])

        with patch("agent.orchestrator.session_scope") as mock_scope:
            session = MagicMock()
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            response = await orchestrator.handle_message("Run test tool")

        assert "Done" in response
        tool_mock.assert_called_once_with(key="val")

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, orchestrator):
        with patch("agent.orchestrator.session_scope") as mock_scope:
            session = MagicMock()
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            result = await orchestrator._execute_tool("nonexistent.tool", {})
        assert "unknown tool" in result.lower()

    @pytest.mark.asyncio
    async def test_execute_tool_stores_output(self, orchestrator):
        orchestrator.register_tool(
            "echo", "Echo tool",
            {"type": "object", "properties": {}},
            lambda msg="": msg,
        )
        with patch("agent.orchestrator.session_scope") as mock_scope:
            session = MagicMock()
            mock_scope.return_value.__enter__ = MagicMock(return_value=session)
            mock_scope.return_value.__exit__ = MagicMock(return_value=False)
            result = await orchestrator._execute_tool("echo", {"msg": "hello"})
        assert result == "hello"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_summarize_delegates_to_ironclaw(self, orchestrator):
        orchestrator._ironclaw.summarize = AsyncMock(return_value="Summary of the text.")
        result = await orchestrator.summarize("Long text here...")
        assert result == "Summary of the text."
        orchestrator._ironclaw.summarize.assert_called_once()
