from __future__ import annotations

import asyncio
import json

import httpx

from app.search.tavily import TavilySearchProvider


def test_tavily_adapter_uses_bounded_http_contract_and_parses_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.tavily.com/search"
        assert request.headers["Authorization"] == "Bearer test-key"
        payload = json.loads(request.content)
        assert payload["max_results"] == 3
        assert payload["include_answer"] is False
        assert payload["include_raw_content"] is False
        assert payload["include_usage"] is True
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Official report",
                        "url": "https://example.gov/report",
                        "content": "Evidence snippet.",
                        "score": 0.82,
                    }
                ],
                "usage": {"credits": 1},
            },
        )

    provider = TavilySearchProvider(
        "test-key",
        transport=httpx.MockTransport(handler),
    )
    batch = asyncio.run(provider.search("test query", 3))

    assert provider.is_simulated is False
    assert batch.credits_used == 1
    assert len(batch.results) == 1
    assert batch.results[0].provider == "tavily"
    assert batch.results[0].url == "https://example.gov/report"
