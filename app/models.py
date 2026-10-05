"""Structured contracts shared by the web and workflow layers."""

from __future__ import annotations

from typing import Any, TypedDict

from pydantic import BaseModel, Field


MAX_QUESTION_LENGTH = 500


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
    workflow_events: list[str]


class PlanningResult(BaseModel):
    """Validated result returned at the deliberate Phase 1 boundary."""

    request_id: str
    status: str
    plan: ResearchPlan
    workflow_events: list[str]
    elapsed_ms: float = Field(ge=0)
