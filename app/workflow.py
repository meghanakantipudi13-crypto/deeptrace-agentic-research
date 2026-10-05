"""LangGraph-based Phase 1 planning workflow."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.logging import log_event
from app.models import PlanningResult, ResearchPlan, ResearchState
from app.providers.base import PlanModel


class PlanningWorkflow:
    """Run the minimal graph and stop after a structured plan is ready."""

    def __init__(self, plan_model: PlanModel) -> None:
        self._plan_model = plan_model
        self._logger = logging.getLogger("deeptrace.workflow")
        builder = StateGraph(ResearchState)
        builder.add_node("start_workflow", self._start_workflow)
        builder.add_node("create_plan", self._create_plan)
        builder.add_node("finish_workflow", self._finish_workflow)
        builder.add_edge(START, "start_workflow")
        builder.add_edge("start_workflow", "create_plan")
        builder.add_edge("create_plan", "finish_workflow")
        builder.add_edge("finish_workflow", END)
        self.graph = builder.compile()

    async def _start_workflow(self, state: ResearchState) -> ResearchState:
        log_event(
            self._logger,
            "workflow_started",
            request_id=state["request_id"],
            stage="start_workflow",
        )
        return {
            "status": "planning",
            "current_stage": "start_workflow",
            "workflow_events": [*state.get("workflow_events", []), "workflow_started"],
        }

    async def _create_plan(self, state: ResearchState) -> ResearchState:
        request_id = state["request_id"]
        log_event(
            self._logger,
            "workflow_stage_started",
            request_id=request_id,
            stage="create_plan",
        )
        plan = await self._plan_model.create_plan(state["question"])
        log_event(
            self._logger,
            "workflow_stage_completed",
            request_id=request_id,
            stage="create_plan",
            simulated=plan.is_simulated,
            step_count=len(plan.steps),
        )
        return {
            "research_plan": plan.model_dump(mode="json"),
            "current_stage": "create_plan",
            "workflow_events": [
                *state.get("workflow_events", []),
                "planning_started",
                "planning_completed",
            ],
        }

    async def _finish_workflow(self, state: ResearchState) -> ResearchState:
        log_event(
            self._logger,
            "workflow_completed",
            request_id=state["request_id"],
            stage="finish_workflow",
            boundary="plan_ready",
        )
        return {
            "status": "plan_ready",
            "current_stage": "finish_workflow",
            "workflow_events": [*state.get("workflow_events", []), "workflow_completed"],
        }

    async def run(self, question: str) -> PlanningResult:
        request_id = str(uuid4())
        started = perf_counter()
        state = await self.graph.ainvoke(
            {
                "request_id": request_id,
                "question": question,
                "status": "received",
                "current_stage": "received",
                "workflow_events": [],
            }
        )
        return PlanningResult(
            request_id=request_id,
            status=state["status"],
            plan=ResearchPlan.model_validate(state["research_plan"]),
            workflow_events=state["workflow_events"],
            elapsed_ms=round((perf_counter() - started) * 1000, 3),
        )
