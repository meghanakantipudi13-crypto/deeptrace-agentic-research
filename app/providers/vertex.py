"""Vertex AI Gemini planning provider with structured, bounded output."""

from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from pydantic import BaseModel, Field

from app.models import PlanStep, ResearchPlan


class _VertexPlanPayload(BaseModel):
    objective: str = Field(min_length=1, max_length=600)
    steps: list[PlanStep] = Field(min_length=1, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=5)


class VertexAIPlanModel:
    """Generate a typed research plan with the Google Gen AI SDK in Vertex mode."""

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        if not project.strip() or not location.strip() or not model.strip():
            raise ValueError("Vertex project, location, and model are required.")
        self.project = project.strip()
        self.location = location.strip()
        self.model = model.strip()
        if client is None:
            try:
                from google import genai
            except ImportError as error:  # pragma: no cover - production dependency path
                raise RuntimeError(
                    "Vertex planning requires the production dependency group: "
                    "pip install -e '.[production]'"
                ) from error
            client = genai.Client(
                vertexai=True,
                project=self.project,
                location=self.location,
            )
        self._client = client

    async def create_plan(self, question: str) -> ResearchPlan:
        started = perf_counter()
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=(
                "Create a concise evidence-oriented research plan for the user question. "
                "Each step must identify concrete evidence needed. Do not answer the "
                f"question or invent sources. User question: {question}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": _VertexPlanPayload,
                "temperature": 0.2,
            },
        )
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, _VertexPlanPayload):
            payload = parsed
        elif parsed is not None:
            payload = _VertexPlanPayload.model_validate(parsed)
        else:
            payload = _VertexPlanPayload.model_validate(json.loads(response.text))

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        model_version = getattr(response, "model_version", None) or self.model
        return ResearchPlan(
            question=question,
            objective=payload.objective,
            steps=payload.steps,
            provider_label=f"Vertex AI Gemini ({model_version})",
            is_simulated=False,
            model_name=str(model_version),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            model_latency_ms=round((perf_counter() - started) * 1000, 3),
            limitations=payload.limitations,
        )
