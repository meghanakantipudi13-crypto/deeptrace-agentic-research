"""Credential-free development planner with explicitly simulated output."""

from __future__ import annotations

from app.models import PlanStep, ResearchPlan


class DeterministicPlanModel:
    """Create a stable planning scaffold without pretending to use an LLM."""

    async def create_plan(self, question: str) -> ResearchPlan:
        subject = question.rstrip(" ?.!") or question
        return ResearchPlan(
            question=question,
            objective=f"Prepare an evidence-driven investigation of: {subject}",
            steps=[
                PlanStep(
                    order=1,
                    title="Define scope and key terms",
                    purpose="Clarify the entities, time range, and comparison criteria required to answer the question.",
                    evidence_needed=[
                        "Authoritative definitions",
                        "Explicit scope and time boundaries",
                    ],
                ),
                PlanStep(
                    order=2,
                    title="Identify required evidence",
                    purpose="List the factual sub-questions and the source types best suited to support them.",
                    evidence_needed=[
                        "Primary or official sources",
                        "Independent corroborating sources",
                    ],
                ),
                PlanStep(
                    order=3,
                    title="Plan verification and synthesis",
                    purpose="Define how later phases should compare sources, handle conflicts, and cite supported conclusions.",
                    evidence_needed=[
                        "Claim-to-source mappings",
                        "Conflict and uncertainty notes",
                    ],
                ),
            ],
            provider_label="Deterministic development planner",
            is_simulated=True,
            limitations=[
                "This is simulated planning output for Phase 1 development.",
                "No retrieval, source verification, or research synthesis has occurred.",
            ],
        )
