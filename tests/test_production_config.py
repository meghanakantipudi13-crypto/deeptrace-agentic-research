from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from app.config import validate_production_environment
from app.providers.vertex import VertexAIPlanModel
from app.search.factory import build_search_provider


def _complete_production_environment() -> dict[str, str]:
    return {
        "DEEPTRACE_ENV": "production",
        "DEEPTRACE_MODEL_PROVIDER": "vertex",
        "GOOGLE_CLOUD_PROJECT": "test-project",
        "GOOGLE_CLOUD_LOCATION": "global",
        "DEEPTRACE_MODEL": "gemini-test",
        "SEARCH_PROVIDER": "tavily",
        "TAVILY_API_KEY": "test-secret",
        "DEEPTRACE_MEMORY_BACKEND": "gcs",
        "DEEPTRACE_GCS_BUCKET": "test-bucket",
        "DEEPTRACE_CHECKPOINT_BACKEND": "postgres",
        "DEEPTRACE_POSTGRES_URI": "postgresql://test.invalid/deeptrace",
    }


def test_production_configuration_is_fail_closed_without_secrets() -> None:
    with pytest.raises(RuntimeError) as captured:
        validate_production_environment({"DEEPTRACE_ENV": "production"})

    message = str(captured.value)
    assert "TAVILY_API_KEY" in message
    assert "DEEPTRACE_MODEL_PROVIDER=vertex" in message
    assert "deterministic" not in message.lower()


def test_complete_production_configuration_passes_without_external_calls() -> None:
    validate_production_environment(_complete_production_environment())


def test_production_tavily_selection_never_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("DEEPTRACE_ENV", "production")
    monkeypatch.setenv("SEARCH_PROVIDER", "tavily")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="deterministic fallback is disabled"):
        build_search_provider()


class _FakeModels:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            parsed={
                "objective": "Compare authoritative evidence.",
                "steps": [
                    {
                        "order": 1,
                        "title": "Collect official evidence",
                        "purpose": "Establish the primary facts.",
                        "evidence_needed": ["Official documentation"],
                    }
                ],
                "limitations": ["Live search still requires approval."],
            },
            usage_metadata=SimpleNamespace(
                prompt_token_count=41,
                candidates_token_count=23,
                total_token_count=64,
            ),
            model_version="gemini-test-001",
        )


def test_vertex_planner_uses_structured_output_and_captures_usage() -> None:
    models = _FakeModels()
    client = SimpleNamespace(aio=SimpleNamespace(models=models))
    provider = VertexAIPlanModel(
        project="test-project",
        location="global",
        model="gemini-test",
        client=client,
    )

    plan = asyncio.run(provider.create_plan("What should be compared?"))

    assert plan.is_simulated is False
    assert plan.model_name == "gemini-test-001"
    assert plan.input_tokens == 41
    assert plan.output_tokens == 23
    assert plan.total_tokens == 64
    assert plan.model_latency_ms is not None
    assert models.calls[0]["model"] == "gemini-test"
    assert models.calls[0]["config"]["response_mime_type"] == "application/json"
