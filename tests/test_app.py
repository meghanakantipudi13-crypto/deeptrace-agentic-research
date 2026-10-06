from __future__ import annotations

import re

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import PlanStep, ResearchPlan
from app.search.deterministic import DeterministicSearchProvider


class CountingSearchProvider:
    provider_name = "counting-fixture-search"
    is_simulated = True

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._delegate = DeterministicSearchProvider()

    async def search(self, query: str, limit: int):
        self.calls.append(query)
        return await self._delegate.search(query, limit)


def _workflow_id(html: str) -> str:
    match = re.search(r'action="/research/([0-9a-f-]+)/decision"', html)
    assert match
    return match.group(1)


class CountingPlanModel:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def create_plan(self, question: str) -> ResearchPlan:
        self.calls.append(question)
        return ResearchPlan(
            question=question,
            objective="Test objective",
            steps=[
                PlanStep(
                    order=1,
                    title="Test planning step",
                    purpose="Prove the provider result reaches the UI.",
                    evidence_needed=["Test evidence requirement"],
                )
            ],
            provider_label="Deterministic test planner",
            is_simulated=True,
            limitations=["Test output only."],
        )


def test_health_endpoint() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "deeptrace", "phase": "4"}


def test_main_page_loads() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Approve the plan before research begins" in response.text
    assert "No sources were retrieved" not in response.text


def test_valid_question_runs_workflow_and_displays_plan() -> None:
    model = CountingPlanModel()
    with TestClient(create_app(model)) as client:
        response = client.post("/plan", data={"question": "  What is evidence quality?  "})

    assert response.status_code == 200
    assert model.calls == ["What is evidence quality?"]
    assert "Test planning step" in response.text
    assert "Simulated development output" in response.text
    assert "No sources were retrieved and no claims were verified." in response.text


def test_empty_question_is_rejected_without_model_call() -> None:
    model = CountingPlanModel()
    with TestClient(create_app(model)) as client:
        response = client.post("/plan", data={"question": " \t\n "})

    assert response.status_code == 400
    assert "Enter a research question" in response.text
    assert model.calls == []

def test_over_length_question_is_rejected_without_model_call() -> None:
    model = CountingPlanModel()
    with TestClient(create_app(model)) as client:
        response = client.post("/plan", data={"question": "x" * 501})

    assert response.status_code == 400
    assert "500 characters or fewer" in response.text
    assert model.calls == []


def test_research_route_pauses_and_displays_approval_controls() -> None:
    model = CountingPlanModel()
    search = CountingSearchProvider()
    with TestClient(create_app(model, search)) as client:
        response = client.post(
            "/research",
            data={"question": "How should evidence quality be evaluated?"},
        )

    assert response.status_code == 200
    assert "SIMULATED DEVELOPMENT MODE" in response.text
    assert "Research Plan Awaiting Approval" in response.text
    assert "Research has NOT started yet" in response.text
    assert "Approve &amp; Research" in response.text
    assert "Approve Modified Plan" in response.text
    assert ">Cancel<" in response.text
    assert "Search queries" not in response.text
    assert search.calls == []


def test_approval_route_resumes_and_renders_research_trace() -> None:
    model = CountingPlanModel()
    search = CountingSearchProvider()
    with TestClient(create_app(model, search)) as client:
        pending = client.post(
            "/research",
            data={"question": "How should evidence quality be evaluated?"},
        )
        response = client.post(
            f"/research/{_workflow_id(pending.text)}/decision",
            data={"decision": "approve"},
        )

    assert response.status_code == 200
    assert search.calls
    assert "Research iterations" in response.text
    assert "Termination: evidence sufficient" in response.text
    assert "Phase 4 boundary reached" in response.text
    assert "Approval: approve" in response.text


def test_cancel_route_performs_no_search() -> None:
    model = CountingPlanModel()
    search = CountingSearchProvider()
    with TestClient(create_app(model, search)) as client:
        pending = client.post(
            "/research",
            data={"question": "How should evidence quality be evaluated?"},
        )
        response = client.post(
            f"/research/{_workflow_id(pending.text)}/decision",
            data={"decision": "reject"},
        )

    assert response.status_code == 200
    assert "Research cancelled" in response.text
    assert "No search calls or research synthesis were performed" in response.text
    assert search.calls == []


def test_modify_route_uses_edited_plan_in_research() -> None:
    model = CountingPlanModel()
    search = CountingSearchProvider()
    with TestClient(create_app(model, search)) as client:
        pending = client.post(
            "/research",
            data={"question": "How should evidence quality be evaluated?"},
        )
        response = client.post(
            f"/research/{_workflow_id(pending.text)}/decision",
            data={
                "decision": "modify",
                "step_title": "Human-edited evidence quality step",
                "step_purpose": "Evaluate human-selected evidence criteria.",
                "step_evidence": "Human-selected primary evidence",
            },
        )

    assert response.status_code == 200
    assert "Human-edited evidence quality step" in response.text
    assert "Approval: modify" in response.text
    assert "Plan modified: True" in response.text
    assert "Human-edited evidence quality step" in search.calls[0]


def test_research_route_preserves_input_validation() -> None:
    model = CountingPlanModel()
    with TestClient(create_app(model)) as client:
        response = client.post("/research", data={"question": "  "})

    assert response.status_code == 400
    assert "Enter a research question" in response.text
    assert model.calls == []
