"""Small structured-logging helpers for workflow observability."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    """Render log records as one-line JSON without request content."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event_data = getattr(record, "event_data", None)
        if isinstance(event_data, dict):
            payload.update(event_data)
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level: int = logging.INFO) -> None:
    """Configure DeepTrace logging once, leaving other loggers untouched."""

    logger = logging.getLogger("deeptrace")
    logger.setLevel(level)
    if not any(getattr(handler, "deeptrace_handler", False) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler.deeptrace_handler = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    logger.propagate = False


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """Log an allowlisted event payload supplied by application code."""

    logger.info(event, extra={"event_data": {"event": event, **fields}})
