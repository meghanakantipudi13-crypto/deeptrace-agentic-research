"""Google Cloud Storage adapter for durable cross-session research memory."""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import ValidationError

from app.memory.base import (
    MAX_MEMORY_RECORD_BYTES,
    MemoryCorruptionError,
    MemoryNotFoundError,
    validate_session_id,
)
from app.memory.models import ResearchMemoryRecord, ResearchMemorySummary


class GCSResearchMemory:
    """Persist versioned records with safe, UUID-only object names."""

    _PREFIX = "research-sessions/"

    def __init__(self, bucket_name: str, client: Any | None = None) -> None:
        if not bucket_name or len(bucket_name) > 222:
            raise ValueError("A valid DEEPTRACE_GCS_BUCKET is required.")
        if client is None:
            try:
                from google.cloud import storage
            except ImportError as error:
                raise RuntimeError(
                    "Install the 'production' dependency group for GCS memory."
                ) from error
            client = storage.Client()
        self._client = client
        self._bucket_name = bucket_name
        self._bucket = client.bucket(bucket_name)

    @classmethod
    def object_name(cls, session_id: str) -> str:
        return f"{cls._PREFIX}{validate_session_id(session_id)}.json"

    @staticmethod
    def _decode(payload: bytes) -> ResearchMemoryRecord:
        if len(payload) > MAX_MEMORY_RECORD_BYTES:
            raise MemoryCorruptionError("Research memory record exceeds the size limit.")
        try:
            return ResearchMemoryRecord.model_validate_json(payload)
        except ValidationError as error:
            raise MemoryCorruptionError("Research memory record is invalid.") from error

    async def save(self, record: ResearchMemoryRecord) -> None:
        payload = record.model_dump_json(indent=2).encode("utf-8")
        if len(payload) > MAX_MEMORY_RECORD_BYTES:
            raise MemoryCorruptionError("Research memory record exceeds the size limit.")
        blob = self._bucket.blob(self.object_name(record.session_id))
        await asyncio.to_thread(
            blob.upload_from_string,
            payload,
            content_type="application/json",
            if_generation_match=0,
        )

    async def get(self, session_id: str) -> ResearchMemoryRecord:
        blob = self._bucket.blob(self.object_name(session_id))
        try:
            payload = await asyncio.to_thread(blob.download_as_bytes)
        except Exception as error:
            if getattr(error, "code", None) == 404:
                raise MemoryNotFoundError("Research session was not found.") from error
            raise
        return self._decode(payload)

    async def list_recent(self, limit: int = 20) -> list[ResearchMemorySummary]:
        bounded_limit = max(1, min(limit, 100))
        blobs = await asyncio.to_thread(
            lambda: list(self._client.list_blobs(self._bucket_name, prefix=self._PREFIX))
        )
        summaries: list[ResearchMemorySummary] = []
        for blob in blobs:
            try:
                payload = await asyncio.to_thread(blob.download_as_bytes)
                summaries.append(self._decode(payload).summary())
            except MemoryCorruptionError:
                continue
        summaries.sort(key=lambda item: item.stored_at, reverse=True)
        return summaries[:bounded_limit]
