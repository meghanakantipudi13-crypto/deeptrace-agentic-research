from __future__ import annotations

import asyncio

from app.models import PlanStep, ResearchPlan
from app.validation import normalize_question
from app.workflow import PlanningWorkflow


class WorkflowSpyModel:
    def __init__(self) -> None:
        self.calls = 0

    async def create_plan(self, question: str) -> ResearchPlan:
        self.calls += 1
        return ResearchPlan(
            question=question,
            objective="Create a testable plan",
            steps=[
                PlanStep(
                    order=1,
                    title="Inspect the question",
                    purpose="Produce structured planning output.",
                    evidence_needed=["Definitions"],
                )
            ],
            provider_label="Workflow spy",
            is_simulated=True,
        )


def test_langgraph_planning_node_executes_and_stops_at_phase_boundary() -> None:
    model = WorkflowSpyModel()
    workflow = PlanningWorkflow(model)

    result = asyncio.run(workflow.run("How should evidence be evaluated?"))

    assert model.calls == 1
    assert result.status == "plan_ready"
    assert result.plan.question == "How should evidence be evaluated?"
    assert result.plan.steps[0].title == "Inspect the question"
    assert result.workflow_events == [
        "workflow_started",
        "planning_started",
        "planning_completed",
        "workflow_completed",
    ]
    assert "retrieved_sources" not in result.model_dump()
    assert "evidence" not in result.model_dump()


def test_compiled_graph_contains_only_phase_one_nodes() -> None:
    workflow = PlanningWorkflow(WorkflowSpyModel())
    graph_nodes = set(workflow.graph.get_graph().nodes)

    assert {"start_workflow", "create_plan", "finish_workflow"}.issubset(graph_nodes)
    assert "retrieve" not in graph_nodes
    assert "verify" not in graph_nodes
    assert "critic" not in graph_nodes


def test_question_normalization_handles_unicode_and_controls() -> None:
    assert normalize_question("  What\u00a0is\x00 evidence?\n") == "What is evidence?"
