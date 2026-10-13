from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from eval.models import EvaluationDataset
from eval.run_evaluation import (
    DEFAULT_DATASET,
    DEFAULT_SAFETY,
    _checks,
    calculate_metrics,
    evaluate,
    load_dataset,
    load_safety_artifact,
    write_results,
)


@pytest.fixture(scope="module")
def completed_run():
    return asyncio.run(evaluate())


def test_dataset_schema_and_category_distribution_are_versioned() -> None:
    dataset = load_dataset()

    assert dataset.dataset_version == "deeptrace-eval-v1"
    assert len(dataset.cases) == 27
    assert {case.category for case in dataset.cases} == {
        "initial_sufficient",
        "self_correction",
        "persistent_insufficiency",
        "citation_integrity",
        "safety_adversarial",
        "hitl_policy",
    }
    assert len({case.case_id for case in dataset.cases}) == len(dataset.cases)


def test_invalid_dataset_fails_closed() -> None:
    raw = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    raw["cases"] = raw["cases"][:1]
    raw["unexpected"] = "not allowed"

    with pytest.raises(ValidationError):
        EvaluationDataset.model_validate(raw)


def test_expected_vs_actual_scoring_exposes_mismatches() -> None:
    case = load_dataset().cases[0]
    actual = {
        "status": "research_result_ready",
        "termination_reason": "max_iterations_reached",
        "retrieval_passes": 2,
        "correction_performed": False,
        "supported_plan_items": [1],
        "citations_valid": True,
        "unsupported_citation_count": 0,
        "search_calls": 2,
    }

    checks = _checks(case, actual)

    assert checks["status"] is True
    assert checks["termination_reason"] is False
    assert checks["retrieval_passes"] is False
    assert checks["supported_plan_items"] is False


def test_zero_denominators_return_unavailable_not_division_error() -> None:
    dataset = load_dataset()
    safety = load_safety_artifact()
    empty_safety = deepcopy(safety)
    empty_safety["metrics"]["attacks_executed"] = 0
    empty_safety["metrics"]["attacks_blocked"] = 0

    metrics = calculate_metrics(dataset, [], empty_safety)

    assert metrics["task_completion_rate_percent"] is None
    assert metrics["citation_validity_rate_percent"] is None
    assert metrics["safety_attack_defense_rate_percent"] is None
    assert metrics["average_workflow_latency_ms"] is None


def test_safety_metric_is_derived_from_canonical_counts() -> None:
    dataset = load_dataset()
    safety = load_safety_artifact()
    changed = deepcopy(safety)
    changed["metrics"]["attacks_executed"] = 4
    changed["metrics"]["attacks_blocked"] = 3

    metrics = calculate_metrics(dataset, [], changed)

    assert metrics["safety_attack_defense_rate_percent"] == 75.0


def test_result_serialization_and_no_silent_overwrite(
    completed_run, tmp_path: Path
) -> None:
    json_path = tmp_path / "result.json"
    markdown_path = tmp_path / "result.md"

    write_results(completed_run, json_path, markdown_path)
    serialized = json.loads(json_path.read_text(encoding="utf-8"))

    assert len(serialized["cases"]) == completed_run.case_count
    assert serialized["metrics"] == completed_run.metrics
    assert "Deterministic Evaluation" in markdown_path.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError, match="Refusing to overwrite"):
        write_results(completed_run, json_path, markdown_path)


def test_failed_case_remains_visible_in_run_artifact(tmp_path: Path) -> None:
    raw = json.loads(DEFAULT_DATASET.read_text(encoding="utf-8"))
    raw["cases"][0]["expected"]["termination_reason"] = "max_iterations_reached"
    altered = tmp_path / "altered-dataset.json"
    altered.write_text(json.dumps(raw), encoding="utf-8")

    run = asyncio.run(evaluate(altered, DEFAULT_SAFETY))
    failure = next(item for item in run.failures if item["case_id"] == "A-01")

    assert run.metrics["tasks_passed"] < run.metrics["tasks_total"]
    assert failure["failure_category"] == "termination mismatch"
    assert "termination_reason" in failure["failed_checks"]
