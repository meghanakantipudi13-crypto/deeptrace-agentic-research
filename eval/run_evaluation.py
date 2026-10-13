"""Run the capability-matched deterministic DeepTrace evaluation."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import platform
import statistics
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from app.models import (
    ApprovalResumePayload,
    CancelledResearchResult,
    PlanStep,
    ProviderSearchResult,
    ResearchPlan,
    ResearchResult,
    SearchBatch,
)
from app.research import validate_citation_mapping
from app.research_workflow import ResearchWorkflow, WorkflowNotAwaitingApprovalError
from eval.models import EvaluationCase, EvaluationCaseResult, EvaluationDataset, EvaluationRun


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / "eval" / "datasets" / "deeptrace_eval_v1.json"
DEFAULT_SAFETY = ROOT / "eval" / "adversarial_results_local.json"
DEFAULT_JSON = ROOT / "eval" / "results" / "deeptrace_eval_v1_local.json"
DEFAULT_MARKDOWN = ROOT / "eval" / "results" / "deeptrace_eval_v1_local.md"
MAX_ITERATIONS = 2


class EvaluationPlanModel:
    def __init__(self, case: EvaluationCase) -> None:
        self.case = case

    async def create_plan(self, question: str) -> ResearchPlan:
        return ResearchPlan(
            question=question,
            objective=f"Evaluate deterministic evidence for {question.rstrip('?')}.",
            steps=[
                PlanStep(
                    order=index,
                    title=item,
                    purpose=f"Assess documented evidence about {item.lower()}.",
                    evidence_needed=[f"Documented {item.lower()} evidence"],
                )
                for index, item in enumerate(self.case.plan_items, start=1)
            ],
            provider_label="evaluation-fixture-planner-v1",
            is_simulated=True,
        )


class EvaluationSearchProvider:
    provider_name = "evaluation-fixture-search-v1"
    is_simulated = True

    def __init__(self, case: EvaluationCase) -> None:
        self.case = case
        self.calls: list[str] = []

    def _step(self, query: str) -> tuple[int, str]:
        for index, item in enumerate(self.case.plan_items, start=1):
            if item.lower() in query.lower():
                return index, item
        return 1, self.case.plan_items[0]

    async def search(self, query: str, limit: int) -> SearchBatch:
        self.calls.append(query)
        order, item = self._step(query)
        final_order = len(self.case.plan_items)
        followup = "follow-up evidence" in query.lower()
        should_withhold = order == final_order and self.case.scenario in {
            "corrected",
            "never_sufficient",
        }
        if should_withhold and not (
            self.case.scenario == "corrected" and followup
        ):
            return SearchBatch(
                results=[
                    ProviderSearchResult(
                        title="Unrelated deterministic control",
                        url=f"https://example.test/{self.case.case_id.lower()}/unrelated-{len(self.calls)}",
                        content=(
                            "A bread recipe discusses flour, yeast, mixing bowls, oven "
                            "temperatures, and kitchen equipment without addressing the research task."
                        ),
                        provider=self.provider_name,
                        rank=1,
                        provider_score=0.1,
                    )
                ]
            )
        content = (
            f"Documented {item.lower()} evidence reports measured findings for "
            f"{self.case.question}. The source describes methods, observations, comparison "
            "criteria, uncertainty, and implementation limitations for this research-plan item."
        )
        return SearchBatch(
            results=[
                ProviderSearchResult(
                    title=f"Documented evidence: {item}",
                    url=f"https://agency.gov/{self.case.case_id.lower()}/step-{order}-{len(self.calls)}",
                    content=content,
                    provider=self.provider_name,
                    rank=1,
                    provider_score=0.9,
                )
            ]
        )


def load_dataset(path: Path = DEFAULT_DATASET) -> EvaluationDataset:
    return EvaluationDataset.model_validate_json(path.read_text(encoding="utf-8"))


def load_safety_artifact(path: Path = DEFAULT_SAFETY) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data.get("attacks"), list) or not isinstance(data.get("metrics"), dict):
        raise ValueError("Safety artifact is missing attacks or metrics.")
    return data


def _citation_facts(result: ResearchResult) -> tuple[bool, int]:
    try:
        validate_citation_mapping(result.preliminary_result, result.citations, result.sources)
        mapping_valid = True
    except ValueError:
        mapping_valid = False
    sources = {source.source_id: source for source in result.sources}
    unsupported = 0
    for citation in result.citations:
        source = sources.get(citation.source_id)
        if (
            source is None
            or citation.citation_id != citation.source_id
            or citation.title != source.title
            or citation.url != source.url
        ):
            unsupported += 1
    citation_ids = {citation.citation_id for citation in result.citations}
    unsupported += sum(
        len(set(claim.citation_ids) - citation_ids)
        for claim in result.preliminary_result.claims
    )
    return mapping_valid and unsupported == 0, unsupported


def _research_actual(result: ResearchResult, provider: EvaluationSearchProvider) -> dict[str, Any]:
    supported = sorted(
        {
            item.plan_step_order
            for item in result.verifications
            if item.accepted_for_synthesis and item.support_level == "supportive"
        }
    )
    citation_valid, unsupported = _citation_facts(result)
    correction = bool(
        result.critic_history
        and not result.critic_history[0].is_sufficient
        and any(query.iteration == 2 for query in result.queries)
        and result.usage.retrieval_passes == 2
    )
    return {
        "status": result.status,
        "termination_reason": result.termination_reason,
        "retrieval_passes": result.usage.retrieval_passes,
        "correction_performed": correction,
        "supported_plan_items": supported,
        "plan_item_count": len(result.plan.steps),
        "citations_valid": citation_valid,
        "citation_count": len(result.citations),
        "unsupported_citation_count": unsupported,
        "search_calls": result.usage.search_calls,
        "provider_call_count": len(provider.calls),
        "retained_sources": result.usage.sources_retained,
        "external_model_calls": result.usage.external_model_calls,
        "provider_credits_used": result.usage.provider_credits_used,
        "workflow_latency_ms": result.usage.total_latency_ms,
        "critic_invocations": result.usage.critic_invocations,
        "approval_decision": result.approval_decision,
        "plan_modified": result.plan_modified,
    }


async def _run_workflow_case(case: EvaluationCase) -> dict[str, Any]:
    provider = EvaluationSearchProvider(case)
    workflow = ResearchWorkflow(EvaluationPlanModel(case), provider)
    pending = await workflow.start(case.question or "")
    preapproval_calls = len(provider.calls)

    if case.scenario == "hitl_pause":
        return {
            "status": pending.status,
            "termination_reason": None,
            "retrieval_passes": 0,
            "correction_performed": False,
            "supported_plan_items": [],
            "plan_item_count": len(pending.plan.steps),
            "citations_valid": True,
            "citation_count": 0,
            "unsupported_citation_count": 0,
            "search_calls": 0,
            "provider_call_count": 0,
            "retained_sources": 0,
            "external_model_calls": 0,
            "provider_credits_used": None,
            "workflow_latency_ms": None,
            "hitl_enforced": preapproval_calls == 0 and bool(pending.interrupt_id),
        }
    if case.scenario == "hitl_reject":
        outcome = await workflow.resume(
            pending.workflow_id, ApprovalResumePayload(decision="reject")
        )
        assert isinstance(outcome, CancelledResearchResult)
        return {
            "status": outcome.status,
            "termination_reason": "human_cancelled",
            "retrieval_passes": 0,
            "correction_performed": False,
            "supported_plan_items": [],
            "plan_item_count": len(outcome.plan.steps),
            "citations_valid": True,
            "citation_count": 0,
            "unsupported_citation_count": 0,
            "search_calls": outcome.search_calls,
            "provider_call_count": len(provider.calls),
            "retained_sources": 0,
            "external_model_calls": 0,
            "provider_credits_used": None,
            "workflow_latency_ms": None,
            "hitl_enforced": preapproval_calls == 0 and len(provider.calls) == 0,
        }
    decision = "approve"
    modified_steps = None
    if case.scenario == "hitl_modify":
        decision = "modify"
        modified_steps = [
            PlanStep(
                order=1,
                title=case.modified_plan_item or "Modified evidence",
                purpose="Evaluate the human-modified evidence requirement.",
                evidence_needed=["Documented modified-plan evidence"],
            )
        ]
    outcome = await workflow.resume(
        pending.workflow_id,
        ApprovalResumePayload(decision=decision, modified_steps=modified_steps),
    )
    assert isinstance(outcome, ResearchResult)
    actual = _research_actual(outcome, provider)
    if case.scenario == "hitl_modify":
        marker = case.modified_plan_item or ""
        actual["hitl_enforced"] = (
            preapproval_calls == 0
            and outcome.plan_modified
            and marker in outcome.queries[0].text
            and marker in provider.calls[0]
        )
    else:
        actual["hitl_enforced"] = preapproval_calls == 0
    if case.scenario == "hitl_duplicate":
        calls_before = len(provider.calls)
        duplicate_rejected = False
        try:
            await workflow.resume(
                pending.workflow_id, ApprovalResumePayload(decision="approve")
            )
        except WorkflowNotAwaitingApprovalError:
            duplicate_rejected = True
        actual["hitl_enforced"] = (
            actual["hitl_enforced"]
            and duplicate_rejected
            and calls_before == len(provider.calls)
        )
        actual["duplicate_rejected"] = duplicate_rejected
    return actual


def _checks(case: EvaluationCase, actual: dict[str, Any]) -> dict[str, bool]:
    expected = case.expected
    checks = {
        "status": actual.get("status") == expected.status,
        "retrieval_passes": expected.retrieval_passes_min
        <= actual.get("retrieval_passes", 0)
        <= expected.retrieval_passes_max,
        "correction": actual.get("correction_performed", False)
        == expected.correction_required,
        "supported_plan_items": actual.get("supported_plan_items", [])
        == expected.supported_plan_items,
        "citation_validity": actual.get("citations_valid") == expected.citations_valid
        and actual.get("unsupported_citation_count", 0)
        <= expected.max_unsupported_citations,
        "search_calls": expected.search_calls_min
        <= actual.get("search_calls", 0)
        <= expected.search_calls_max,
    }
    if expected.termination_reason is not None:
        checks["termination_reason"] = (
            actual.get("termination_reason") == expected.termination_reason
        )
    if expected.hitl_behavior is not None:
        checks["hitl_enforcement"] = actual.get("hitl_enforced") is True
    if expected.safety_defended is not None:
        checks["safety_defense"] = (
            actual.get("safety_defended") == expected.safety_defended
        )
    return checks


def _failure_category(checks: dict[str, bool]) -> str | None:
    mapping = {
        "termination_reason": "termination mismatch",
        "correction": "evidence gap or correction failure",
        "supported_plan_items": "retrieval or evidence coverage failure",
        "citation_validity": "citation failure",
        "hitl_enforcement": "HITL failure",
        "safety_defense": "safety failure",
        "search_calls": "resource-bound failure",
        "retrieval_passes": "bounded-termination failure",
        "status": "terminal-state failure",
    }
    return next((mapping[name] for name, passed in checks.items() if not passed), None)


async def _execute_case(
    case: EvaluationCase, safety_by_id: dict[str, dict[str, Any]]
) -> EvaluationCaseResult:
    started = perf_counter()
    try:
        if case.category == "safety_adversarial":
            attack = safety_by_id.get(case.attack_id or "")
            if attack is None:
                raise ValueError(f"Missing canonical safety result {case.attack_id}.")
            actual = {
                "status": attack["classification"].replace(" ", "_"),
                "termination_reason": None,
                "retrieval_passes": attack.get("retrieval_passes", 0),
                "correction_performed": False,
                "supported_plan_items": [],
                "citations_valid": "S999" not in attack.get("citation_ids", []),
                "citation_count": len(attack.get("citation_ids", [])),
                "unsupported_citation_count": int(
                    "S999" in attack.get("citation_ids", [])
                ),
                "search_calls": attack.get("search_calls", 0),
                "safety_defended": bool(
                    attack.get("passed")
                    and not attack.get("unsafe_objective_succeeded")
                ),
                "canonical_artifact_reference": case.attack_id,
            }
        else:
            actual = await _run_workflow_case(case)
        checks = _checks(case, actual)
        passed = all(checks.values())
        return EvaluationCaseResult(
            case_id=case.case_id,
            category=case.category,
            scenario=case.scenario,
            passed=passed,
            checks=checks,
            expected=case.expected.model_dump(mode="json"),
            actual=actual,
            failure_category=_failure_category(checks),
            evaluation_elapsed_ms=round((perf_counter() - started) * 1000, 3),
        )
    except Exception as error:  # Evaluation must retain unexpected failures.
        return EvaluationCaseResult(
            case_id=case.case_id,
            category=case.category,
            scenario=case.scenario,
            passed=False,
            checks={"execution": False},
            expected=case.expected.model_dump(mode="json"),
            actual={},
            failure_category="unexpected evaluation failure",
            error=f"{type(error).__name__}: {error}",
            evaluation_elapsed_ms=round((perf_counter() - started) * 1000, 3),
        )


def _rate(numerator: int, denominator: int) -> float | None:
    return round(100 * numerator / denominator, 3) if denominator else None


def _average(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 3) if values else None


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)], 3)


def calculate_metrics(
    dataset: EvaluationDataset,
    results: list[EvaluationCaseResult],
    safety_artifact: dict[str, Any],
) -> dict[str, Any]:
    by_id = {case.case_id: case for case in dataset.cases}
    termination = [
        result
        for result in results
        if by_id[result.case_id].expected.termination_reason is not None
    ]
    correction = [r for r in results if r.category == "self_correction"]
    persistent = [r for r in results if r.category == "persistent_insufficiency"]
    hitl = [r for r in results if r.category == "hitl_policy"]
    research_results = [
        r
        for r in results
        if r.actual.get("status") == "research_result_ready"
    ]
    total_plan_items = sum(r.actual.get("plan_item_count", 0) for r in research_results)
    supported_items = sum(
        len(r.actual.get("supported_plan_items", [])) for r in research_results
    )
    citation_total = sum(r.actual.get("citation_count", 0) for r in results)
    unsupported = sum(r.actual.get("unsupported_citation_count", 0) for r in results)
    valid_citations = citation_total - unsupported
    latencies = [
        float(r.actual["workflow_latency_ms"])
        for r in research_results
        if r.actual.get("workflow_latency_ms") is not None
    ]
    safety_metrics = safety_artifact["metrics"]
    errors = sum(result.error is not None for result in results)
    return {
        "task_completion_rate_percent": _rate(
            sum(result.passed for result in results), len(results)
        ),
        "tasks_passed": sum(result.passed for result in results),
        "tasks_total": len(results),
        "expected_termination_accuracy_percent": _rate(
            sum(r.checks.get("termination_reason", False) for r in termination),
            len(termination),
        ),
        "termination_cases": len(termination),
        "self_correction_success_rate_percent": _rate(
            sum(
                r.checks.get("correction", False)
                and r.checks.get("termination_reason", False)
                and r.checks.get("supported_plan_items", False)
                for r in correction
            ),
            len(correction),
        ),
        "self_correction_cases": len(correction),
        "evidence_coverage_percent": _rate(supported_items, total_plan_items),
        "supported_plan_items": supported_items,
        "total_plan_items": total_plan_items,
        "citation_validity_rate_percent": _rate(valid_citations, citation_total),
        "valid_citations": valid_citations,
        "emitted_citations": citation_total,
        "unsupported_citation_count": unsupported,
        "hitl_enforcement_rate_percent": _rate(
            sum(r.checks.get("hitl_enforcement", False) for r in hitl), len(hitl)
        ),
        "hitl_cases": len(hitl),
        "safety_attack_defense_rate_percent": _rate(
            int(safety_metrics["attacks_blocked"]),
            int(safety_metrics["attacks_executed"]),
        ),
        "safety_attacks_blocked": safety_metrics["attacks_blocked"],
        "safety_attacks_executed": safety_metrics["attacks_executed"],
        "bounded_termination_rate_percent": _rate(
            sum(
                r.checks.get("retrieval_passes", False)
                and r.checks.get("termination_reason", False)
                for r in persistent
            ),
            len(persistent),
        ),
        "persistent_insufficiency_cases": len(persistent),
        "error_rate_percent": _rate(errors, len(results)),
        "unexpected_errors": errors,
        "average_workflow_latency_ms": _average(latencies),
        "median_workflow_latency_ms": (
            round(statistics.median(latencies), 3) if latencies else None
        ),
        "p95_workflow_latency_ms": _p95(latencies),
        "latency_sample_size": len(latencies),
        "average_retrieval_passes": _average(
            [float(r.actual.get("retrieval_passes", 0)) for r in research_results]
        ),
        "average_search_calls": _average(
            [float(r.actual.get("search_calls", 0)) for r in research_results]
        ),
        "average_retained_sources": _average(
            [float(r.actual.get("retained_sources", 0)) for r in research_results]
        ),
        "external_model_calls": sum(
            int(r.actual.get("external_model_calls", 0)) for r in research_results
        ),
        "provider_credits_used": None,
        "token_usage": None,
    }


METRIC_DEFINITIONS = {
    "task_completion_rate_percent": "Cases satisfying every machine-checkable expected outcome / all dataset cases.",
    "expected_termination_accuracy_percent": "Cases with the expected termination reason / cases specifying a termination reason.",
    "self_correction_success_rate_percent": "Category B cases that detected an initial gap, issued/evaluated a second-pass query, reached expected coverage, and terminated as expected / Category B cases.",
    "evidence_coverage_percent": "Plan items with at least one accepted supportive source / plan items in workflows producing research results; designed persistent gaps remain in the denominator.",
    "citation_validity_rate_percent": "Emitted citations closing over retained source IDs and metadata / all emitted citations.",
    "unsupported_citation_count": "Emitted or claim-referenced citation IDs without a valid retained-source mapping.",
    "hitl_enforcement_rate_percent": "HITL cases satisfying their pause/approve/reject/modify/duplicate policy assertion / HITL cases.",
    "safety_attack_defense_rate_percent": "Blocked attacks / attacks executed, derived from the canonical Phase 6 artifact.",
    "bounded_termination_rate_percent": "Persistent-insufficiency cases stopping at the expected reason within the two-pass bound / persistent-insufficiency cases.",
    "error_rate_percent": "Cases raising an unexpected harness or workflow exception / all dataset cases.",
}


def _git_metadata() -> tuple[str, bool]:
    try:
        safe_directory = str(ROOT).replace("\\", "/")
        git = ["git", "-c", f"safe.directory={safe_directory}"]
        commit = subprocess.run(
            [*git, "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                [*git, "status", "--porcelain"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return commit, dirty
    except (OSError, subprocess.SubprocessError):
        return "unavailable", True


async def evaluate(
    dataset_path: Path = DEFAULT_DATASET,
    safety_path: Path = DEFAULT_SAFETY,
) -> EvaluationRun:
    dataset = load_dataset(dataset_path)
    safety = load_safety_artifact(safety_path)
    safety_by_id = {attack["attack_id"]: attack for attack in safety["attacks"]}
    results = [await _execute_case(case, safety_by_id) for case in dataset.cases]
    now = datetime.now(UTC)
    commit, dirty = _git_metadata()
    failures = [
        {
            "case_id": result.case_id,
            "failure_category": result.failure_category,
            "failed_checks": [name for name, passed in result.checks.items() if not passed],
            "expected": result.expected,
            "actual": result.actual,
            "error": result.error,
        }
        for result in results
        if not result.passed
    ]
    return EvaluationRun(
        schema_version=1,
        evaluation_id=f"deeptrace-eval-v1-local-{now.strftime('%Y%m%dT%H%M%SZ')}",
        evaluation_timestamp_utc=now.isoformat(),
        evaluation_date=now.date().isoformat(),
        git_commit=commit,
        git_worktree_dirty=dirty,
        dataset_version=dataset.dataset_version,
        provider_mode=dataset.provider_mode,
        application_phase=7,
        application_version="0.6.0-runtime; phase7-evaluation",
        python_version=platform.python_version(),
        platform=platform.platform(),
        configuration={
            "maximum_retrieval_passes": MAX_ITERATIONS,
            "paid_provider_calls": False,
            "model_provider": "deterministic fixture planner",
            "search_provider": "deterministic fixture search",
        },
        category_counts=dict(sorted(Counter(case.category for case in dataset.cases).items())),
        case_count=len(dataset.cases),
        metrics=calculate_metrics(dataset, results, safety),
        metric_definitions=METRIC_DEFINITIONS,
        failures=failures,
        cases=results,
        safety_artifact={
            "path": str(safety_path.relative_to(ROOT)).replace("\\", "/"),
            "executed_at": safety.get("executed_at"),
            "attacks_executed": safety["metrics"]["attacks_executed"],
            "attacks_blocked": safety["metrics"]["attacks_blocked"],
            "deployed_system": safety.get("environment", {}).get("deployed_system"),
        },
        cost_analysis={
            "deterministic_evaluation_dollar_cost": 0.0,
            "basis": "No paid model, search, storage, or infrastructure calls were made by this deterministic run.",
            "production_projection_available": False,
            "future_inputs": [
                "model input and output tokens with dated prices",
                "Tavily requests or credits",
                "GCS operations and retained bytes",
                "PostgreSQL and compute runtime assumptions",
            ],
        },
    )


def render_markdown(run: EvaluationRun) -> str:
    metrics = run.metrics
    failure_lines = (
        [
            f"- `{item['case_id']}` — {item['failure_category']}; failed checks: "
            f"{', '.join(item['failed_checks']) or 'execution'}"
            for item in run.failures
        ]
        or ["- No dataset cases failed in this deterministic run."]
    )
    category_rows = "\n".join(
        f"| {category} | {count} |" for category, count in run.category_counts.items()
    )
    return f"""# DeepTrace Deterministic Evaluation v1

**Scope:** Local deterministic capability evaluation; not live web-research quality or deployed performance.

**Timestamp (UTC):** {run.evaluation_timestamp_utc}

**Dataset:** `{run.dataset_version}`

**Cases:** {run.case_count}

**Provider mode:** `{run.provider_mode}`

**Git HEAD at execution:** `{run.git_commit}` (worktree dirty: `{str(run.git_worktree_dirty).lower()}`)

## Dataset

| Category | Cases |
|---|---:|
{category_rows}

## Core results

| Metric | Result |
|---|---:|
| Task completion rate | {metrics['task_completion_rate_percent']}% ({metrics['tasks_passed']}/{metrics['tasks_total']}) |
| Expected-termination accuracy | {metrics['expected_termination_accuracy_percent']}% |
| Self-correction success rate | {metrics['self_correction_success_rate_percent']}% |
| Evidence coverage | {metrics['evidence_coverage_percent']}% ({metrics['supported_plan_items']}/{metrics['total_plan_items']}) |
| Citation validity rate | {metrics['citation_validity_rate_percent']}% ({metrics['valid_citations']}/{metrics['emitted_citations']}) |
| Unsupported citations accepted | {metrics['unsupported_citation_count']} |
| HITL enforcement rate | {metrics['hitl_enforcement_rate_percent']}% |
| Safety attack defense rate | {metrics['safety_attack_defense_rate_percent']}% ({metrics['safety_attacks_blocked']}/{metrics['safety_attacks_executed']}) |
| Bounded-termination rate | {metrics['bounded_termination_rate_percent']}% |
| Unexpected error rate | {metrics['error_rate_percent']}% ({metrics['unexpected_errors']}/{metrics['tasks_total']}) |

## Deterministic performance and resources

The latency sample contains {metrics['latency_sample_size']} completed research-result workflows. These local fixture timings do not predict production latency.

| Metric | Result |
|---|---:|
| Average workflow latency | {metrics['average_workflow_latency_ms']} ms |
| Median workflow latency | {metrics['median_workflow_latency_ms']} ms |
| Nearest-rank p95 workflow latency | {metrics['p95_workflow_latency_ms']} ms |
| Average retrieval passes | {metrics['average_retrieval_passes']} |
| Average search calls | {metrics['average_search_calls']} |
| Average retained sources | {metrics['average_retained_sources']} |
| External model calls | {metrics['external_model_calls']} |
| Provider credits | unavailable/not applicable |
| Token usage | unavailable/not applicable |

## Failures

{chr(10).join(failure_lines)}

## Safety and cost boundaries

Safety defense is derived from `{run.safety_artifact['path']}`, not manually entered. The three attacks were local; deployed adversarial execution remains open.

Measured deterministic paid-provider cost was **$0.00** because no paid API, model, storage, or infrastructure calls occurred. This is not a production cost estimate. Production analysis requires actual token counts, Tavily usage, storage operations, and infrastructure runtime with dated prices.
"""


def write_results(
    run: EvaluationRun,
    json_path: Path,
    markdown_path: Path,
    *,
    overwrite: bool = False,
) -> None:
    for path in (json_path, markdown_path):
        if path.exists() and not overwrite:
            raise FileExistsError(f"Refusing to overwrite existing evidence: {path}")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(run), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--safety-artifact", type=Path, default=DEFAULT_SAFETY)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    run = asyncio.run(evaluate(args.dataset, args.safety_artifact))
    write_results(
        run,
        args.json_output,
        args.markdown_output,
        overwrite=args.overwrite,
    )
    print(json.dumps({"case_count": run.case_count, "metrics": run.metrics}, sort_keys=True))


if __name__ == "__main__":
    main()
