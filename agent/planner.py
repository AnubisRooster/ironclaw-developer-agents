"""Workflow planning module for decomposing user requests into tool steps."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("claw-agent.planner")


class PlanStep(BaseModel):
    """A single step in an action plan."""

    tool_name: str = Field(..., description="Name of the tool to invoke")
    tool_args: dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    description: str = Field(default="", description="Human-readable step description")
    depends_on: list[int] = Field(default_factory=list, description="Indices of prior steps this step depends on")


class ActionPlan(BaseModel):
    """Structured plan for executing a user request across multiple tool calls."""

    goal: str = Field(..., description="High-level goal of the plan")
    reasoning: str = Field(default="", description="Brief reasoning for the plan")
    steps: list[PlanStep] = Field(default_factory=list, description="Ordered list of tool execution steps")


PLANNER_PROMPT = """You are a developer automation assistant. Given a user request and available tools, decompose the request into a structured action plan.

Available tools: {tools}

User request: {user_request}

{context_section}

Respond with ONLY valid JSON (no markdown, no explanation). Use this exact structure:
{{
  "goal": "brief goal description",
  "reasoning": "why this plan makes sense",
  "steps": [
    {{
      "tool_name": "tool_name",
      "tool_args": {{ "arg1": "value1" }},
      "description": "what this step does",
      "depends_on": []
    }}
  ]
}}

For each step, set depends_on to a list of step indices (0-based) that must complete before this step.
Return ONLY the JSON object."""


class Planner:
    """
    Decomposes user requests into structured action plans using an LLM.
    """

    def __init__(self, llm_client: Any) -> None:
        """
        Initialize the planner with an LLM client.

        Args:
            llm_client: Client with async chat(messages) method returning text.
        """
        self._llm = llm_client

    async def create_plan(
        self,
        user_request: str,
        available_tools: list[str],
        context: str = "",
    ) -> ActionPlan:
        """
        Create an action plan from a user request using available tools.

        Args:
            user_request: The user's request or question.
            available_tools: List of tool names the agent can use.
            context: Optional additional context (e.g. conversation summary).

        Returns:
            Parsed ActionPlan with goal, reasoning, and steps.

        Raises:
            ValueError: If LLM response cannot be parsed as valid ActionPlan.
        """
        tools_str = ", ".join(available_tools)
        context_section = f"Context: {context}\n\n" if context else ""

        prompt = PLANNER_PROMPT.format(
            tools=tools_str,
            user_request=user_request,
            context_section=context_section,
        )

        messages = [
            {"role": "system", "content": "You output only valid JSON. No markdown, no extra text."},
            {"role": "user", "content": prompt},
        ]

        response = await self._llm.chat(messages)
        logger.debug("Planner LLM response: %s", response[:500])

        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            json_lines = [
                line for line in lines
                if not line.startswith("```") and line.strip()
            ]
            response = "\n".join(json_lines)

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error("Planner could not parse JSON: %s", e)
            raise ValueError(f"Invalid plan JSON: {e}") from e

        try:
            return ActionPlan(**data)
        except Exception as e:
            logger.error("Planner could not build ActionPlan: %s", e)
            raise ValueError(f"Invalid plan structure: {e}") from e
