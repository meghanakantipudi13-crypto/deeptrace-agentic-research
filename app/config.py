"""Fail-closed environment validation for production provider mode."""

from __future__ import annotations

import os
from collections.abc import Mapping


PRODUCTION_ENVIRONMENT = "production"


def is_production_environment(environment: Mapping[str, str] | None = None) -> bool:
    values = os.environ if environment is None else environment
    return values.get("DEEPTRACE_ENV", "development").strip().lower() == PRODUCTION_ENVIRONMENT


def validate_production_environment(
    environment: Mapping[str, str] | None = None,
) -> None:
    """Reject incomplete or simulated production configuration without exposing values."""

    values = os.environ if environment is None else environment
    if not is_production_environment(values):
        return

    required = (
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION",
        "DEEPTRACE_MODEL",
        "TAVILY_API_KEY",
        "DEEPTRACE_GCS_BUCKET",
        "DEEPTRACE_POSTGRES_URI",
    )
    problems = [name for name in required if not values.get(name, "").strip()]
    expected = {
        "DEEPTRACE_MODEL_PROVIDER": "vertex",
        "SEARCH_PROVIDER": "tavily",
        "DEEPTRACE_MEMORY_BACKEND": "gcs",
        "DEEPTRACE_CHECKPOINT_BACKEND": "postgres",
    }
    for name, expected_value in expected.items():
        if values.get(name, "").strip().lower() != expected_value:
            problems.append(f"{name}={expected_value}")
    if problems:
        joined = ", ".join(problems)
        raise RuntimeError(
            "Production configuration is incomplete or unsafe; configure: " + joined
        )
