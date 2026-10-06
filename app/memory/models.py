"""Versioned, validated schemas for durable research memory."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import (
    Citation,
    PreliminaryResearchResult,
    ResearchPlan,
    UsageMetadata,
)


MEMORY_SCHEMA_VERSION = 1


class StoredSourceMetadata(BaseModel):
    """Useful source provenance without retaining retrieved page text."""

    source_id: str = Field(pattern=r"^S[1-9][0-9]*$")
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=1, max_length=2_000)
    provider: str = Field(min_length=1, max_length=100)
    retrieved_at: str
    is_simulated: bool


class ResearchMemoryRecord(BaseModel):
    """One terminal workflow record suitable for local disk or object storage."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = MEMORY_SCHEMA_VERSION
    session_id: str
    created_at: datetime
    stored_at: datetime
    status: Literal["completed", "cancelled"]
    question: str = Field(min_length=1, max_length=500)
    plan: ResearchPlan
    approval_decision: Literal["approve", "modify", "reject"]
    plan_modified: bool
    provider_mode: Literal["simulated", "real"]
    provider_label: str = Field(min_length=1, max_length=100)
    termination_reason: str
    report: PreliminaryResearchResult | None = None
    citations: list[Citation] = Field(default_factory=list)
    sources: list[StoredSourceMetadata] = Field(default_factory=list, max_length=12)
    usage: UsageMetadata | None = None

    @field_validator("session_id")
    @classmethod
    def validate_uuid(cls, value: str) -> str:
        if str(UUID(value)) != value:
            raise ValueError("session_id must be a canonical UUID")
        return value

    @model_validator(mode="after")
    def validate_terminal_shape(self) -> "ResearchMemoryRecord":
        if self.status == "completed" and (self.report is None or self.usage is None):
            raise ValueError("Completed records require a report and usage metadata.")
        if self.status == "cancelled" and (
            self.report is not None or self.citations or self.sources or self.usage is not None
        ):
            raise ValueError("Cancelled records cannot contain research output.")
        return self

    def summary(self) -> "ResearchMemorySummary":
        return ResearchMemorySummary(
            session_id=self.session_id,
            created_at=self.created_at,
            stored_at=self.stored_at,
            status=self.status,
            question=self.question,
            provider_mode=self.provider_mode,
            termination_reason=self.termination_reason,
            retrieval_passes=self.usage.retrieval_passes if self.usage else None,
        )


class ResearchMemorySummary(BaseModel):
    """Bounded metadata for a history listing."""

    session_id: str
    created_at: datetime
    stored_at: datetime
    status: Literal["completed", "cancelled"]
    question: str
    provider_mode: Literal["simulated", "real"]
    termination_reason: str
    retrieval_passes: int | None = Field(default=None, ge=0)
