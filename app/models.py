"""Structured contracts shared by the web and workflow layers."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


MAX_QUESTION_LENGTH = 500
MAX_INITIAL_QUERIES = 3
MAX_RESULTS_PER_QUERY = 3
MAX_TOTAL_SOURCES = 8
MAX_SOURCE_CONTENT_LENGTH = 1_500


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


class ResearchState(TypedDict, total=False):
    """Minimal LangGraph state designed for later additive extension."""

    request_id: str
    question: str
    current_stage: str
    status: str
    research_plan: dict[str, Any]
    search_queries: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    evidence_verifications: list[dict[str, Any]]
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
    provider_credits_used: float | None = Field(default=None, ge=0)
    node_latencies_ms: dict[str, float] = Field(default_factory=dict)
    total_latency_ms: float = Field(ge=0)


class ResearchResult(BaseModel):
    """Validated result returned at the deliberate single-pass Phase 2 boundary."""

    request_id: str
    status: str
    plan: ResearchPlan
    queries: list[SearchQuery]
    sources: list[Source]
    verifications: list[EvidenceVerification]
    citations: list[Citation]
    preliminary_result: PreliminaryResearchResult
    usage: UsageMetadata
    workflow_events: list[str]
    search_provider_label: str
    search_is_simulated: bool
    elapsed_ms: float = Field(ge=0)
