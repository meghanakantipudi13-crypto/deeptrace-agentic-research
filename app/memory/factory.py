"""Environment-driven research memory selection."""

from __future__ import annotations

import os
from pathlib import Path

from app.memory.base import ResearchMemoryRepository
from app.memory.filesystem import FileSystemResearchMemory
from app.memory.gcs import GCSResearchMemory


def build_memory_repository() -> ResearchMemoryRepository:
    backend = os.getenv("DEEPTRACE_MEMORY_BACKEND", "filesystem").strip().lower()
    if backend == "filesystem":
        root = Path(os.getenv("DEEPTRACE_MEMORY_DIR", ".deeptrace-memory"))
        return FileSystemResearchMemory(root)
    if backend == "gcs":
        bucket = os.getenv("DEEPTRACE_GCS_BUCKET", "").strip()
        if not bucket:
            raise RuntimeError("DEEPTRACE_GCS_BUCKET is required for GCS memory.")
        return GCSResearchMemory(bucket)
    raise RuntimeError(f"Unsupported DEEPTRACE_MEMORY_BACKEND: {backend}")
