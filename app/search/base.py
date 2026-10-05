"""Provider-neutral search contract."""

from __future__ import annotations

from typing import Protocol

from app.models import SearchBatch


class SearchProvider(Protocol):
    """Replaceable bounded search interface used only by graph nodes."""

    provider_name: str
    is_simulated: bool

    async def search(self, query: str, limit: int) -> SearchBatch:
        """Return normalized provider results and reported usage facts."""
        ...
