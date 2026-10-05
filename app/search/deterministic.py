"""Deterministic simulated retrieval for development and ordinary tests."""

from __future__ import annotations

import hashlib

from app.models import ProviderSearchResult, SearchBatch


class DeterministicSearchProvider:
    """Return fake `.test` sources that can never be confused with live research."""

    provider_name = "deterministic-fixture-search"
    is_simulated = True

    def __init__(self, reason: str = "development mode") -> None:
        self.reason = reason

    async def search(self, query: str, limit: int) -> SearchBatch:
        query_key = hashlib.sha256(query.encode("utf-8")).hexdigest()[:10]
        fixtures = [
            ProviderSearchResult(
                title="Simulated evidence overview",
                url="https://evidence.deeptrace.test/overview",
                content=(
                    f"Simulated source evidence for the query '{query}'. "
                    "It describes definitions, reported observations, and scope constraints for development testing."
                ),
                provider=self.provider_name,
                rank=1,
                provider_score=0.91,
            ),
            ProviderSearchResult(
                title="Simulated methods note",
                url=f"https://evidence.deeptrace.test/methods/{query_key}",
                content=(
                    f"A simulated methods note related to {query}. "
                    "It identifies measurement choices and uncertainty that a later research pass should inspect."
                ),
                provider=self.provider_name,
                rank=2,
                provider_score=0.76,
            ),
            ProviderSearchResult(
                title="Simulated unrelated result",
                url=f"https://evidence.deeptrace.test/unrelated/{query_key}",
                content="A simulated article about bread recipes and kitchen equipment.",
                provider=self.provider_name,
                rank=3,
                provider_score=0.08,
            ),
        ]
        return SearchBatch(results=fixtures[: max(0, limit)], credits_used=0)
