"""Tests for agent/memory.py, agent/planner.py, and agent/orchestrator.py."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.memory import ConversationMemory
from agent.planner import ActionPlan, PlanStep, Planner
from agent.orchestrator import LLMClient, Orchestrator, ToolRegistry, TOOL_CALL_PATTERN


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
            steps=[PlanStep(tool_name="github.summarize_pull_request", tool_args={"repo": "org/repo", "pr_number": 42})],
        )
        assert len(plan.steps) == 1
        assert plan.goal == "Summarize PR"


class TestPlanner:
    @pytest.mark.asyncio
    async def test_create_plan_parses_json(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value=json.dumps({
            "goal": "Summarize PR",
            "reasoning": "User wants PR summary",
            "steps": [
                {"tool_name": "github.summarize_pull_request", "tool_args": {"repo": "org/repo", "pr_number": 42}, "description": "get PR", "depends_on": []}
            ],
        }))
        planner = Planner(mock_llm)
        plan = await planner.create_plan("Summarize PR 42", ["github.summarize_pull_request"])
        assert isinstance(plan, ActionPlan)
        assert plan.goal == "Summarize PR"
        assert len(plan.steps) == 1
        assert plan.steps[0].tool_name == "github.summarize_pull_request"

    @pytest.mark.asyncio
    async def test_create_plan_strips_markdown(self):
        mock_llm = AsyncMock()
        json_body = json.dumps({"goal": "test", "reasoning": "", "steps": []})
        mock_llm.chat = AsyncMock(return_value=f"```json\n{json_body}\n```")
        planner = Planner(mock_llm)
        plan = await planner.create_plan("test", [])
        assert plan.goal == "test"

    @pytest.mark.asyncio
    async def test_create_plan_invalid_json_raises(self):
        mock_llm = AsyncMock()
        mock_llm.chat = AsyncMock(return_value="this is not json")
        planner = Planner(mock_llm)
        with pytest.raises(ValueError, match="Invalid plan JSON"):
            await planner.create_plan("test", [])


# ── Tool Registry ───────────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_get(self):
        reg = ToolRegistry()
        func = lambda x: x
        reg.register("my.tool", func, "A test tool")
        assert reg.get_tool("my.tool") is func

    def test_get_missing_tool(self):
        reg = ToolRegistry()
        assert reg.get_tool("nonexistent") is None

    def test_list_tools(self):
        reg = ToolRegistry()
        reg.register("a", lambda: None, "tool a")
        reg.register("b", lambda: None, "tool b")
        assert sorted(reg.list_tools()) == ["a", "b"]

    def test_get_tool_descriptions(self):
        reg = ToolRegistry()
        reg.register("slack.send", lambda: None, "Send Slack message")
        desc = reg.get_tool_descriptions()
        assert "slack.send" in desc
        assert "Send Slack message" in desc

    def test_empty_descriptions(self):
        reg = ToolRegistry()
        assert reg.get_tool_descriptions() == "No tools registered."


# ── LLMClient ───────────────────────────────────────────────────────────

class TestLLMClient:
    def test_openai_provider(self, env_secrets):
        client = LLMClient()
        assert client._base_url == "https://api.openai.com/v1"
        assert client._model == "gpt-4o"

    def test_openrouter_provider(self, monkeypatch):
        monkeypatch.setenv("OPENCLAW_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENCLAW_API_KEY", "test")
        monkeypatch.setenv("OPENCLAW_MODEL", "test-model")
        from security.secrets import get_secrets
        get_secrets.cache_clear()
        client = LLMClient()
        assert "openrouter.ai" in client._base_url

    def test_ollama_provider(self, monkeypatch):
        monkeypatch.setenv("OPENCLAW_PROVIDER", "ollama")
        monkeypatch.setenv("OPENCLAW_API_KEY", "")
        monkeypatch.setenv("OPENCLAW_MODEL", "llama3")
        monkeypatch.setenv("OPENCLAW_BASE_URL", "")
        from security.secrets import get_secrets
        get_secrets.cache_clear()
        client = LLMClient()
        assert "localhost:11434" in client._base_url

    def test_ollama_custom_url(self, monkeypatch):
        monkeypatch.setenv("OPENCLAW_PROVIDER", "ollama")
        monkeypatch.setenv("OPENCLAW_API_KEY", "")
        monkeypatch.setenv("OPENCLAW_MODEL", "llama3")
        monkeypatch.setenv("OPENCLAW_BASE_URL", "http://myhost:5000/v1")
        from security.secrets import get_secrets
        get_secrets.cache_clear()
        client = LLMClient()
        assert client._base_url == "http://myhost:5000/v1"


# ── TOOL_CALL_PATTERN ──────────────────────────────────────────────────

class TestToolCallPattern:
    def test_matches_tool_call_block(self):
        text = 'Some text\n```tool_call\n{"tool_name": "slack.send_message", "tool_args": {"channel": "#test"}}\n```\nMore text'
        matches = TOOL_CALL_PATTERN.findall(text)
        assert len(matches) == 1
        parsed = json.loads(matches[0].strip())
        assert parsed["tool_name"] == "slack.send_message"

    def test_matches_json_block(self):
        text = '```json\n{"tool_name": "github.create_issue", "tool_args": {}}\n```'
        matches = TOOL_CALL_PATTERN.findall(text)
        assert len(matches) == 1

    def test_no_match_on_plain_text(self):
        matches = TOOL_CALL_PATTERN.findall("Just a normal response with no tool calls.")
        assert len(matches) == 0


# ── Orchestrator ────────────────────────────────────────────────────────

class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self, env_secrets):
        with patch("agent.orchestrator.get_session") as mock_gs:
            mock_gs.return_value = MagicMock()
            orch = Orchestrator()
            return orch

    def test_register_tool(self, orchestrator):
        orchestrator.register_tool("test.tool", lambda: "ok", "A test")
        assert "test.tool" in orchestrator._registry.list_tools()

    @pytest.mark.asyncio
    async def test_handle_message_no_tool_call(self, orchestrator):
        with patch.object(orchestrator._llm, "chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "Here is your answer."
            response = await orchestrator.handle_message("What is 2+2?")
            assert response == "Here is your answer."

    @pytest.mark.asyncio
    async def test_handle_message_with_tool_call(self, orchestrator):
        tool_mock = MagicMock(return_value={"result": "done"})
        orchestrator.register_tool("test.tool", tool_mock, "Test tool")

        call_response = 'Let me call the tool.\n```tool_call\n{"tool_name": "test.tool", "tool_args": {"key": "val"}}\n```'

        with patch.object(orchestrator._llm, "chat", new_callable=AsyncMock) as mock_chat:
            mock_chat.side_effect = [call_response, "Done! The tool returned success."]
            with patch("agent.orchestrator.get_session") as mock_gs:
                mock_gs.return_value = MagicMock()
                response = await orchestrator.handle_message("Run test tool")

        assert "Done" in response
        tool_mock.assert_called_once_with(key="val")

    @pytest.mark.asyncio
    async def test_execute_tool_unknown_raises(self, orchestrator):
        with pytest.raises(KeyError, match="Unknown tool"):
            await orchestrator.execute_tool("nonexistent.tool", {})

    @pytest.mark.asyncio
    async def test_execute_tool_stores_output(self, orchestrator):
        orchestrator.register_tool("echo", lambda msg: msg, "Echo tool")
        with patch("agent.orchestrator.get_session") as mock_gs:
            session = MagicMock()
            mock_gs.return_value = session
            result = await orchestrator.execute_tool("echo", {"msg": "hello"})
            assert result == "hello"
            session.add.assert_called_once()
            session.commit.assert_called_once()
