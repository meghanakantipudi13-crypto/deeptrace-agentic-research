"""Strict schemas for the versioned DeepTrace evaluation dataset and results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


Category = Literal[
    "initial_sufficient",
    "self_correction",
    "persistent_insufficiency",
    "citation_integrity",
    "safety_adversarial",
    "hitl_policy",
]
Scenario = Literal[
    "sufficient",
    "corrected",
    "never_sufficient",
    "citation_closure",
    "safety_reference",
    "hitl_pause",
    "hitl_approve",
    "hitl_reject",
    "hitl_modify",
    "hitl_duplicate",
]


class ExpectedOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    termination_reason: str | None = None
    retrieval_passes_min: int = Field(default=0, ge=0, le=2)
    retrieval_passes_max: int = Field(default=2, ge=0, le=2)
    correction_required: bool = False
    supported_plan_items: list[int] = Field(default_factory=list)
    citations_valid: bool = True
    max_unsupported_citations: int = Field(default=0, ge=0)
    search_calls_min: int = Field(default=0, ge=0)
    search_calls_max: int = Field(default=10, ge=0)
    hitl_behavior: Literal["pause", "approve", "reject", "modify", "duplicate"] | None = None
    safety_defended: bool | None = None

    @model_validator(mode="after")
    def validate_ranges(self) -> "ExpectedOutcome":
        if self.retrieval_passes_min > self.retrieval_passes_max:
            raise ValueError("retrieval pass minimum cannot exceed maximum")
        if self.search_calls_min > self.search_calls_max:
            raise ValueError("search-call minimum cannot exceed maximum")
        return self


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[A-F]-\d{2}$")
    category: Category
    scenario: Scenario
    question: str | None = Field(default=None, min_length=5, max_length=500)
    plan_items: list[str] = Field(default_factory=list, max_length=3)
    modified_plan_item: str | None = Field(default=None, min_length=3, max_length=120)
    attack_id: str | None = Field(default=None, pattern=r"^PI-\d{3}$")
    expected: ExpectedOutcome

    @model_validator(mode="after")
    def validate_case_shape(self) -> "EvaluationCase":
        if self.category == "safety_adversarial":
            if self.scenario != "safety_reference" or not self.attack_id:
                raise ValueError("safety cases must reference a canonical attack")
        elif not self.question:
            raise ValueError("non-safety cases require a research question")
        if self.category in {
            "initial_sufficient",
            "self_correction",
            "persistent_insufficiency",
            "citation_integrity",
            "hitl_policy",
        } and not self.plan_items:
            raise ValueError("workflow and HITL cases require plan items")
        if self.scenario == "hitl_modify" and not self.modified_plan_item:
            raise ValueError("modify cases require modified_plan_item")
        return self


class EvaluationDataset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    dataset_version: Literal["deeptrace-eval-v1"]
    provider_mode: Literal["deterministic_local"]
    description: str = Field(min_length=20)
    cases: list[EvaluationCase] = Field(min_length=25, max_length=30)

    @model_validator(mode="after")
    def validate_dataset(self) -> "EvaluationDataset":
        ids = [case.case_id for case in self.cases]
        if len(ids) != len(set(ids)):
            raise ValueError("evaluation case IDs must be unique")
        required = {
            "initial_sufficient",
            "self_correction",
            "persistent_insufficiency",
            "citation_integrity",
            "safety_adversarial",
            "hitl_policy",
        }
        if {case.category for case in self.cases} != required:
            raise ValueError("dataset must include every required capability category")
        return self


class EvaluationCaseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str
    category: Category
    scenario: Scenario
    passed: bool
    checks: dict[str, bool]
    expected: dict[str, Any]
    actual: dict[str, Any]
    failure_category: str | None = None
    error: str | None = None
    evaluation_elapsed_ms: float = Field(ge=0)


class EvaluationRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1]
    evaluation_id: str
    evaluation_timestamp_utc: str
    evaluation_date: str
    git_commit: str
    git_worktree_dirty: bool
    dataset_version: str
    provider_mode: str
    application_phase: Literal[7]
    application_version: str
    python_version: str
    platform: str
    configuration: dict[str, Any]
    category_counts: dict[str, int]
    case_count: int
    metrics: dict[str, Any]
    metric_definitions: dict[str, str]
    failures: list[dict[str, Any]]
    cases: list[EvaluationCaseResult]
    safety_artifact: dict[str, Any]
    cost_analysis: dict[str, Any]
