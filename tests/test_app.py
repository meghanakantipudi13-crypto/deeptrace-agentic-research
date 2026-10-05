from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import PlanStep, ResearchPlan


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
    assert response.json() == {"status": "healthy", "service": "deeptrace", "phase": "3"}


def test_main_page_loads() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "Trace a question through evidence-driven correction" in response.text
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


def test_research_route_displays_phase_three_iteration_trace() -> None:
    from app.search.deterministic import DeterministicSearchProvider

    model = CountingPlanModel()
    with TestClient(create_app(model, DeterministicSearchProvider())) as client:
        response = client.post(
            "/research",
            data={"question": "How should evidence quality be evaluated?"},
        )

    assert response.status_code == 200
    assert "SIMULATED DEVELOPMENT MODE" in response.text
    assert "Search queries" in response.text
    assert "Sources and verification" in response.text
    assert "Research iterations" in response.text
    assert "Iteration 1" in response.text
    assert "Termination: evidence sufficient" in response.text
    assert "Bounded research result" in response.text
    assert "Phase 3 boundary reached" in response.text


def test_research_route_preserves_input_validation() -> None:
    model = CountingPlanModel()
    with TestClient(create_app(model)) as client:
        response = client.post("/research", data={"question": "  "})

    assert response.status_code == 400
    assert "Enter a research question" in response.text
    assert model.calls == []
