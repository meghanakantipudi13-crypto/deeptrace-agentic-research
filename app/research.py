"""Pure query, normalization, verification, criticism, and synthesis functions."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.models import (
    MAX_FOLLOWUP_QUERIES,
    MAX_INITIAL_QUERIES,
    MAX_SOURCE_CONTENT_LENGTH,
    MAX_TOTAL_SOURCES,
    Citation,
    CitedClaim,
    EvidenceGap,
    EvidenceSufficiency,
    EvidenceVerification,
    PreliminaryResearchResult,
    ProviderSearchResult,
    ResearchPlan,
    SearchQuery,
    Source,
)
from app.safety import contains_instruction_like_text


_WORDS = re.compile(r"[a-z0-9][a-z0-9'-]*", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "for", "from",
    "how", "in", "is", "it", "of", "on", "or", "should", "the", "to", "what",
    "when", "where", "which", "who", "why", "with", "would",
}
_TRACKING_QUERY_KEYS = {"ref", "source", "fbclid", "gclid"}


def _tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in _WORDS.findall(text)
        if len(token) > 2 and token.lower() not in _STOPWORDS
    }


def generate_search_queries(
    question: str,
    plan: ResearchPlan,
    limit: int = MAX_INITIAL_QUERIES,
) -> list[SearchQuery]:
    """Derive distinct bounded queries from plan steps, not repeated raw input."""

    queries: list[SearchQuery] = []
    seen: set[str] = set()
    subject = question.rstrip(" ?.!")
    for step in plan.steps:
        evidence_hint = step.evidence_needed[0] if step.evidence_needed else "supporting evidence"
        text = f'{subject} — {step.title}: {evidence_hint}'[:350]
        normalized = " ".join(text.lower().split())
        if normalized in seen or normalized == " ".join(question.lower().split()):
            continue
        seen.add(normalized)
        queries.append(
            SearchQuery(
                query_id=f"Q{len(queries) + 1}",
                plan_step_order=step.order,
                text=text,
            )
        )
        if len(queries) >= max(1, min(limit, MAX_INITIAL_QUERIES)):
            break
    return queries


def generate_followup_queries(
    question: str,
    plan: ResearchPlan,
    critic: EvidenceSufficiency,
    previous_queries: list[SearchQuery],
    iteration: int,
    limit: int = MAX_FOLLOWUP_QUERIES,
) -> list[SearchQuery]:
    """Create bounded, gap-targeted queries while suppressing prior query text."""

    steps = {step.order: step for step in plan.steps}
    seen = {" ".join(query.text.lower().split()) for query in previous_queries}
    queries: list[SearchQuery] = []
    for gap in critic.evidence_gaps:
        step = steps.get(gap.plan_step_order)
        if step is None:
            continue
        evidence_hint = "; ".join(step.evidence_needed[:2])
        text = (
            f"{question.rstrip(' ?.!')} — follow-up evidence for {step.title}: "
            f"{gap.description}; seek {evidence_hint}"
        )[:350]
        normalized = " ".join(text.lower().split())
        if normalized in seen:
            continue
        seen.add(normalized)
        queries.append(
            SearchQuery(
                query_id=f"Q{len(previous_queries) + len(queries) + 1}",
                plan_step_order=gap.plan_step_order,
                text=text,
                iteration=iteration,
                evidence_gap=gap.description,
            )
        )
        if len(queries) >= max(1, min(limit, MAX_FOLLOWUP_QUERIES)):
            break
    return queries


def canonicalize_url(url: str) -> str | None:
    """Return a stable HTTP(S) URL for safe deduplication, or reject it."""

    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
        )
    )
    path = parsed.path.rstrip("/") or "/"
    host = parsed.hostname.lower()
    try:
        port = parsed.port
    except ValueError:
        return None
    if port:
        host = f"{host}:{port}"
    return urlunsplit((parsed.scheme.lower(), host, path, query, ""))


def normalize_and_deduplicate_sources(
    collected: list[tuple[SearchQuery, ProviderSearchResult]],
    *,
    is_simulated: bool,
    total_limit: int = MAX_TOTAL_SOURCES,
    existing_sources: list[Source] | None = None,
    retrieval_iteration: int = 1,
) -> tuple[list[Source], int]:
    """Attach provenance and deduplicate against current and prior iterations."""

    existing_sources = existing_sources or []
    retained: list[Source] = []
    seen_urls = {source.canonical_url for source in existing_sources}
    duplicates_removed = 0
    retrieved_at = datetime.now(UTC).isoformat()
    bounded_total_limit = max(1, min(total_limit, MAX_TOTAL_SOURCES))
    if len(existing_sources) >= bounded_total_limit:
        return retained, 0
    for query, result in collected:
        canonical_url = canonicalize_url(result.url)
        if canonical_url is None:
            continue
        if canonical_url in seen_urls:
            duplicates_removed += 1
            continue
        seen_urls.add(canonical_url)
        content = " ".join(result.content.split())[:MAX_SOURCE_CONTENT_LENGTH]
        retained.append(
            Source(
                source_id=f"S{len(existing_sources) + len(retained) + 1}",
                title=result.title,
                url=result.url,
                canonical_url=canonical_url,
                content=content,
                query_id=query.query_id,
                query_text=query.text,
                plan_step_order=query.plan_step_order,
                provider=result.provider,
                rank=result.rank,
                provider_score=result.provider_score,
                retrieved_at=retrieved_at,
                is_simulated=is_simulated,
                instruction_like=contains_instruction_like_text(content),
                retrieval_iteration=retrieval_iteration,
            )
        )
        if len(existing_sources) + len(retained) >= bounded_total_limit:
            break
    return retained, duplicates_removed


def evaluate_evidence_sufficiency(
    plan: ResearchPlan,
    sources: list[Source],
    verifications: list[EvidenceVerification],
    iteration: int,
) -> EvidenceSufficiency:
    """Assess plan coverage without treating evidence as universal factual truth."""

    decisions = {item.source_id: item for item in verifications}
    sources_by_step: dict[int, list[Source]] = {}
    for source in sources:
        sources_by_step.setdefault(source.plan_step_order, []).append(source)

    gaps: list[EvidenceGap] = []
    supported_steps = 0
    for step in plan.steps:
        step_sources = sources_by_step.get(step.order, [])
        step_decisions = [
            decisions[source.source_id]
            for source in step_sources
            if source.source_id in decisions
        ]
        if any(
            decision.accepted_for_synthesis and decision.support_level == "supportive"
            for decision in step_decisions
        ):
            supported_steps += 1
            continue
        if not step_sources:
            issue = "missing"
            description = "No retained source covers this plan item."
        elif any(decision.accepted_for_synthesis for decision in step_decisions):
            issue = "weak"
            description = "Only contextual evidence is available; supportive evidence is missing."
        else:
            issue = "rejected"
            description = "Retrieved candidates were rejected as irrelevant, insufficient, or unsafe."
        gaps.append(
            EvidenceGap(
                plan_step_order=step.order,
                plan_step_title=step.title,
                issue=issue,
                description=description,
            )
        )

    total_steps = len(plan.steps)
    confidence = supported_steps / total_steps
    is_sufficient = not gaps
    recommendations = [
        (
            f"Follow up on plan item {gap.plan_step_order} ({gap.plan_step_title}): "
            f"{gap.description}"
        )
        for gap in gaps[:MAX_FOLLOWUP_QUERIES]
    ]
    reason = (
        "Every research-plan item has at least one accepted supportive source."
        if is_sufficient
        else f"{len(gaps)} of {total_steps} research-plan items still lack supportive evidence."
    )
    return EvidenceSufficiency(
        iteration=iteration,
        is_sufficient=is_sufficient,
        confidence=round(confidence, 3),
        evidence_gaps=gaps,
        unsupported_subquestions=[gap.plan_step_order for gap in gaps],
        conflicts_detected=[],
        reason=(
            f"{reason} Conflict detection is limited because current snippets do not "
            "encode normalized claim stances."
        ),
        recommended_followup_queries=recommendations,
    )


def _quality_signal(url: str) -> str:
    hostname = (urlsplit(url).hostname or "").lower()
    if hostname.endswith(".gov") or ".gov." in hostname:
        return "official-domain-signal"
    if hostname.endswith(".edu") or ".edu." in hostname:
        return "academic-domain-signal"
    return "unknown"


def verify_sources(
    question: str,
    plan: ResearchPlan,
    sources: list[Source],
) -> list[EvidenceVerification]:
    """Apply explicit deterministic relevance/support checks to each source."""

    steps = {step.order: step for step in plan.steps}
    verifications: list[EvidenceVerification] = []
    for source in sources:
        step = steps.get(source.plan_step_order)
        target_text = " ".join(
            [
                question,
                step.title if step else "",
                step.purpose if step else "",
                " ".join(step.evidence_needed) if step else "",
            ]
        )
        target_tokens = _tokens(target_text)
        source_tokens = _tokens(f"{source.title} {source.content}")
        overlap = len(target_tokens & source_tokens)
        denominator = max(1, min(len(target_tokens), 8))
        relevance_score = min(1.0, overlap / denominator)
        relevant = relevance_score >= 0.125
        if source.instruction_like:
            support_level = "insufficient"
            accepted = False
            reason = "Instruction-like text was quarantined as untrusted content."
        elif relevant and len(source.content) >= 80:
            support_level = "supportive"
            accepted = True
            reason = "The snippet overlaps the linked plan item and contains substantive text."
        elif relevant and source.content:
            support_level = "contextual"
            accepted = True
            reason = "The snippet is relevant but provides limited context rather than strong support."
        else:
            support_level = "insufficient"
            accepted = False
            reason = "The snippet does not materially overlap the question and linked plan item."
        verifications.append(
            EvidenceVerification(
                source_id=source.source_id,
                plan_step_order=source.plan_step_order,
                relevant=relevant,
                relevance_score=round(relevance_score, 3),
                support_level=support_level,
                quality_signal=_quality_signal(source.url),
                accepted_for_synthesis=accepted,
                instruction_like=source.instruction_like,
                reason=reason,
            )
        )
    return verifications


def _first_sentence(content: str, limit: int = 500) -> str:
    compact = " ".join(content.split())
    match = re.search(r"(?<=[.!?])\s", compact)
    sentence = compact[: match.start() + 1] if match else compact
    return sentence[:limit].rstrip()


def validate_citation_mapping(
    result: PreliminaryResearchResult,
    citations: list[Citation],
    sources: list[Source],
) -> None:
    """Fail closed if a claim cites anything outside retained source metadata."""

    sources_by_id = {source.source_id: source for source in sources}
    citation_ids = {citation.citation_id for citation in citations}
    if len(citation_ids) != len(citations):
        raise ValueError("Citation IDs must be unique.")
    for citation in citations:
        source = sources_by_id.get(citation.source_id)
        if source is None or citation.citation_id != citation.source_id:
            raise ValueError(f"Citation {citation.citation_id} does not map to a retained source.")
        if citation.title != source.title or citation.url != source.url:
            raise ValueError(
                f"Citation {citation.citation_id} metadata does not match its retained source."
            )
    for claim in result.claims:
        missing = set(claim.citation_ids) - citation_ids
        if missing:
            raise ValueError(f"Claim references nonexistent citations: {sorted(missing)}")


def synthesize_preliminary_result(
    question: str,
    sources: list[Source],
    verifications: list[EvidenceVerification],
    *,
    critic: EvidenceSufficiency | None = None,
    termination_reason: str | None = None,
    retrieval_passes: int = 1,
) -> tuple[PreliminaryResearchResult, list[Citation]]:
    """Create an extractive result using accumulated accepted evidence only."""

    decisions = {verification.source_id: verification for verification in verifications}
    accepted = [
        source
        for source in sources
        if decisions.get(source.source_id)
        and decisions[source.source_id].accepted_for_synthesis
    ]
    citations = [
        Citation(
            citation_id=source.source_id,
            source_id=source.source_id,
            title=source.title,
            url=source.url,
        )
        for source in accepted
    ]
    claims = [
        CitedClaim(
            text=f"{source.title} reports: {_first_sentence(source.content)}",
            citation_ids=[source.source_id],
        )
        for source in accepted[:5]
        if source.content
    ]
    if claims:
        summary = (
            f"For the question '{question}', {retrieval_passes} bounded retrieval pass(es) "
            f"retained {len(accepted)} accepted source snippets."
        )
    else:
        summary = (
            f"For the question '{question}', the bounded retrieval process did not find evidence "
            "that met the foundational relevance and support checks."
        )
    incomplete = bool(critic and not critic.is_sufficient)
    if incomplete:
        summary += (
            f" Evidence remained incomplete at termination ({termination_reason}); "
            f"unsupported plan items: {critic.unsupported_subquestions}."
        )
    result = PreliminaryResearchResult(
        summary=summary,
        claims=claims,
        limitations=[
            f"The workflow stopped after {retrieval_passes} bounded retrieval pass(es).",
            "Source quality signals are heuristic and do not establish objective truth.",
            (
                "The critic still identified unresolved evidence gaps."
                if incomplete
                else "The deterministic critic found supportive coverage for every plan item."
            ),
        ],
    )
    validate_citation_mapping(result, citations, sources)
    return result, citations
