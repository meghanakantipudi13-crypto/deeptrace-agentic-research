"""Foundational research-question validation for Phase 1."""

from __future__ import annotations

import unicodedata

from app.models import MAX_QUESTION_LENGTH


class QuestionValidationError(ValueError):
    """A user-correctable research-question error."""


def normalize_question(value: str) -> str:
    """Normalize visible text, remove malformed controls, and validate length."""

    if not isinstance(value, str):
        raise QuestionValidationError("Enter a research question as text.")

    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.category(character).startswith("C")
        or character in {"\t", "\n", "\r"}
    )
    normalized = " ".join(normalized.split())

    if not normalized:
        raise QuestionValidationError("Enter a research question before creating a plan.")
    if len(normalized) > MAX_QUESTION_LENGTH:
        raise QuestionValidationError(
            f"Keep the research question to {MAX_QUESTION_LENGTH} characters or fewer."
        )
    return normalized
