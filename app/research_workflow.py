"""Phase 4 interruptible research workflow with bounded self-correction."""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from uuid import UUID, uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.logging import log_event
from app.models import (
    MAX_RESEARCH_ITERATIONS,
    MAX_RESULTS_PER_QUERY,
    ApprovalInterruptPayload,
    ApprovalResumePayload,
    CancelledResearchResult,
    Citation,
    EvidenceSufficiency,
    EvidenceVerification,
    PendingResearchResult,
    ResearchIterationTrace,
    ResearchPlan,
    ResearchResult,
    ResearchState,
    SearchQuery,
    Source,
    UsageMetadata,
)
from app.providers.base import PlanModel
from app.research import (
    evaluate_evidence_sufficiency,
    generate_followup_queries,
    generate_search_queries,
    normalize_and_deduplicate_sources,
    synthesize_preliminary_result,
    verify_sources,
)
from app.search.base import SearchProvider


class WorkflowNotFoundError(LookupError):
    """Raised when a workflow ID has no checkpoint in this process."""


class WorkflowNotAwaitingApprovalError(RuntimeError):
    """Raised for duplicate, completed, cancelled, or otherwise invalid resumes."""


class ResearchWorkflow:
    """Pause after planning and resume only through a validated human decision."""

    def __init__(
        self,
        plan_model: PlanModel,
        search_provider: SearchProvider,
        *,
        max_research_iterations: int = MAX_RESEARCH_ITERATIONS,
    ) -> None:
        self._plan_model = plan_model
        self._search_provider = search_provider
        self._max_research_iterations = max(
            1, min(max_research_iterations, MAX_RESEARCH_ITERATIONS)
        )
        self._logger = logging.getLogger("deeptrace.research_workflow")
        self._checkpointer = InMemorySaver()
        self._resume_lock = asyncio.Lock()
        builder = StateGraph(ResearchState)
        builder.add_node("start_workflow", self._start_workflow)
        builder.add_node("create_plan", self._create_plan)
        builder.add_node("request_approval", self._request_approval)
        builder.add_node("approval_checkpoint", self._approval_checkpoint)
        builder.add_node("cancel_workflow", self._cancel_workflow)
        builder.add_node("generate_queries", self._generate_queries)
        builder.add_node("retrieve_sources", self._retrieve_sources)
        builder.add_node("verify_evidence", self._verify_evidence)
        builder.add_node("critic", self._critic)
        builder.add_node("revise_queries", self._revise_queries)
        builder.add_node("synthesize_research_result", self._synthesize)
        builder.add_node("finish_workflow", self._finish_workflow)
        builder.add_edge(START, "start_workflow")
        builder.add_edge("start_workflow", "create_plan")
        builder.add_edge("create_plan", "request_approval")
        builder.add_edge("request_approval", "approval_checkpoint")
        builder.add_conditional_edges(
            "approval_checkpoint",
            self._route_after_approval,
            {"research": "generate_queries", "cancel": "cancel_workflow"},
        )
        builder.add_edge("cancel_workflow", END)
        builder.add_edge("generate_queries", "retrieve_sources")
        builder.add_edge("retrieve_sources", "verify_evidence")
        builder.add_edge("verify_evidence", "critic")
        builder.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {
                "revise_queries": "revise_queries",
                "synthesize": "synthesize_research_result",
            },
        )
        builder.add_conditional_edges(
            "revise_queries",
            self._route_after_revision,
            {
                "retrieve_sources": "retrieve_sources",
                "synthesize": "synthesize_research_result",
            },
        )
        builder.add_edge("synthesize_research_result", "finish_workflow")
        builder.add_edge("finish_workflow", END)
        self.graph = builder.compile(checkpointer=self._checkpointer)

    def _started(self, state: ResearchState, stage: str) -> float:
        log_event(
            self._logger,
            "workflow_stage_started",
            request_id=state["request_id"],
            stage=stage,
            iteration=state.get("retrieval_iteration", 1),
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
            iteration=state.get("retrieval_iteration", 1),
            node_latency_ms=elapsed_ms,
            **fields,
        )
        latency_key = f"{stage}_iteration_{state.get('retrieval_iteration', 1)}"
        return {**state.get("node_latencies_ms", {}), latency_key: elapsed_ms}

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

    async def _request_approval(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "request_approval")
        plan = ResearchPlan.model_validate(state["research_plan"])
        log_event(
            self._logger,
            "approval_requested",
            request_id=state["request_id"],
            plan_item_count=len(plan.steps),
        )
        return {
            "status": "awaiting_approval",
            "current_stage": "request_approval",
            "node_latencies_ms": self._completed(
                state,
                "request_approval",
                started,
                plan_item_count=len(plan.steps),
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                "approval_requested",
                "workflow_interrupted",
            ],
        }

    async def _approval_checkpoint(self, state: ResearchState) -> ResearchState:
        plan = ResearchPlan.model_validate(state["research_plan"])
        payload = ApprovalInterruptPayload(
            workflow_id=state["request_id"],
            question=state["question"],
            proposed_plan=plan,
            plan_item_count=len(plan.steps),
            provider_mode=(
                "simulated"
                if plan.is_simulated or self._search_provider.is_simulated
                else "real"
            ),
            explanation=(
                "No external research has been performed. Approval will generate queries "
                "and begin the bounded iterative retrieval workflow."
            ),
        )
        response = interrupt(
            payload.model_dump(mode="json"),
            response_schema=ApprovalResumePayload,
        )
        decision = ApprovalResumePayload.model_validate(response)
        plan_modified = decision.decision == "modify"
        if plan_modified:
            plan = ResearchPlan.model_validate(
                {
                    **plan.model_dump(mode="json"),
                    "steps": [
                        step.model_dump(mode="json")
                        for step in decision.modified_steps or []
                    ],
                }
            )
        events = [*state.get("workflow_events", []), "approval_received"]
        if plan_modified:
            events.append("plan_modified")
            log_event(
                self._logger,
                "plan_modified",
                request_id=state["request_id"],
                plan_item_count=len(plan.steps),
            )
        if decision.decision == "reject":
            events.append("workflow_rejected")
            status = "rejected"
            log_event(
                self._logger,
                "workflow_rejected",
                request_id=state["request_id"],
            )
        else:
            events.append("workflow_resumed")
            status = "approved"
            log_event(
                self._logger,
                "workflow_resumed",
                request_id=state["request_id"],
                decision=decision.decision,
            )
        log_event(
            self._logger,
            "approval_received",
            request_id=state["request_id"],
            decision=decision.decision,
            plan_modified=plan_modified,
            plan_item_count=len(plan.steps),
        )
        return {
            "research_plan": plan.model_dump(mode="json"),
            "approval_decision": decision.decision,
            "plan_modified": plan_modified,
            "status": status,
            "current_stage": "approval_checkpoint",
            "workflow_events": events,
        }

    def _route_after_approval(self, state: ResearchState) -> str:
        return "cancel" if state.get("approval_decision") == "reject" else "research"

    async def _cancel_workflow(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "cancel_workflow")
        log_event(
            self._logger,
            "workflow_cancelled",
            request_id=state["request_id"],
            search_calls=state.get("usage", {}).get("search_calls", 0),
        )
        return {
            "status": "cancelled",
            "current_stage": "cancel_workflow",
            "node_latencies_ms": self._completed(
                state,
                "cancel_workflow",
                started,
                search_calls=state.get("usage", {}).get("search_calls", 0),
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                "workflow_cancelled",
            ],
        }

    async def _generate_queries(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "generate_queries")
        plan = ResearchPlan.model_validate(state["research_plan"])
        queries = generate_search_queries(state["question"], plan)
        serialized = [query.model_dump(mode="json") for query in queries]
        return {
            "search_queries": serialized,
            "active_search_queries": serialized,
            "current_stage": "generate_queries",
            "node_latencies_ms": self._completed(
                state, "generate_queries", started, query_count=len(queries)
            ),
            "workflow_events": [*state.get("workflow_events", []), "queries_generated"],
        }

    async def _retrieve_sources(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "retrieve_sources")
        iteration = state["retrieval_iteration"]
        queries = [
            SearchQuery.model_validate(item) for item in state["active_search_queries"]
        ]
        existing = [Source.model_validate(item) for item in state.get("sources", [])]
        collected = []
        results_received = 0
        calls_attempted = 0
        credits: float | None = None
        provider_failed = False
        for query in queries:
            calls_attempted += 1
            try:
                batch = await self._search_provider.search(query.text, MAX_RESULTS_PER_QUERY)
            except Exception:
                provider_failed = True
                log_event(
                    self._logger,
                    "search_provider_failed",
                    request_id=state["request_id"],
                    provider=self._search_provider.provider_name,
                    iteration=iteration,
                )
                break
            results_received += len(batch.results)
            collected.extend((query, result) for result in batch.results)
            if batch.credits_used is not None:
                credits = (credits or 0) + batch.credits_used
        new_sources, duplicates_removed = normalize_and_deduplicate_sources(
            collected,
            is_simulated=self._search_provider.is_simulated,
            existing_sources=existing,
            retrieval_iteration=iteration,
        )
        sources = [*existing, *new_sources]
        prior_usage = state.get("usage", {})
        previous_credits = prior_usage.get("provider_credits_used")
        total_credits = None
        if previous_credits is not None or credits is not None:
            total_credits = (previous_credits or 0) + (credits or 0)
        usage = {
            **prior_usage,
            "query_count": len(state["search_queries"]),
            "search_calls": prior_usage.get("search_calls", 0) + calls_attempted,
            "search_results_received": (
                prior_usage.get("search_results_received", 0) + results_received
            ),
            "sources_retained": len(sources),
            "duplicates_removed": (
                prior_usage.get("duplicates_removed", 0) + duplicates_removed
            ),
            "retrieval_passes": iteration,
            "provider_credits_used": total_credits,
        }
        return {
            "sources": [source.model_dump(mode="json") for source in sources],
            "new_source_ids": [source.source_id for source in new_sources],
            "usage": usage,
            "termination_reason": (
                "provider_failure" if provider_failed else state.get("termination_reason")
            ),
            "current_stage": "retrieve_sources",
            "node_latencies_ms": self._completed(
                state,
                "retrieve_sources",
                started,
                provider=self._search_provider.provider_name,
                search_calls=calls_attempted,
                results_received=results_received,
                additional_sources=len(new_sources),
                duplicates_removed=duplicates_removed,
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                f"retrieval_iteration_{iteration}_completed",
            ],
        }

    async def _verify_evidence(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "verify_evidence")
        iteration = state["retrieval_iteration"]
        plan = ResearchPlan.model_validate(state["research_plan"])
        sources = [Source.model_validate(item) for item in state["sources"]]
        verifications = verify_sources(state["question"], plan, sources)
        new_ids = set(state.get("new_source_ids", []))
        accepted_added = sum(
            item.accepted_for_synthesis and item.source_id in new_ids
            for item in verifications
        )
        return {
            "evidence_verifications": [
                item.model_dump(mode="json") for item in verifications
            ],
            "iteration_accepted_added": accepted_added,
            "current_stage": "verify_evidence",
            "node_latencies_ms": self._completed(
                state,
                "verify_evidence",
                started,
                relevant_count=sum(item.relevant for item in verifications),
                accepted_total=sum(item.accepted_for_synthesis for item in verifications),
                additional_evidence_accepted=accepted_added,
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                f"verification_iteration_{iteration}_completed",
            ],
        }

    async def _critic(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "critic")
        iteration = state["retrieval_iteration"]
        plan = ResearchPlan.model_validate(state["research_plan"])
        sources = [Source.model_validate(item) for item in state["sources"]]
        verifications = [
            EvidenceVerification.model_validate(item)
            for item in state["evidence_verifications"]
        ]
        decision = evaluate_evidence_sufficiency(plan, sources, verifications, iteration)
        termination_reason = state.get("termination_reason")
        if termination_reason != "provider_failure":
            if decision.is_sufficient:
                termination_reason = "evidence_sufficient"
            elif iteration > 1 and not state.get("new_source_ids"):
                termination_reason = "no_new_evidence"
            elif iteration >= state["max_research_iterations"]:
                termination_reason = "max_iterations_reached"
            else:
                termination_reason = None
        route = "synthesize" if termination_reason else "revise_queries"
        active_queries = [
            SearchQuery.model_validate(item) for item in state["active_search_queries"]
        ]
        trace = ResearchIterationTrace(
            iteration=iteration,
            query_ids=[query.query_id for query in active_queries],
            query_count=len(active_queries),
            sources_added=len(state.get("new_source_ids", [])),
            accepted_added=state.get("iteration_accepted_added", 0),
            is_sufficient=decision.is_sufficient,
            evidence_gaps=[
                f"Plan item {gap.plan_step_order}: {gap.description}"
                for gap in decision.evidence_gaps
            ],
            route_selected=route,
        )
        prior_usage = state.get("usage", {})
        return {
            "critic_decision": decision.model_dump(mode="json"),
            "critic_history": [
                *state.get("critic_history", []),
                decision.model_dump(mode="json"),
            ],
            "iteration_traces": [
                *state.get("iteration_traces", []),
                trace.model_dump(mode="json"),
            ],
            "termination_reason": termination_reason,
            "usage": {
                **prior_usage,
                "critic_invocations": prior_usage.get("critic_invocations", 0) + 1,
            },
            "current_stage": "critic",
            "node_latencies_ms": self._completed(
                state,
                "critic",
                started,
                is_sufficient=decision.is_sufficient,
                confidence=decision.confidence,
                evidence_gap_count=len(decision.evidence_gaps),
                route_selected=route,
                termination_reason=termination_reason,
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                f"critic_iteration_{iteration}_{'sufficient' if decision.is_sufficient else 'insufficient'}",
            ],
        }

    def _route_after_critic(self, state: ResearchState) -> str:
        return "synthesize" if state.get("termination_reason") else "revise_queries"

    async def _revise_queries(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "revise_queries")
        plan = ResearchPlan.model_validate(state["research_plan"])
        critic = EvidenceSufficiency.model_validate(state["critic_decision"])
        previous = [SearchQuery.model_validate(item) for item in state["search_queries"]]
        next_iteration = state["retrieval_iteration"] + 1
        followups = generate_followup_queries(
            state["question"], plan, critic, previous, next_iteration
        )
        termination_reason = state.get("termination_reason")
        traces = list(state.get("iteration_traces", []))
        if not followups:
            termination_reason = "no_new_queries"
            if traces:
                traces[-1] = {**traces[-1], "route_selected": "synthesize"}
        serialized = [query.model_dump(mode="json") for query in followups]
        prior_usage = state.get("usage", {})
        return {
            "search_queries": [*state["search_queries"], *serialized],
            "active_search_queries": serialized,
            "retrieval_iteration": (
                next_iteration if followups else state["retrieval_iteration"]
            ),
            "termination_reason": termination_reason,
            "iteration_traces": traces,
            "usage": {
                **prior_usage,
                "correction_iterations": (
                    prior_usage.get("correction_iterations", 0) + (1 if followups else 0)
                ),
            },
            "current_stage": "revise_queries",
            "node_latencies_ms": self._completed(
                state,
                "revise_queries",
                started,
                followup_query_count=len(followups),
                route_selected="retrieve_sources" if followups else "synthesize",
                termination_reason=termination_reason,
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                (
                    f"queries_revised_for_iteration_{next_iteration}"
                    if followups
                    else "query_revision_produced_no_new_queries"
                ),
            ],
        }

    def _route_after_revision(self, state: ResearchState) -> str:
        return "retrieve_sources" if state.get("active_search_queries") else "synthesize"

    async def _synthesize(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "synthesize_research_result")
        sources = [Source.model_validate(item) for item in state["sources"]]
        verifications = [
            EvidenceVerification.model_validate(item)
            for item in state["evidence_verifications"]
        ]
        critic = EvidenceSufficiency.model_validate(state["critic_decision"])
        preliminary, citations = synthesize_preliminary_result(
            state["question"],
            sources,
            verifications,
            critic=critic,
            termination_reason=state["termination_reason"],
            retrieval_passes=state.get("usage", {}).get("retrieval_passes", 0),
        )
        return {
            "preliminary_result": preliminary.model_dump(mode="json"),
            "citations": [citation.model_dump(mode="json") for citation in citations],
            "current_stage": "synthesize_research_result",
            "node_latencies_ms": self._completed(
                state,
                "synthesize_research_result",
                started,
                claim_count=len(preliminary.claims),
                citation_count=len(citations),
                termination_reason=state["termination_reason"],
            ),
            "workflow_events": [
                *state.get("workflow_events", []),
                "synthesis_completed",
            ],
        }

    async def _finish_workflow(self, state: ResearchState) -> ResearchState:
        started = self._started(state, "finish_workflow")
        return {
            "status": "research_result_ready",
            "current_stage": "finish_workflow",
            "node_latencies_ms": self._completed(
                state,
                "finish_workflow",
                started,
                termination_reason=state["termination_reason"],
                retrieval_passes=state.get("usage", {}).get("retrieval_passes", 0),
            ),
            "workflow_events": [*state.get("workflow_events", []), "workflow_completed"],
        }

    def _config(self, workflow_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": workflow_id}}

    async def start(self, question: str) -> PendingResearchResult:
        """Create a thread and return only after LangGraph has genuinely interrupted."""

        workflow_id = str(uuid4())
        config = self._config(workflow_id)
        log_event(
            self._logger,
            "workflow_created",
            request_id=workflow_id,
        )
        await self.graph.ainvoke(
            {
                "request_id": workflow_id,
                "question": question,
                "status": "received",
                "current_stage": "received",
                "approval_decision": None,
                "plan_modified": False,
                "retrieval_iteration": 1,
                "max_research_iterations": self._max_research_iterations,
                "termination_reason": None,
                "sources": [],
                "critic_history": [],
                "iteration_traces": [],
                "usage": {},
                "node_latencies_ms": {},
                "workflow_events": ["workflow_created"],
            },
            config,
        )
        pending = await self.get_pending(workflow_id)
        log_event(
            self._logger,
            "workflow_interrupted",
            request_id=workflow_id,
            interrupt_id=pending.interrupt_id,
        )
        return pending

    async def get_pending(self, workflow_id: str) -> PendingResearchResult:
        """Read and validate an interrupted workflow without advancing it."""

        try:
            UUID(workflow_id)
        except (ValueError, TypeError) as error:
            raise WorkflowNotFoundError("Unknown workflow ID.") from error
        config = self._config(workflow_id)
        snapshot = await self.graph.aget_state(config)
        state = snapshot.values
        if not state:
            raise WorkflowNotFoundError("Unknown workflow ID.")
        interrupts = [item for task in snapshot.tasks for item in task.interrupts]
        if (
            state.get("status") != "awaiting_approval"
            or "approval_checkpoint" not in snapshot.next
            or len(interrupts) != 1
        ):
            log_event(
                self._logger,
                "duplicate_resume_rejected",
                request_id=workflow_id,
                current_status=state.get("status", "unknown"),
            )
            raise WorkflowNotAwaitingApprovalError(
                "Workflow is not awaiting approval."
            )
        approval_payload = ApprovalInterruptPayload.model_validate(interrupts[0].value)
        return PendingResearchResult(
            workflow_id=workflow_id,
            status="awaiting_approval",
            plan=ResearchPlan.model_validate(state["research_plan"]),
            approval_payload=approval_payload,
            interrupt_id=interrupts[0].id,
            workflow_events=state["workflow_events"],
        )

    async def resume(
        self,
        workflow_id: str,
        approval: ApprovalResumePayload,
    ) -> ResearchResult | CancelledResearchResult:
        """Resume one interrupted thread exactly once after integrity checks."""

        try:
            UUID(workflow_id)
        except (ValueError, TypeError) as error:
            raise WorkflowNotFoundError("Unknown workflow ID.") from error
        config = self._config(workflow_id)
        async with self._resume_lock:
            snapshot = await self.graph.aget_state(config)
            state = snapshot.values
            if not state:
                raise WorkflowNotFoundError("Unknown workflow ID.")
            has_interrupt = any(task.interrupts for task in snapshot.tasks)
            if (
                state.get("status") != "awaiting_approval"
                or "approval_checkpoint" not in snapshot.next
                or not has_interrupt
            ):
                log_event(
                    self._logger,
                    "duplicate_resume_rejected",
                    request_id=workflow_id,
                    current_status=state.get("status", "unknown"),
                )
                raise WorkflowNotAwaitingApprovalError(
                    "Workflow is not awaiting approval."
                )
            state = await self.graph.ainvoke(
                Command(resume=approval.model_dump(mode="json")),
                config,
            )
        if state["status"] == "cancelled":
            return CancelledResearchResult(
                workflow_id=workflow_id,
                status="cancelled",
                approval_decision="reject",
                question=state["question"],
                plan=ResearchPlan.model_validate(state["research_plan"]),
                search_calls=state.get("usage", {}).get("search_calls", 0),
                workflow_events=state["workflow_events"],
            )
        return self._build_research_result(state)

    def _build_research_result(self, state: ResearchState) -> ResearchResult:
        usage = state.get("usage", {})
        elapsed_ms = round(sum(state.get("node_latencies_ms", {}).values()), 3)
        return ResearchResult(
            request_id=state["request_id"],
            status=state["status"],
            plan=ResearchPlan.model_validate(state["research_plan"]),
            approval_decision=state["approval_decision"],
            plan_modified=state.get("plan_modified", False),
            queries=[SearchQuery.model_validate(item) for item in state["search_queries"]],
            sources=[Source.model_validate(item) for item in state["sources"]],
            verifications=[
                EvidenceVerification.model_validate(item)
                for item in state["evidence_verifications"]
            ],
            critic_history=[
                EvidenceSufficiency.model_validate(item)
                for item in state["critic_history"]
            ],
            iterations=[
                ResearchIterationTrace.model_validate(item)
                for item in state["iteration_traces"]
            ],
            termination_reason=state["termination_reason"],
            max_research_iterations=state["max_research_iterations"],
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
                critic_invocations=usage.get("critic_invocations", 0),
                correction_iterations=usage.get("correction_iterations", 0),
                provider_credits_used=usage.get("provider_credits_used"),
                node_latencies_ms=state.get("node_latencies_ms", {}),
                total_latency_ms=elapsed_ms,
            ),
            workflow_events=state["workflow_events"],
            search_provider_label=self._search_provider.provider_name,
            search_is_simulated=self._search_provider.is_simulated,
            elapsed_ms=elapsed_ms,
        )
