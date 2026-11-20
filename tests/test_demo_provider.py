from __future__ import annotations

import asyncio

import pytest

from app.models import ApprovalResumePayload
from app.providers.deterministic import DeterministicPlanModel
from app.research_workflow import ResearchWorkflow
from app.search.demo import CorrectionDemoSearchProvider
from app.search.factory import build_search_provider


def test_demo_provider_triggers_visible_correction_and_quarantine() -> None:
    workflow = ResearchWorkflow(
        DeterministicPlanModel(),
        CorrectionDemoSearchProvider(),
    )

    async def execute():
        pending = await workflow.start("How should a public research claim be verified?")
        return await workflow.resume(
            pending.workflow_id,
            ApprovalResumePayload(decision="approve"),
        )

    result = asyncio.run(execute())

    assert result.usage.retrieval_passes == 2
    assert result.usage.correction_iterations == 1
    assert [decision.is_sufficient for decision in result.critic_history] == [False, True]
    assert result.iterations[0].route_selected == "revise_queries"
    assert result.iterations[1].route_selected == "synthesize"
    assert any(source.instruction_like for source in result.sources)
    quarantined = {event.subject_id for event in result.safety_events}
    cited = {citation.source_id for citation in result.citations}
    assert quarantined
    assert quarantined.isdisjoint(cited)


def test_demo_provider_is_refused_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPTRACE_ENV", "production")
    monkeypatch.setenv("SEARCH_PROVIDER", "demo-correction")

    with pytest.raises(RuntimeError, match="cannot run in production"):
        build_search_provider()
