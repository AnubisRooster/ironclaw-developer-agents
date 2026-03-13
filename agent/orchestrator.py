"""Main orchestrator — the brain of the Developer Automation Agent."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Callable

import httpx

from database.models import ToolOutput, get_session
from security.secrets import get_secrets

from agent.memory import ConversationMemory
from agent.planner import Planner

logger = logging.getLogger("claw-agent.orchestrator")

TOOL_CALL_PATTERN = re.compile(
    r"```(?:tool_call|json)\s*\n(.*?)\n```",
    re.DOTALL | re.IGNORECASE,
)

SYSTEM_PROMPT_TEMPLATE = """You are a developer automation assistant. You help developers with tasks using the following tools:

{tool_descriptions}

When you need to call a tool, output a JSON block in this exact format:

```tool_call
{{"tool_name": "tool_name", "tool_args": {{"arg": "value"}}}}
```

After receiving tool results, synthesize them and respond to the user. If no tool is needed, reply directly. Be concise and efficient."""


class LLMClient:
    """
    Configurable LLM client supporting OpenRouter, OpenAI, and Ollama.
    """

    def __init__(self) -> None:
        """Initialize client from secrets (provider, base_url, api_key)."""
        secrets = get_secrets()
        self._provider = secrets.openclaw_provider.lower()
        self._model = secrets.openclaw_model
        self._api_key = secrets.openclaw_api_key

        if self._provider == "openrouter":
            self._base_url = "https://openrouter.ai/api/v1"
        elif self._provider == "openai":
            self._base_url = "https://api.openai.com/v1"
        elif self._provider == "ollama":
            self._base_url = secrets.openclaw_base_url or "http://localhost:11434/v1"
        else:
            logger.warning("Unknown provider %r, defaulting to OpenRouter", self._provider)
            self._base_url = "https://openrouter.ai/api/v1"

        logger.info("LLMClient initialized: provider=%s, base_url=%s", self._provider, self._base_url)

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send messages to the LLM and return the assistant content.

        Args:
            messages: List of {role, content} dicts.
            temperature: Sampling temperature (default 0.2).
            max_tokens: Max response tokens (default 4096).

        Returns:
            Content of the first assistant choice.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            ValueError: If response has no choices or content.
        """
        url = f"{self._base_url.rstrip('/')}/chat/completions"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.debug("POST %s with %d messages", url, len(messages))
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("LLM response has no choices")

        content = choices[0].get("message", {}).get("content")
        if content is None:
            raise ValueError("LLM response has no content")
        return str(content).strip()


class ToolRegistry:
    """Registry of available tools: name -> (callable, description)."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._tools: dict[str, tuple[Callable[..., Any], str]] = {}

    def register(self, name: str, func: Callable[..., Any], description: str) -> None:
        """
        Register a tool.

        Args:
            name: Unique tool name.
            func: Callable to invoke (sync or async).
            description: Human-readable description for the LLM.
        """
        self._tools[name] = (func, description)
        logger.debug("Registered tool: %s", name)

    def get_tool(self, name: str) -> Callable[..., Any] | None:
        """Return the callable for the given tool name, or None."""
        entry = self._tools.get(name)
        return entry[0] if entry else None

    def list_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> str:
        """Return formatted string of all tool names and descriptions."""
        lines = [f"- {name}: {desc}" for name, (_, desc) in self._tools.items()]
        return "\n".join(lines) if lines else "No tools registered."


class Orchestrator:
    """
    Main agent orchestrator: manages LLM, planner, memory, and tool execution.
    """

    def __init__(self) -> None:
        """Create LLMClient, Planner, ConversationMemory, and ToolRegistry."""
        self._llm = LLMClient()
        self._planner = Planner(self._llm)
        self._memory = ConversationMemory()
        self._registry = ToolRegistry()

    def register_tool(self, name: str, func: Callable[..., Any], description: str) -> None:
        """Delegate to ToolRegistry."""
        self._registry.register(name, func, description)

    async def handle_message(self, user_message: str) -> str:
        """
        Process a user message: add to memory, send to LLM, execute tools as needed.

        Args:
            user_message: The user's message.

        Returns:
            Final text response to the user.
        """
        self._memory.add_message("user", user_message)
        logger.info("Handling user message: %s", user_message[:200])

        tool_descriptions = self._registry.get_tool_descriptions()
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(tool_descriptions=tool_descriptions)

        max_iterations = 10
        for i in range(max_iterations):
            messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
            messages.extend(self._memory.to_llm_messages())

            response = await self._llm.chat(messages)
            logger.debug("LLM response (iter %d): %s", i + 1, response[:500])

            tool_calls = TOOL_CALL_PATTERN.findall(response)
            if not tool_calls:
                self._memory.add_message("assistant", response)
                return response

            self._memory.add_message("assistant", response)
            for block in tool_calls:
                try:
                    data = json.loads(block.strip())
                    tool_name = data.get("tool_name")
                    tool_args = data.get("tool_args") or {}
                    if not tool_name:
                        logger.warning("Tool call missing tool_name: %s", block[:200])
                        continue
                    result = await self.execute_tool(tool_name, tool_args)
                    self._memory.add_message("user", f"[Tool result: {tool_name}]\n{result}")
                    logger.info("Executed tool %s, got result len=%d", tool_name, len(str(result)))
                except json.JSONDecodeError as e:
                    logger.warning("Could not parse tool_call JSON: %s", e)
                    continue

        logger.warning("handle_message hit max iterations (%d)", max_iterations)
        self._memory.add_message("assistant", response)
        return response

    async def execute_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        """
        Look up tool, invoke it, store result in ToolOutput, return result string.

        Args:
            tool_name: Name of the registered tool.
            tool_args: Arguments to pass to the tool.

        Returns:
            Result of the tool call as a string.

        Raises:
            KeyError: If tool is not registered.
        """
        func = self._registry.get_tool(tool_name)
        if func is None:
            raise KeyError(f"Unknown tool: {tool_name}")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(**tool_args)
            else:
                result = await asyncio.to_thread(func, **tool_args)
        except Exception as e:
            logger.exception("Tool %s failed: %s", tool_name, e)
            result = f"Error: {e}"

        result_str = str(result) if result is not None else ""

        try:
            session = get_session()
            try:
                record = ToolOutput(
                    tool_name=tool_name,
                    input_data=json.dumps(tool_args),
                    output_data=result_str,
                )
                session.add(record)
                session.commit()
            finally:
                session.close()
        except Exception as e:
            logger.warning("Could not persist ToolOutput: %s", e)

        return result_str
