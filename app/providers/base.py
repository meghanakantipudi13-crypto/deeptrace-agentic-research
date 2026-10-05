"""Provider interfaces used by the planning workflow."""

from __future__ import annotations

from typing import Protocol

from app.models import ResearchPlan


class PlanModel(Protocol):
    """Small seam for a future Vertex AI planner and deterministic tests."""

    async def create_plan(self, question: str) -> ResearchPlan:
        """Return a validated structured plan for the normalized question."""
        ...
