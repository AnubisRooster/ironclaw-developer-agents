"""IronClaw client — communicates with the Rust-based OpenClaw runtime via HTTP.

IronClaw is responsible for all AI reasoning: prompt interpretation, planning
actions, selecting tools, and summarisation.  The Python orchestrator never
performs reasoning itself; it delegates every decision to IronClaw.

Architecture:

    Python Orchestrator  ──HTTP/JSON──▶  IronClaw Runtime (Rust)
                                              │
                                              ▼
                                         LLM Provider
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from security.secrets import get_secrets

logger = logging.getLogger("claw-agent.ironclaw")


class IronClawClient:
    """HTTP client for the IronClaw (Rust OpenClaw) reasoning runtime.

    All reasoning — prompt interpretation, tool selection, planning, and
    summarisation — is delegated to IronClaw through this client.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        secrets = get_secrets()
        self._base_url = (base_url or secrets.ironclaw_url).rstrip("/")
        self._api_key = api_key or secrets.ironclaw_api_key
        self._timeout = float(secrets.ironclaw_timeout)
        logger.info("IronClaw client ready: %s", self._base_url)

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Send a chat request to IronClaw and return the full response.

        Args:
            messages: Conversation messages in ``[{role, content}]`` format.
            tools: Optional tool schemas (from :pyclass:`ToolSchemaRegistry`).
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.

        Returns:
            Parsed JSON response from IronClaw containing either a text reply
            or an ``actions`` list of tool calls to execute.
        """
        url = f"{self._base_url}/v1/chat"
        payload: dict[str, Any] = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug("POST %s with %d messages, %d tools", url, len(messages), len(tools or []))
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def plan(
        self,
        user_request: str,
        tools: list[dict[str, Any]],
        context: str = "",
    ) -> dict[str, Any]:
        """Ask IronClaw to decompose a request into an action plan.

        Args:
            user_request: Natural-language request from the user.
            tools: Available tool schemas.
            context: Optional conversation context / summary.

        Returns:
            Action plan with ``goal``, ``reasoning``, and ``actions`` list.
        """
        url = f"{self._base_url}/v1/plan"
        payload: dict[str, Any] = {
            "request": user_request,
            "tools": tools,
        }
        if context:
            payload["context"] = context

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug("POST %s — planning for: %s", url, user_request[:120])
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    async def summarize(self, content: str, instruction: str = "") -> str:
        """Ask IronClaw to summarise arbitrary content.

        Args:
            content: Raw text to summarise (logs, PR diffs, emails, etc.).
            instruction: Optional directive (e.g. "focus on errors").

        Returns:
            Summary string.
        """
        url = f"{self._base_url}/v1/summarize"
        payload: dict[str, Any] = {"content": content}
        if instruction:
            payload["instruction"] = instruction

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            logger.debug("POST %s — summarizing %d chars", url, len(content))
            resp = await client.post(url, json=payload, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
            return data.get("summary", "")

    async def health(self) -> dict[str, Any]:
        """Check IronClaw runtime health."""
        url = f"{self._base_url}/health"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()
