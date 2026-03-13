"""Workflow execution engine — runs loaded YAML workflows in response to events."""

from __future__ import annotations

import datetime as dt
import json
import logging
from typing import Any, Dict, Optional

from database.models import WorkflowRun, get_session
from events.bus import EventBus, event_bus
from events.types import AgentEvent
from workflows.loader import WorkflowDefinition, load_all_workflows

logger = logging.getLogger("claw-agent.workflows")


class WorkflowEngine:
    """Loads workflow definitions and executes them when matching events arrive."""

    def __init__(
        self,
        bus: EventBus | None = None,
        workflow_dir: str = "workflows",
    ) -> None:
        self._bus = bus or event_bus
        self._workflows: Dict[str, WorkflowDefinition] = {}
        self._tool_registry: Dict[str, Any] = {}
        self._workflow_dir = workflow_dir

    def load(self) -> None:
        """Load workflow definitions and subscribe triggers to the event bus."""
        self._workflows = load_all_workflows(self._workflow_dir)
        for trigger in self._workflows:
            self._bus.subscribe(trigger, self._handle_event)
        logger.info(
            "WorkflowEngine ready — %d workflow(s) registered", len(self._workflows)
        )

    def register_tool(self, name: str, func: Any) -> None:
        """Register an executable tool that workflows can invoke."""
        self._tool_registry[name] = func

    async def _handle_event(self, event: AgentEvent) -> None:
        """Dispatch a matching workflow when an event fires."""
        wf = self._workflows.get(event.event_type)
        if not wf:
            return
        await self.run_workflow(wf, event)

    async def run_workflow(
        self, wf: WorkflowDefinition, event: AgentEvent
    ) -> Dict[str, Any]:
        """Execute every action in a workflow sequentially."""
        logger.info("Starting workflow: %s (trigger: %s)", wf.name, wf.trigger)

        run = WorkflowRun(
            workflow_name=wf.name,
            trigger_event=event.event_type,
            status="running",
        )
        session = get_session()
        session.add(run)
        session.commit()

        results: list[Dict[str, Any]] = []
        status = "completed"

        for i, action in enumerate(wf.actions):
            step_label = f"[{wf.name} step {i + 1}/{len(wf.actions)}] {action.description or action.tool}"
            logger.info("Executing %s", step_label)

            tool_func = self._tool_registry.get(action.tool)
            if not tool_func:
                logger.error("Tool not found: %s", action.tool)
                results.append({"step": i + 1, "tool": action.tool, "error": "tool_not_found"})
                if action.on_failure == "stop":
                    status = "failed"
                    break
                continue

            merged_args = {**action.args, **event.payload}
            try:
                if _is_coroutine(tool_func):
                    result = await tool_func(**merged_args)
                else:
                    result = tool_func(**merged_args)
                results.append({"step": i + 1, "tool": action.tool, "result": result})
                logger.info("Step %d succeeded: %s", i + 1, action.tool)
            except Exception as exc:
                logger.exception("Step %d failed: %s", i + 1, action.tool)
                results.append({"step": i + 1, "tool": action.tool, "error": str(exc)})
                if action.on_failure == "stop":
                    status = "failed"
                    break

        run.status = status
        run.result = json.dumps(results, default=str)
        run.finished_at = dt.datetime.now(dt.timezone.utc)
        session.merge(run)
        session.commit()
        session.close()

        logger.info("Workflow %s finished with status: %s", wf.name, status)
        return {"workflow": wf.name, "status": status, "results": results}


def _is_coroutine(func: Any) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)
