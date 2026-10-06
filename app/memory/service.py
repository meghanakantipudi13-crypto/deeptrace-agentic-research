"""Convert terminal workflows into durable, privacy-bounded memory records."""

from __future__ import annotations

from datetime import UTC, datetime

from app.memory.models import ResearchMemoryRecord, StoredSourceMetadata
from app.models import CancelledResearchResult, ResearchResult


def record_from_outcome(
    outcome: ResearchResult | CancelledResearchResult,
) -> ResearchMemoryRecord:
    """Persist completed reports and explicit cancellation metadata, never failures."""

    if isinstance(outcome, CancelledResearchResult):
        return ResearchMemoryRecord(
            session_id=outcome.workflow_id,
            created_at=outcome.created_at,
            stored_at=datetime.now(UTC),
            status="cancelled",
            question=outcome.question,
            plan=outcome.plan,
            approval_decision="reject",
            plan_modified=False,
            provider_mode="simulated" if outcome.plan.is_simulated else "real",
            provider_label=outcome.plan.provider_label,
            termination_reason="human_cancelled",
        )
    return ResearchMemoryRecord(
        session_id=outcome.request_id,
        created_at=outcome.created_at,
        stored_at=datetime.now(UTC),
        status="completed",
        question=outcome.plan.question,
        plan=outcome.plan,
        approval_decision=outcome.approval_decision,
        plan_modified=outcome.plan_modified,
        provider_mode="simulated" if outcome.search_is_simulated else "real",
        provider_label=outcome.search_provider_label,
        termination_reason=outcome.termination_reason,
        report=outcome.preliminary_result,
        citations=outcome.citations,
        sources=[
            StoredSourceMetadata(
                source_id=source.source_id,
                title=source.title,
                url=source.url,
                provider=source.provider,
                retrieved_at=source.retrieved_at,
                is_simulated=source.is_simulated,
            )
            for source in outcome.sources
        ],
        usage=outcome.usage,
    )
