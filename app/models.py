"""Structured contracts shared by the web and workflow layers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field, model_validator


MAX_QUESTION_LENGTH = 500
MAX_INITIAL_QUERIES = 3
MAX_FOLLOWUP_QUERIES = 2
MAX_RESULTS_PER_QUERY = 3
MAX_TOTAL_SOURCES = 12
MAX_SOURCE_CONTENT_LENGTH = 1_500
MAX_RESEARCH_ITERATIONS = 2


class PlanStep(BaseModel):
    """One planned research activity; it is not evidence or a result."""

    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=120)
    purpose: str = Field(min_length=1, max_length=500)
    evidence_needed: list[str] = Field(min_length=1, max_length=5)


class ResearchPlan(BaseModel):
    """Structured Phase 1 output from a planning provider."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)
    objective: str = Field(min_length=1, max_length=600)
    steps: list[PlanStep] = Field(min_length=1, max_length=8)
    provider_label: str = Field(min_length=1, max_length=100)
    is_simulated: bool
    limitations: list[str] = Field(default_factory=list, max_length=5)


class ApprovalResumePayload(BaseModel):
    """Validated human response supplied to the LangGraph interrupt."""

    decision: Literal["approve", "modify", "reject"]
    modified_steps: list[PlanStep] | None = Field(default=None, min_length=1, max_length=8)

    @model_validator(mode="after")
    def validate_decision_payload(self) -> "ApprovalResumePayload":
        if self.decision == "modify" and not self.modified_steps:
            raise ValueError("A modified plan must contain at least one valid plan item.")
        if self.decision != "modify" and self.modified_steps is not None:
            raise ValueError("Modified plan items are only valid with the modify decision.")
        return self


class ApprovalInterruptPayload(BaseModel):
    """Safe structured context surfaced to a human at the checkpoint."""

    workflow_id: str
    question: str
    proposed_plan: ResearchPlan
    plan_item_count: int = Field(ge=1, le=8)
    provider_mode: Literal["simulated", "real"]
    explanation: str


class PendingResearchResult(BaseModel):
    """Public result returned only when the graph is genuinely interrupted."""

    workflow_id: str
    status: Literal["awaiting_approval"]
    plan: ResearchPlan
    approval_payload: ApprovalInterruptPayload
    interrupt_id: str
    workflow_events: list[str]


class CancelledResearchResult(BaseModel):
    """Terminal human-rejected workflow with no research output."""

    workflow_id: str
    status: Literal["cancelled"]
    approval_decision: Literal["reject"]
    question: str
    plan: ResearchPlan
    search_calls: int = Field(default=0, ge=0)
    workflow_events: list[str]
    created_at: datetime


class ResearchState(TypedDict, total=False):
    """Minimal LangGraph state designed for later additive extension."""

    request_id: str
    created_at: str
    question: str
    current_stage: str
    status: str
    research_plan: dict[str, Any]
    approval_decision: str | None
    plan_modified: bool
    search_queries: list[dict[str, Any]]
    active_search_queries: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    new_source_ids: list[str]
    iteration_accepted_added: int
    evidence_verifications: list[dict[str, Any]]
    critic_decision: dict[str, Any]
    critic_history: list[dict[str, Any]]
    iteration_traces: list[dict[str, Any]]
    retrieval_iteration: int
    max_research_iterations: int
    termination_reason: str | None
    citations: list[dict[str, Any]]
    preliminary_result: dict[str, Any]
    usage: dict[str, Any]
    node_latencies_ms: dict[str, float]
    workflow_events: list[str]


class PlanningResult(BaseModel):
    """Validated result returned at the deliberate Phase 1 boundary."""

    request_id: str
    status: str
    plan: ResearchPlan
    workflow_events: list[str]
    elapsed_ms: float = Field(ge=0)


class SearchQuery(BaseModel):
    """A bounded query linked to the plan step that produced it."""

    query_id: str = Field(pattern=r"^Q[1-9][0-9]*$")
    plan_step_order: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=350)
    iteration: int = Field(default=1, ge=1)
    evidence_gap: str | None = Field(default=None, max_length=500)


class ProviderSearchResult(BaseModel):
    """Provider-neutral result before workflow provenance is attached."""

    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_000)
    content: str = Field(default="", max_length=10_000)
    provider: str = Field(min_length=1, max_length=100)
    rank: int = Field(ge=1)
    provider_score: float | None = Field(default=None, ge=0, le=1)
    published_at: str | None = Field(default=None, max_length=100)


class SearchBatch(BaseModel):
    """One provider call and the raw usage facts it reported."""

    results: list[ProviderSearchResult]
    credits_used: float | None = Field(default=None, ge=0)


class Source(BaseModel):
    """Normalized, provenance-preserving untrusted search evidence."""

    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_000)
    canonical_url: str = Field(min_length=1, max_length=2_000)
    content: str = Field(default="", max_length=MAX_SOURCE_CONTENT_LENGTH)
    query_id: str = Field(pattern=r"^Q[1-9][0-9]*$")
    query_text: str = Field(min_length=1, max_length=350)
    plan_step_order: int = Field(ge=1)
    provider: str = Field(min_length=1, max_length=100)
    rank: int = Field(ge=1)
    provider_score: float | None = Field(default=None, ge=0, le=1)
    retrieved_at: str
    is_simulated: bool
    instruction_like: bool = False
    retrieval_iteration: int = Field(default=1, ge=1)


class EvidenceVerification(BaseModel):
    """Explicit relevance/support decision separate from retrieval."""

    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    plan_step_order: int = Field(ge=1)
    relevant: bool
    relevance_score: float = Field(ge=0, le=1)
    support_level: Literal["supportive", "contextual", "insufficient"]
    quality_signal: Literal["official-domain-signal", "academic-domain-signal", "unknown"]
    accepted_for_synthesis: bool
    instruction_like: bool
    reason: str = Field(min_length=1, max_length=500)


class EvidenceGap(BaseModel):
    """A structured plan-coverage deficiency identified by trusted critic code."""

    plan_step_order: int = Field(ge=1)
    plan_step_title: str = Field(min_length=1, max_length=120)
    issue: Literal["missing", "weak", "rejected", "conflict"]
    description: str = Field(min_length=1, max_length=500)


class EvidenceSufficiency(BaseModel):
    """Structured critic output used by conditional graph routing."""

    iteration: int = Field(ge=1)
    is_sufficient: bool
    confidence: float = Field(ge=0, le=1)
    evidence_gaps: list[EvidenceGap] = Field(default_factory=list)
    unsupported_subquestions: list[int] = Field(default_factory=list)
    conflicts_detected: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1, max_length=800)
    recommended_followup_queries: list[str] = Field(default_factory=list, max_length=5)


class ResearchIterationTrace(BaseModel):
    """Concise observable facts for one retrieval/verification/critic pass."""

    iteration: int = Field(ge=1)
    query_ids: list[str]
    query_count: int = Field(ge=0)
    sources_added: int = Field(ge=0)
    accepted_added: int = Field(ge=0)
    is_sufficient: bool
    evidence_gaps: list[str] = Field(default_factory=list)
    route_selected: Literal["revise_queries", "synthesize"]


class Citation(BaseModel):
    """A citation ID that resolves directly to a retained source."""

    citation_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_000)


class CitedClaim(BaseModel):
    """An extractive preliminary claim with validated citation IDs."""

    text: str = Field(min_length=1, max_length=1_000)
    citation_ids: list[str] = Field(min_length=1, max_length=4)


class PreliminaryResearchResult(BaseModel):
    """First-pass synthesis constrained to accepted retrieved evidence."""

    summary: str = Field(min_length=1, max_length=1_500)
    claims: list[CitedClaim] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=6)


class UsageMetadata(BaseModel):
    """Raw usage facts for later cost analysis; no fabricated dollar estimate."""

    query_count: int = Field(ge=0)
    search_calls: int = Field(ge=0)
    search_results_received: int = Field(ge=0)
    sources_retained: int = Field(ge=0)
    duplicates_removed: int = Field(ge=0)
    retrieval_passes: int = Field(ge=0)
    external_model_calls: int = Field(ge=0)
    critic_invocations: int = Field(default=0, ge=0)
    correction_iterations: int = Field(default=0, ge=0)
    provider_credits_used: float | None = Field(default=None, ge=0)
    node_latencies_ms: dict[str, float] = Field(default_factory=dict)
    total_latency_ms: float = Field(ge=0)


class ResearchResult(BaseModel):
    """Validated result returned after the bounded Phase 3 research loop."""

    request_id: str
    created_at: datetime
    status: str
    plan: ResearchPlan
    approval_decision: Literal["approve", "modify"]
    plan_modified: bool
    queries: list[SearchQuery]
    sources: list[Source]
    verifications: list[EvidenceVerification]
    critic_history: list[EvidenceSufficiency]
    iterations: list[ResearchIterationTrace]
    termination_reason: Literal[
        "evidence_sufficient",
        "max_iterations_reached",
        "no_new_queries",
        "no_new_evidence",
        "provider_failure",
    ]
    max_research_iterations: int = Field(ge=1)
    citations: list[Citation]
    preliminary_result: PreliminaryResearchResult
    usage: UsageMetadata
    workflow_events: list[str]
    search_provider_label: str
    search_is_simulated: bool
    elapsed_ms: float = Field(ge=0)
