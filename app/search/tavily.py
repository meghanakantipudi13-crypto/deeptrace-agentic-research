"""Minimal Tavily HTTP adapter without a provider-specific SDK dependency."""

from __future__ import annotations

from typing import Any

import httpx

from app.models import ProviderSearchResult, SearchBatch


class TavilySearchProvider:
    """Use Tavily's bounded source-attributed search endpoint."""

    provider_name = "tavily"
    is_simulated = False

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 20.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Tavily API key is required for live search.")
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def search(self, query: str, limit: int) -> SearchBatch:
        bounded_limit = min(max(limit, 1), 20)
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "search_depth": "basic",
                    "max_results": bounded_limit,
                    "topic": "general",
                    "include_answer": False,
                    "include_raw_content": False,
                    "include_images": False,
                    "include_usage": True,
                    "safe_search": True,
                },
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()

        results: list[ProviderSearchResult] = []
        for rank, item in enumerate(payload.get("results", [])[:bounded_limit], start=1):
            title = str(item.get("title") or "Untitled source").strip()[:500]
            url = str(item.get("url") or "").strip()[:2_000]
            if not url:
                continue
            score = item.get("score")
            results.append(
                ProviderSearchResult(
                    title=title,
                    url=url,
                    content=str(item.get("content") or "").strip()[:10_000],
                    provider=self.provider_name,
                    rank=rank,
                    provider_score=float(score) if isinstance(score, (int, float)) else None,
                    published_at=(
                        str(item["published_date"])[:100]
                        if item.get("published_date") is not None
                        else None
                    ),
                )
            )
        usage = payload.get("usage") or {}
        credits = usage.get("credits")
        return SearchBatch(
            results=results,
            credits_used=float(credits) if isinstance(credits, (int, float)) else None,
        )
