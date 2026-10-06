from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from app.models import (
    ApprovalResumePayload,
    CancelledResearchResult,
    PlanStep,
    ProviderSearchResult,
    ResearchPlan,
    ResearchResult,
    SearchBatch,
)
from app.research_workflow import (
    ResearchWorkflow,
    WorkflowNotAwaitingApprovalError,
    WorkflowNotFoundError,
)


QUESTION = "How should a city evaluate cooling interventions?"


class ApprovalPlanModel:
    async def create_plan(self, question: str) -> ResearchPlan:
        return ResearchPlan(
            question=question,
            objective="Evaluate cooling interventions",
            steps=[
                PlanStep(
                    order=1,
                    title="Original cooling metric",
                    purpose="Define a comparable cooling metric.",
                    evidence_needed=["Measured cooling evidence"],
                )
            ],
            provider_label="approval-test-planner",
            is_simulated=True,
        )


class ApprovalSearchProvider:
    provider_name = "approval-test-search"
    is_simulated = True

    def __init__(self) -> None:
        self.calls: list[str] = []

    async def search(self, query: str, limit: int) -> SearchBatch:
        self.calls.append(query)
        return SearchBatch(
            results=[
                ProviderSearchResult(
                    title=f"Evidence for {query[:80]}",
                    url=f"https://approval.test/source-{len(self.calls)}",
                    content=(
                        f"Measured cooling evidence for {query} provides a detailed comparable "
                        "evaluation method, observation period, and uncertainty statement."
                    ),
                    provider=self.provider_name,
                    rank=1,
                    provider_score=0.9,
                )
            ]
        )


def _workflow() -> tuple[ResearchWorkflow, ApprovalSearchProvider]:
    search = ApprovalSearchProvider()
    return ResearchWorkflow(ApprovalPlanModel(), search), search


def test_scenario_a_workflow_really_interrupts_before_research() -> None:
    workflow, search = _workflow()

    async def execute():
        pending = await workflow.start(QUESTION)
        snapshot = await workflow.graph.aget_state(
            {"configurable": {"thread_id": pending.workflow_id}}
        )
        return pending, snapshot

    pending, snapshot = asyncio.run(execute())

    assert pending.status == "awaiting_approval"
    assert pending.interrupt_id
    assert pending.approval_payload.workflow_id == pending.workflow_id
    assert pending.approval_payload.plan_item_count == 1
    assert "No external research has been performed" in pending.approval_payload.explanation
    assert "approval_checkpoint" in snapshot.next
    assert any(task.interrupts for task in snapshot.tasks)
    assert "search_queries" not in snapshot.values
    assert search.calls == []


def test_scenario_b_approve_resumes_same_workflow() -> None:
    workflow, search = _workflow()

    async def execute():
        pending = await workflow.start(QUESTION)
        result = await workflow.resume(
            pending.workflow_id,
            ApprovalResumePayload(decision="approve"),
        )
        return pending, result

    pending, result = asyncio.run(execute())

    assert isinstance(result, ResearchResult)
    assert result.request_id == pending.workflow_id
    assert result.plan == pending.plan
    assert result.approval_decision == "approve"
    assert result.plan_modified is False
    assert search.calls
    assert result.status == "research_result_ready"


def test_scenario_c_modified_plan_changes_downstream_queries() -> None:
    workflow, search = _workflow()
    modified_step = PlanStep(
        order=1,
        title="Human-edited cooling equity evidence",
        purpose="Compare cooling outcomes across vulnerable neighborhoods.",
        evidence_needed=["Neighborhood cooling equity measurements"],
    )

    async def execute():
        pending = await workflow.start(QUESTION)
        return await workflow.resume(
            pending.workflow_id,
            ApprovalResumePayload(decision="modify", modified_steps=[modified_step]),
        )

    result = asyncio.run(execute())

    assert isinstance(result, ResearchResult)
    assert result.approval_decision == "modify"
    assert result.plan_modified is True
    assert result.plan.steps == [modified_step]
    assert "Human-edited cooling equity evidence" in result.queries[0].text
    assert "Human-edited cooling equity evidence" in search.calls[0]
    assert "plan_modified" in result.workflow_events


def test_scenario_d_reject_cancels_without_search_or_result() -> None:
    workflow, search = _workflow()

    async def execute():
        pending = await workflow.start(QUESTION)
        result = await workflow.resume(
            pending.workflow_id,
            ApprovalResumePayload(decision="reject"),
        )
        with pytest.raises(WorkflowNotAwaitingApprovalError):
            await workflow.resume(
                pending.workflow_id,
                ApprovalResumePayload(decision="approve"),
            )
        return result

    result = asyncio.run(execute())

    assert isinstance(result, CancelledResearchResult)
    assert result.status == "cancelled"
    assert result.search_calls == 0
    assert search.calls == []
    assert "workflow_cancelled" in result.workflow_events


def test_scenario_e_invalid_resume_is_rejected() -> None:
    workflow, search = _workflow()

    with pytest.raises(WorkflowNotFoundError, match="Unknown workflow ID"):
        asyncio.run(
            workflow.resume(
                "not-a-workflow-id",
                ApprovalResumePayload(decision="approve"),
            )
        )

    with pytest.raises(ValidationError, match="modified plan"):
        ApprovalResumePayload(decision="modify", modified_steps=None)
    with pytest.raises(ValidationError, match="Input should be"):
        ApprovalResumePayload.model_validate({"decision": "bypass"})
    assert search.calls == []


def test_scenario_f_duplicate_approval_does_not_repeat_research() -> None:
    workflow, search = _workflow()

    async def execute():
        pending = await workflow.start(QUESTION)
        await workflow.resume(
            pending.workflow_id,
            ApprovalResumePayload(decision="approve"),
        )
        calls_after_first = len(search.calls)
        with pytest.raises(
            WorkflowNotAwaitingApprovalError,
            match="not awaiting approval",
        ):
            await workflow.resume(
                pending.workflow_id,
                ApprovalResumePayload(decision="approve"),
            )
        return calls_after_first

    calls_after_first = asyncio.run(execute())

    assert len(search.calls) == calls_after_first
    assert calls_after_first == 1
