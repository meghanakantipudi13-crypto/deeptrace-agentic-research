"""Provider-neutral research memory contract and safe identifier handling."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.memory.models import ResearchMemoryRecord, ResearchMemorySummary


MAX_MEMORY_RECORD_BYTES = 1_000_000


class MemoryNotFoundError(LookupError):
    """The requested durable research record does not exist."""


class MemoryCorruptionError(RuntimeError):
    """A stored record is malformed, unsupported, or exceeds safety limits."""


def validate_session_id(session_id: str) -> str:
    """Return a canonical UUID and reject path-like or ambiguous identifiers."""

    try:
        value = UUID(session_id)
    except (TypeError, ValueError) as error:
        raise MemoryNotFoundError("Research session was not found.") from error
    canonical = str(value)
    if session_id != canonical:
        raise MemoryNotFoundError("Research session was not found.")
    return canonical


class ResearchMemoryRepository(Protocol):
    """Minimal async persistence interface shared by local and GCS adapters."""

    async def save(self, record: ResearchMemoryRecord) -> None: ...

    async def get(self, session_id: str) -> ResearchMemoryRecord: ...

    async def list_recent(self, limit: int = 20) -> list[ResearchMemorySummary]: ...
