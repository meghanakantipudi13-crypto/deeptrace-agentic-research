"""Atomic local-filesystem research memory for development and restart tests."""

from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path

from pydantic import ValidationError

from app.memory.base import (
    MAX_MEMORY_RECORD_BYTES,
    MemoryCorruptionError,
    MemoryNotFoundError,
    validate_session_id,
)
from app.memory.models import ResearchMemoryRecord, ResearchMemorySummary


class FileSystemResearchMemory:
    """Store one bounded JSON document per canonical UUID."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        canonical = validate_session_id(session_id)
        path = (self._root / f"{canonical}.json").resolve()
        if path.parent != self._root:
            raise MemoryNotFoundError("Research session was not found.")
        return path

    @staticmethod
    def _serialize(record: ResearchMemoryRecord) -> bytes:
        payload = record.model_dump_json(indent=2).encode("utf-8")
        if len(payload) > MAX_MEMORY_RECORD_BYTES:
            raise MemoryCorruptionError("Research memory record exceeds the size limit.")
        return payload

    def _read(self, path: Path) -> ResearchMemoryRecord:
        try:
            if path.stat().st_size > MAX_MEMORY_RECORD_BYTES:
                raise MemoryCorruptionError("Research memory record exceeds the size limit.")
            return ResearchMemoryRecord.model_validate_json(path.read_bytes())
        except FileNotFoundError as error:
            raise MemoryNotFoundError("Research session was not found.") from error
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValidationError) as error:
            raise MemoryCorruptionError("Research memory record is invalid.") from error

    async def save(self, record: ResearchMemoryRecord) -> None:
        payload = self._serialize(record)
        destination = self._path(record.session_id)

        def write() -> None:
            descriptor, temporary_name = tempfile.mkstemp(
                dir=self._root, prefix=".pending-", suffix=".json"
            )
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, destination)
            except Exception:
                try:
                    os.unlink(temporary_name)
                except FileNotFoundError:
                    pass
                raise

        await asyncio.to_thread(write)

    async def get(self, session_id: str) -> ResearchMemoryRecord:
        path = self._path(session_id)
        return await asyncio.to_thread(self._read, path)

    async def list_recent(self, limit: int = 20) -> list[ResearchMemorySummary]:
        bounded_limit = max(1, min(limit, 100))

        def read_all() -> list[ResearchMemorySummary]:
            summaries: list[ResearchMemorySummary] = []
            for path in self._root.glob("*.json"):
                try:
                    summaries.append(self._read(path).summary())
                except (MemoryCorruptionError, MemoryNotFoundError):
                    continue
            summaries.sort(key=lambda item: item.stored_at, reverse=True)
            return summaries[:bounded_limit]

        return await asyncio.to_thread(read_all)
