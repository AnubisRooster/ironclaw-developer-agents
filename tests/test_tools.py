"""Tests for tools/registry.py — Tool Schema Registry."""

import pytest

from tools.registry import ToolSchema, ToolSchemaRegistry


class TestToolSchema:
    def test_basic_schema(self):
        schema = ToolSchema(
            name="github.summarize_pr",
            description="Summarize a GitHub pull request",
            parameters={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                },
                "required": ["repo", "pr_number"],
            },
        )
        assert schema.name == "github.summarize_pr"
        assert "repo" in schema.parameters["properties"]

    def test_default_parameters(self):
        schema = ToolSchema(name="simple.tool", description="A simple tool")
        assert schema.parameters["type"] == "object"
        assert schema.parameters["properties"] == {}


class TestToolSchemaRegistry:
    def test_register_and_list(self):
        reg = ToolSchemaRegistry()
        reg.register_tool(
            name="slack.send_message",
            description="Send a Slack message",
            parameters={"type": "object", "properties": {"channel": {"type": "string"}}, "required": ["channel"]},
            handler=lambda channel: {"ok": True},
        )
        assert "slack.send_message" in reg.list_tool_names()

    def test_get_all_tools(self):
        reg = ToolSchemaRegistry()
        reg.register_tool("a.tool", "Tool A", {"type": "object", "properties": {}}, lambda: None)
        reg.register_tool("b.tool", "Tool B", {"type": "object", "properties": {}}, lambda: None)
        tools = reg.get_all_tools()
        assert len(tools) == 2
        names = {t["name"] for t in tools}
        assert names == {"a.tool", "b.tool"}

    def test_get_tool_schema(self):
        reg = ToolSchemaRegistry()
        reg.register_tool("test.tool", "A test", {"type": "object", "properties": {}}, lambda: None)
        schema = reg.get_tool_schema("test.tool")
        assert schema is not None
        assert schema.name == "test.tool"

    def test_get_tool_schema_missing(self):
        reg = ToolSchemaRegistry()
        assert reg.get_tool_schema("nonexistent") is None

    def test_get_tool_descriptions(self):
        reg = ToolSchemaRegistry()
        reg.register_tool("slack.send", "Send Slack message", {"type": "object", "properties": {}}, lambda: None)
        desc = reg.get_tool_descriptions()
        assert "slack.send" in desc
        assert "Send Slack message" in desc

    def test_empty_descriptions(self):
        reg = ToolSchemaRegistry()
        assert reg.get_tool_descriptions() == "No tools registered."

    @pytest.mark.asyncio
    async def test_execute_tool_sync(self):
        reg = ToolSchemaRegistry()
        reg.register_tool("echo", "Echo tool", {"type": "object", "properties": {}}, lambda msg="": msg)
        result = await reg.execute_tool("echo", {"msg": "hello"})
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_execute_tool_async(self):
        async def async_handler(x=0):
            return x * 2

        reg = ToolSchemaRegistry()
        reg.register_tool("double", "Double a number", {"type": "object", "properties": {}}, async_handler)
        result = await reg.execute_tool("double", {"x": 5})
        assert result == 10

    @pytest.mark.asyncio
    async def test_execute_tool_unknown_raises(self):
        reg = ToolSchemaRegistry()
        with pytest.raises(KeyError, match="Unknown tool"):
            await reg.execute_tool("nonexistent", {})

    def test_json_schema_roundtrip(self):
        reg = ToolSchemaRegistry()
        params = {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Repository name"},
                "pr_number": {"type": "integer", "description": "PR number"},
            },
            "required": ["repo", "pr_number"],
        }
        reg.register_tool("github.summarize_pr", "Summarize PR", params, lambda **kw: kw)
        tools = reg.get_all_tools()
        assert tools[0]["parameters"]["required"] == ["repo", "pr_number"]
        assert tools[0]["parameters"]["properties"]["repo"]["type"] == "string"
