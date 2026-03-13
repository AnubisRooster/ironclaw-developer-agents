"""Agent orchestrator — the central coordinator of the Developer Automation Agent.

All reasoning is delegated to IronClaw.  The orchestrator is responsible for:
  - receiving user messages
  - sending them (with tool schemas) to IronClaw
  - executing the tool actions IronClaw returns
  - feeding results back to IronClaw for synthesis
  - persisting tool results to PostgreSQL
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.ironclaw_client import IronClawClient
from agent.memory import ConversationMemory
from database.postgres import session_scope
from database.models import ToolResult
from tools.registry import ToolSchemaRegistry

logger = logging.getLogger("claw-agent.orchestrator")


class Orchestrator:
    """Main agent orchestrator: manages IronClaw, memory, and tool execution.

    The orchestrator never performs reasoning itself.  Every decision —
    which tools to call, what to say to the user — comes from IronClaw.
    """

    def __init__(
        self,
        ironclaw: IronClawClient | None = None,
        registry: ToolSchemaRegistry | None = None,
    ) -> None:
        self._ironclaw = ironclaw or IronClawClient()
        self._registry = registry or ToolSchemaRegistry()
        self._memory = ConversationMemory()

    @property
    def registry(self) -> ToolSchemaRegistry:
        return self._registry

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Any,
    ) -> None:
        """Convenience method to register a tool on the embedded registry."""
        self._registry.register_tool(name, description, parameters, handler)

    async def handle_message(self, user_message: str) -> str:
        """Process a user message through the IronClaw reasoning loop.

        1. Add message to memory.
        2. Send conversation + available tools to IronClaw.
        3. If IronClaw returns tool actions, execute them and loop.
        4. When IronClaw returns a text response, return it.

        Args:
            user_message: Natural-language input from the user or event.

        Returns:
            Final text response to the user.
        """
        self._memory.add_message("user", user_message)
        logger.info("Handling user message: %s", user_message[:200])

        tools = self._registry.get_all_tools()

        max_iterations = 10
        for iteration in range(max_iterations):
            messages = self._memory.to_llm_messages()
            response = await self._ironclaw.chat(messages=messages, tools=tools)

            actions = response.get("actions")
            text = response.get("content") or response.get("text", "")

            if not actions:
                self._memory.add_message("assistant", text)
                return text

            self._memory.add_message("assistant", text or "(executing tools)")

            for action in actions:
                tool_name = action.get("tool")
                tool_args = action.get("parameters") or action.get("args") or {}
                if not tool_name:
                    logger.warning("IronClaw returned action without tool name: %s", action)
                    continue

                result = await self._execute_tool(tool_name, tool_args)
                self._memory.add_message(
                    "user", f"[Tool result: {tool_name}]\n{result}"
                )
                logger.info(
                    "Executed tool %s (iter %d), result length=%d",
                    tool_name, iteration + 1, len(str(result)),
                )

        logger.warning("handle_message hit max iterations (%d)", max_iterations)
        return text

    async def _execute_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        """Execute a tool and persist the result.

        Args:
            tool_name: Name of the registered tool.
            tool_args: Arguments to pass to the tool handler.

        Returns:
            Result as a string.
        """
        try:
            result = await self._registry.execute_tool(tool_name, tool_args)
        except KeyError:
            logger.error("IronClaw requested unknown tool: %s", tool_name)
            result = f"Error: unknown tool '{tool_name}'"
        except Exception as exc:
            logger.exception("Tool %s failed: %s", tool_name, exc)
            result = f"Error: {exc}"

        result_str = str(result) if result is not None else ""

        try:
            with session_scope() as session:
                record = ToolResult(
                    tool_name=tool_name,
                    input_data=json.dumps(tool_args, default=str),
                    output_data=result_str[:50000],
                )
                session.add(record)
        except Exception as exc:
            logger.warning("Could not persist ToolResult: %s", exc)

        return result_str

    async def summarize(self, content: str, instruction: str = "") -> str:
        """Delegate summarisation to IronClaw.

        Registered as the ``agent.summarize`` tool so workflows can use it.
        """
        return await self._ironclaw.summarize(content, instruction)
