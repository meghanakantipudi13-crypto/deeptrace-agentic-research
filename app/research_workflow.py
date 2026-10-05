"""Single-pass Phase 2 LangGraph retrieval and verification workflow."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from app.logging import log_event
from app.models import (
    MAX_RESULTS_PER_QUERY,
    Citation,
    EvidenceVerification,
    ResearchPlan,
    ResearchResult,
    ResearchState,
    SearchQuery,
    Source,
    UsageMetadata,
)
from app.providers.base import PlanModel
from app.research import (
    generate_search_queries,
    normalize_and_deduplicate_sources,
    synthesize_preliminary_result,
    verify_sources,
)
from app.search.base import SearchProvider


class ResearchWorkflow:
    """Run exactly one retrieval pass and stop before critic/self-correction."""

    def __init__(self, plan_model: PlanModel, search_provider: SearchProvider) -> None:
        self._plan_model = plan_model
        self._search_provider = search_provider
        self._logger = logging.getLogger("deeptrace.research_workflow")
        builder = StateGraph(ResearchState)
        builder.add_node("start_workflow", self._start_workflow)
        builder.add_node("create_plan", self._create_plan)
        builder.add_node("generate_queries", self._generate_queries)
        builder.add_node("retrieve_sources", self._retrieve_sources)
        builder.add_node("verify_evidence", self._verify_evidence)
        builder.add_node("synthesize_preliminary_result", self._synthesize)
        builder.add_node("finish_workflow", self._finish_workflow)
        builder.add_edge(START, "start_workflow")
        builder.add_edge("start_workflow", "create_plan")
        builder.add_edge("create_plan", "generate_queries")
        builder.add_edge("generate_queries", "retrieve_sources")
        builder.add_edge("retrieve_sources", "verify_evidence")
        builder.add_edge("verify_evidence", "synthesize_preliminary_result")
        builder.add_edge("synthesize_preliminary_result", "finish_workflow")
        builder.add_edge("finish_workflow", END)
        self.graph = builder.compile()

    def _started(self, state: ResearchState, stage: str) -> float:
        log_event(
            self._logger,
            "workflow_stage_started",
            request_id=state["request_id"],
            stage=stage,
        )
        return perf_counter()

    def _completed(
        self,
        state: ResearchState,
        stage: str,
        started: float,
        **fields: object,
    ) -> dict[str, float]:
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        log_event(
            self._logger,
            "workflow_stage_completed",
            request_id=state["request_id"],
            stage=stage,
            node_latency_ms=elapsed_ms,
            **fields,
        )
        return {**state.get("node_latencies_ms", {}), stage: elapsed_ms}

    async def _start_workflow(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "start_workflow")
        return {
            "status": "planning",
            "current_stage": "start_workflow",
            "node_latencies_ms": self._completed(state, "start_workflow", started),
            "workflow_events": [*state.get("workflow_events", []), "workflow_started"],
        }

    async def _create_plan(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "create_plan")
        plan = await self._plan_model.create_plan(state["question"])
        return {
            "research_plan": plan.model_dump(mode="json"),
            "current_stage": "create_plan",
            "usage": {"external_model_calls": 0 if plan.is_simulated else 1},
            "node_latencies_ms": self._completed(
                state,
                "create_plan",
                started,
                simulated=plan.is_simulated,
                step_count=len(plan.steps),
            ),
            "workflow_events": [*state.get("workflow_events", []), "planning_completed"],
        }

    async def _generate_queries(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "generate_queries")
        plan = ResearchPlan.model_validate(state["research_plan"])
        queries = generate_search_queries(state["question"], plan)
        return {
            "search_queries": [query.model_dump(mode="json") for query in queries],
            "current_stage": "generate_queries",
            "node_latencies_ms": self._completed(
                state,
                "generate_queries",
                started,
                query_count=len(queries),
            ),
            "workflow_events": [*state.get("workflow_events", []), "queries_generated"],
        }

    async def _retrieve_sources(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "retrieve_sources")
        queries = [SearchQuery.model_validate(item) for item in state["search_queries"]]
        collected = []
        results_received = 0
        credits: float | None = None
        for query in queries:
            batch = await self._search_provider.search(query.text, MAX_RESULTS_PER_QUERY)
            results_received += len(batch.results)
            collected.extend((query, result) for result in batch.results)
            if batch.credits_used is not None:
                credits = (credits or 0) + batch.credits_used
        sources, duplicates_removed = normalize_and_deduplicate_sources(
            collected,
            is_simulated=self._search_provider.is_simulated,
        )
        prior_usage = state.get("usage", {})
        usage = {
            **prior_usage,
            "query_count": len(queries),
            "search_calls": len(queries),
            "search_results_received": results_received,
            "sources_retained": len(sources),
            "duplicates_removed": duplicates_removed,
            "retrieval_passes": 1,
            "provider_credits_used": credits,
        }
        return {
            "sources": [source.model_dump(mode="json") for source in sources],
            "usage": usage,
            "current_stage": "retrieve_sources",
            "node_latencies_ms": self._completed(
                state,
                "retrieve_sources",
                started,
                provider=self._search_provider.provider_name,
                search_calls=len(queries),
                results_received=results_received,
                sources_retained=len(sources),
                duplicates_removed=duplicates_removed,
            ),
            "workflow_events": [*state.get("workflow_events", []), "retrieval_completed"],
        }

    async def _verify_evidence(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "verify_evidence")
        plan = ResearchPlan.model_validate(state["research_plan"])
        sources = [Source.model_validate(item) for item in state["sources"]]
        verifications = verify_sources(state["question"], plan, sources)
        accepted = sum(item.accepted_for_synthesis for item in verifications)
        return {
            "evidence_verifications": [item.model_dump(mode="json") for item in verifications],
            "current_stage": "verify_evidence",
            "node_latencies_ms": self._completed(
                state,
                "verify_evidence",
                started,
                relevant_count=sum(item.relevant for item in verifications),
                accepted_count=accepted,
                rejected_count=len(verifications) - accepted,
            ),
            "workflow_events": [*state.get("workflow_events", []), "verification_completed"],
        }

    async def _synthesize(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "synthesize_preliminary_result")
        sources = [Source.model_validate(item) for item in state["sources"]]
        verifications = [
            EvidenceVerification.model_validate(item)
            for item in state["evidence_verifications"]
        ]
        preliminary, citations = synthesize_preliminary_result(
            state["question"], sources, verifications
        )
        return {
            "preliminary_result": preliminary.model_dump(mode="json"),
            "citations": [citation.model_dump(mode="json") for citation in citations],
            "current_stage": "synthesize_preliminary_result",
            "node_latencies_ms": self._completed(
                state,
                "synthesize_preliminary_result",
                started,
                claim_count=len(preliminary.claims),
                citation_count=len(citations),
            ),
            "workflow_events": [*state.get("workflow_events", []), "synthesis_completed"],
        }

    async def _finish_workflow(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "finish_workflow")
        return {
            "status": "preliminary_result_ready",
            "current_stage": "finish_workflow",
            "node_latencies_ms": self._completed(
                state,
                "finish_workflow",
                started,
                boundary="single_retrieval_pass_complete",
            ),
            "workflow_events": [*state.get("workflow_events", []), "workflow_completed"],
        }

    async def run(self, question: str) -> ResearchResult:
        request_id = str(uuid4())
        started = perf_counter()
        state = await self.graph.ainvoke(
            {
                "request_id": request_id,
                "question": question,
                "status": "received",
                "current_stage": "received",
                "usage": {},
                "node_latencies_ms": {},
                "workflow_events": [],
            }
        )
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        usage = state.get("usage", {})
        return ResearchResult(
            request_id=request_id,
            status=state["status"],
            plan=ResearchPlan.model_validate(state["research_plan"]),
            queries=[SearchQuery.model_validate(item) for item in state["search_queries"]],
            sources=[Source.model_validate(item) for item in state["sources"]],
            verifications=[
                EvidenceVerification.model_validate(item)
                for item in state["evidence_verifications"]
            ],
            citations=[Citation.model_validate(item) for item in state["citations"]],
            preliminary_result=state["preliminary_result"],
            usage=UsageMetadata(
                query_count=usage.get("query_count", 0),
                search_calls=usage.get("search_calls", 0),
                search_results_received=usage.get("search_results_received", 0),
                sources_retained=usage.get("sources_retained", 0),
                duplicates_removed=usage.get("duplicates_removed", 0),
                retrieval_passes=usage.get("retrieval_passes", 0),
                external_model_calls=usage.get("external_model_calls", 0),
                provider_credits_used=usage.get("provider_credits_used"),
                node_latencies_ms=state.get("node_latencies_ms", {}),
                total_latency_ms=elapsed_ms,
            ),
            workflow_events=state["workflow_events"],
            search_provider_label=self._search_provider.provider_name,
            search_is_simulated=self._search_provider.is_simulated,
            elapsed_ms=elapsed_ms,
        )
