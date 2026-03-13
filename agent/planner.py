"""Workflow planning module — delegates plan creation to IronClaw."""

from __future__ import annotations

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


class Planner:
    """Decomposes user requests into structured action plans via IronClaw.

    Unlike direct LLM planning, this planner delegates entirely to the
    IronClaw runtime, which handles prompt construction and response parsing.
    """

    def __init__(self, ironclaw_client: Any) -> None:
        """
        Args:
            ironclaw_client: :pyclass:`IronClawClient` instance.
        """
        self._ironclaw = ironclaw_client

    async def create_plan(
        self,
        user_request: str,
        available_tools: list[dict[str, Any]],
        context: str = "",
    ) -> ActionPlan:
        """Create an action plan by asking IronClaw to decompose the request.

        Args:
            user_request: The user's request or question.
            available_tools: Tool schemas from the registry.
            context: Optional additional context.

        Returns:
            Parsed :pyclass:`ActionPlan`.

        Raises:
            ValueError: If IronClaw response cannot be parsed as a valid plan.
        """
        data = await self._ironclaw.plan(
            user_request=user_request,
            tools=available_tools,
            context=context,
        )
        logger.debug("IronClaw plan response: %s", str(data)[:500])

        try:
            steps = []
            for action in data.get("actions", data.get("steps", [])):
                steps.append(PlanStep(
                    tool_name=action.get("tool") or action.get("tool_name", ""),
                    tool_args=action.get("parameters") or action.get("tool_args", {}),
                    description=action.get("description", ""),
                    depends_on=action.get("depends_on", []),
                ))
            return ActionPlan(
                goal=data.get("goal", user_request),
                reasoning=data.get("reasoning", ""),
                steps=steps,
            )
        except Exception as exc:
            logger.error("Could not build ActionPlan from IronClaw response: %s", exc)
            raise ValueError(f"Invalid plan structure: {exc}") from exc
