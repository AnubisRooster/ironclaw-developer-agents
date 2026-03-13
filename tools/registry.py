"""Tool Schema Registry — dynamic registration of tools with JSON schema definitions.

IronClaw queries this registry to understand available capabilities.
Each tool carries a name, description, JSON schema for parameters, and a handler function.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable

from pydantic import BaseModel, Field

logger = logging.getLogger("claw-agent.tools")


class ToolSchema(BaseModel):
    """Schema definition for a registered tool."""

    name: str = Field(..., description="Unique dot-delimited tool name (e.g. github.summarize_pr)")
    description: str = Field(..., description="Human-readable description of the tool")
    parameters: dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}, "required": []},
        description="JSON Schema for tool parameters",
    )


class RegisteredTool(BaseModel):
    """Internal record combining a schema with its handler reference."""

    tool_schema: ToolSchema
    handler_name: str = ""

    model_config = {"arbitrary_types_allowed": True}


class ToolSchemaRegistry:
    """Registry of tools with JSON Schema definitions and executable handlers.

    Integrations register their tools here. IronClaw queries the registry to
    understand available capabilities. The orchestrator uses the registry to
    execute tool calls returned by IronClaw.
    """

    def __init__(self) -> None:
        self._schemas: dict[str, ToolSchema] = {}
        self._handlers: dict[str, Callable[..., Any]] = {}

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[..., Any],
    ) -> None:
        """Register a tool with its JSON schema and handler function.

        Args:
            name: Unique tool name (e.g. ``github.summarize_pr``).
            description: What the tool does, shown to IronClaw.
            parameters: JSON Schema object describing accepted parameters.
            handler: Callable (sync or async) that executes the tool.
        """
        schema = ToolSchema(name=name, description=description, parameters=parameters)
        self._schemas[name] = schema
        self._handlers[name] = handler
        logger.info("Registered tool: %s", name)

    def get_all_tools(self) -> list[dict[str, Any]]:
        """Return all registered tool schemas as JSON-serialisable dicts.

        This payload is sent to IronClaw so it knows what tools are available.
        """
        return [s.model_dump() for s in self._schemas.values()]

    def get_tool_schema(self, name: str) -> ToolSchema | None:
        """Return the schema for a specific tool, or ``None``."""
        return self._schemas.get(name)

    def list_tool_names(self) -> list[str]:
        """Return a sorted list of registered tool names."""
        return sorted(self._schemas.keys())

    def get_tool_descriptions(self) -> str:
        """Return a formatted string of all tool names and descriptions."""
        lines = [f"- {s.name}: {s.description}" for s in self._schemas.values()]
        return "\n".join(lines) if lines else "No tools registered."

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Look up a tool handler and invoke it.

        Args:
            name: Registered tool name.
            arguments: Keyword arguments matching the tool's parameter schema.

        Returns:
            The tool handler's return value.

        Raises:
            KeyError: If no tool with the given name is registered.
        """
        handler = self._handlers.get(name)
        if handler is None:
            raise KeyError(f"Unknown tool: {name}")

        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)
        return await asyncio.to_thread(handler, **arguments)
