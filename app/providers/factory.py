"""Environment-based planning provider selection."""

from __future__ import annotations

import os

from app.providers.base import PlanModel
from app.providers.deterministic import DeterministicPlanModel
from app.providers.vertex import VertexAIPlanModel


def build_plan_model() -> PlanModel:
    requested = os.getenv("DEEPTRACE_MODEL_PROVIDER", "deterministic").strip().lower()
    if requested in {"deterministic", "simulated", "fixture"}:
        return DeterministicPlanModel()
    if requested == "vertex":
        return VertexAIPlanModel(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", ""),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", ""),
            model=os.getenv("DEEPTRACE_MODEL", ""),
        )
    raise ValueError(f"Unsupported DEEPTRACE_MODEL_PROVIDER: {requested}")
