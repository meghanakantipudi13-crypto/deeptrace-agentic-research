from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from app.memory import (
    FileSystemResearchMemory,
    MemoryCorruptionError,
    MemoryNotFoundError,
    record_from_outcome,
)
from app.models import (
    ApprovalResumePayload,
    PlanStep,
    ProviderSearchResult,
    ResearchPlan,
    ResearchResult,
    SearchBatch,
)
from app.research_workflow import ResearchWorkflow


class MemoryPlanModel:
    async def create_plan(self, question: str) -> ResearchPlan:
        return ResearchPlan(
            question=question,
            objective="Persist a deterministic result.",
            steps=[
                PlanStep(
                    order=1,
                    title="Durable evidence",
                    purpose="Verify durable memory behavior.",
                    evidence_needed=["Persistent primary evidence"],
                )
            ],
            provider_label="memory-test-planner",
            is_simulated=True,
        )


class MemorySearchProvider:
    provider_name = "memory-test-search"
    is_simulated = True

    async def search(self, query: str, limit: int) -> SearchBatch:
        return SearchBatch(
            results=[
                ProviderSearchResult(
                    title="Durable memory source",
                    url="https://memory.test/source",
                    content=(
                        "Persistent primary evidence provides a detailed verified method, "
                        "measurement result, limitation, and implementation context."
                    ),
                    provider=self.provider_name,
                    rank=1,
                    provider_score=0.95,
                )
            ]
        )


def _completed_record(question: str = "Does durable memory survive restart?"):
    async def execute():
        workflow = ResearchWorkflow(MemoryPlanModel(), MemorySearchProvider())
        pending = await workflow.start(question)
        outcome = await workflow.resume(
            pending.workflow_id, ApprovalResumePayload(decision="approve")
        )
        assert isinstance(outcome, ResearchResult)
        return record_from_outcome(outcome)

    return asyncio.run(execute())


def test_scenario_a_completed_research_persists_in_new_repository(tmp_path: Path) -> None:
    record = _completed_record()
    first = FileSystemResearchMemory(tmp_path)
    asyncio.run(first.save(record))

    second = FileSystemResearchMemory(tmp_path)
    loaded = asyncio.run(second.get(record.session_id))

    assert loaded.question == record.question
    assert loaded.plan == record.plan
    assert loaded.report == record.report
    assert loaded.citations == record.citations
    assert {item.source_id for item in loaded.sources} == {
        item.source_id for item in loaded.citations
    }


def test_scenario_b_history_is_newest_first_with_summary_metadata(tmp_path: Path) -> None:
    older = _completed_record("Older durable question?")
    newer = _completed_record("Newer durable question?")
    older = older.model_copy(update={"stored_at": datetime.now(UTC) - timedelta(days=1)})
    newer = newer.model_copy(update={"stored_at": datetime.now(UTC)})
    repository = FileSystemResearchMemory(tmp_path)
    asyncio.run(repository.save(older))
    asyncio.run(repository.save(newer))

    history = asyncio.run(repository.list_recent())

    assert [item.session_id for item in history] == [newer.session_id, older.session_id]
    assert history[0].question == "Newer durable question?"
    assert history[0].status == "completed"
    assert history[0].termination_reason == newer.termination_reason
    assert history[0].retrieval_passes == newer.usage.retrieval_passes


def test_scenario_c_known_and_unknown_session_retrieval(tmp_path: Path) -> None:
    record = _completed_record()
    repository = FileSystemResearchMemory(tmp_path)
    asyncio.run(repository.save(record))

    assert asyncio.run(repository.get(record.session_id)).session_id == record.session_id
    with pytest.raises(MemoryNotFoundError, match="not found"):
        asyncio.run(repository.get(str(uuid4())))


def test_scenario_d_restart_uses_no_python_global(tmp_path: Path) -> None:
    record = _completed_record()
    asyncio.run(FileSystemResearchMemory(tmp_path).save(record))

    del record
    recreated = FileSystemResearchMemory(Path(str(tmp_path)))
    history = asyncio.run(recreated.list_recent())

    assert len(history) == 1
    assert (tmp_path / f"{history[0].session_id}.json").is_file()


def test_scenario_e_cancelled_record_has_no_research_output(tmp_path: Path) -> None:
    async def cancel():
        workflow = ResearchWorkflow(MemoryPlanModel(), MemorySearchProvider())
        pending = await workflow.start("Cancel this durable workflow?")
        return await workflow.resume(
            pending.workflow_id, ApprovalResumePayload(decision="reject")
        )

    record = record_from_outcome(asyncio.run(cancel()))
    repository = FileSystemResearchMemory(tmp_path)
    asyncio.run(repository.save(record))
    loaded = asyncio.run(FileSystemResearchMemory(tmp_path).get(record.session_id))

    assert loaded.status == "cancelled"
    assert loaded.termination_reason == "human_cancelled"
    assert loaded.report is None
    assert loaded.citations == []
    assert loaded.sources == []
    assert loaded.usage is None


def test_scenario_f_malformed_record_fails_safely(tmp_path: Path) -> None:
    session_id = str(uuid4())
    (tmp_path / f"{session_id}.json").write_text(
        '{"schema_version": 1, "session_id": "not-valid"}', encoding="utf-8"
    )
    repository = FileSystemResearchMemory(tmp_path)

    with pytest.raises(MemoryCorruptionError, match="invalid"):
        asyncio.run(repository.get(session_id))
    assert asyncio.run(repository.list_recent()) == []


@pytest.mark.parametrize(
    "unsafe_id",
    ["../secrets", "..\\secrets", "/absolute/path", "not-a-uuid", str(uuid4()).upper()],
)
def test_scenario_g_unsafe_identifiers_are_rejected(
    tmp_path: Path, unsafe_id: str
) -> None:
    repository = FileSystemResearchMemory(tmp_path)
    with pytest.raises(MemoryNotFoundError):
        asyncio.run(repository.get(unsafe_id))
