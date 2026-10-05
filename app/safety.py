"""Foundational structural boundary for untrusted retrieved content."""

from __future__ import annotations

import re

from app.models import Source


_INSTRUCTION_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore (all |any )?(previous|prior|system|developer) instructions?",
        r"(?:important )?system message",
        r"skip (?:the )?(verification|verifier|workflow|research)",
        r"(?:change|grant|expand) (?:the )?(tool )?permissions?",
        r"(?:mark|treat) (?:this|the source) as (?:fully )?trusted",
        r"stop researching",
    )
)


def contains_instruction_like_text(content: str) -> bool:
    """Annotate obvious instruction-like evidence without granting it authority."""

    return any(pattern.search(content) for pattern in _INSTRUCTION_PATTERNS)


def format_untrusted_evidence(source: Source) -> str:
    """Delimiter contract for any future model call that receives evidence."""

    return (
        f'<untrusted_evidence source_id="{source.source_id}" '
        f'provider="{source.provider}">\n'
        f"{source.content}\n"
        "</untrusted_evidence>"
    )
