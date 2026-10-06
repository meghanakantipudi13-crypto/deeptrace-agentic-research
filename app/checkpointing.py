"""Supported LangGraph checkpoint backends kept separate from research memory."""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from app.logging import log_event


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[BaseCheckpointSaver]:
    """Open the configured saver for the full FastAPI application lifespan."""

    backend = os.getenv("DEEPTRACE_CHECKPOINT_BACKEND", "memory").strip().lower()
    logger = logging.getLogger("deeptrace.checkpointing")
    log_event(logger, "checkpoint_backend_selected", backend=backend)
    if backend == "memory":
        yield InMemorySaver()
        return
    if backend == "sqlite":
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        except ImportError as error:
            raise RuntimeError(
                "Install the 'dev' dependency group for local SQLite checkpoints."
            ) from error
        sqlite_path = os.getenv(
            "DEEPTRACE_SQLITE_PATH", ".deeptrace-checkpoints.sqlite"
        ).strip()
        if not sqlite_path:
            raise RuntimeError("DEEPTRACE_SQLITE_PATH is required for SQLite checkpoints.")
        async with AsyncSqliteSaver.from_conn_string(sqlite_path) as saver:
            yield saver
        return
    if backend != "postgres":
        raise RuntimeError(f"Unsupported DEEPTRACE_CHECKPOINT_BACKEND: {backend}")

    connection_uri = os.getenv("DEEPTRACE_POSTGRES_URI", "").strip()
    if not connection_uri:
        raise RuntimeError("DEEPTRACE_POSTGRES_URI is required for PostgreSQL checkpoints.")
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    except ImportError as error:
        raise RuntimeError(
            "Install the 'production' dependency group for PostgreSQL checkpoints."
        ) from error

    async with AsyncPostgresSaver.from_conn_string(connection_uri) as saver:
        if os.getenv("DEEPTRACE_POSTGRES_SETUP", "false").lower() == "true":
            await saver.setup()
        yield saver
