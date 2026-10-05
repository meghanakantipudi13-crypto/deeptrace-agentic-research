"""Environment-based search provider selection."""

from __future__ import annotations

import os

from app.search.base import SearchProvider
from app.search.deterministic import DeterministicSearchProvider
from app.search.tavily import TavilySearchProvider


def build_search_provider() -> SearchProvider:
    """Select live Tavily only when explicitly requested and credentialed."""

    requested = os.getenv("SEARCH_PROVIDER", "deterministic").strip().lower()
    if requested == "tavily":
        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if api_key:
            return TavilySearchProvider(api_key)
        return DeterministicSearchProvider(reason="TAVILY_API_KEY is not configured")
    if requested in {"deterministic", "simulated", "fixture"}:
        return DeterministicSearchProvider()
    raise ValueError(f"Unsupported SEARCH_PROVIDER: {requested}")
