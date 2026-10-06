from __future__ import annotations

import asyncio
from pathlib import Path

from app.models import ApprovalResumePayload, ResearchResult
from app.research_workflow import ResearchWorkflow
from tests.test_hitl_workflow import ApprovalPlanModel, ApprovalSearchProvider, QUESTION


def test_sqlite_checkpoint_recovers_interrupt_in_new_workflow_instance(
    tmp_path: Path,
) -> None:
    async def execute():
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

        database = str(tmp_path / "checkpoints.sqlite")
        first_search = ApprovalSearchProvider()
        async with AsyncSqliteSaver.from_conn_string(database) as first_saver:
            first_workflow = ResearchWorkflow(
                ApprovalPlanModel(), first_search, checkpointer=first_saver
            )
            pending = await first_workflow.start(QUESTION)
        assert first_search.calls == []

        second_search = ApprovalSearchProvider()
        async with AsyncSqliteSaver.from_conn_string(database) as second_saver:
            second_workflow = ResearchWorkflow(
                ApprovalPlanModel(), second_search, checkpointer=second_saver
            )
            recovered = await second_workflow.get_pending(pending.workflow_id)
            result = await second_workflow.resume(
                pending.workflow_id, ApprovalResumePayload(decision="approve")
            )
        return pending, recovered, result, second_search

    pending, recovered, result, search = asyncio.run(execute())

    assert recovered.workflow_id == pending.workflow_id
    assert recovered.interrupt_id == pending.interrupt_id
    assert isinstance(result, ResearchResult)
    assert result.request_id == pending.workflow_id
    assert search.calls
