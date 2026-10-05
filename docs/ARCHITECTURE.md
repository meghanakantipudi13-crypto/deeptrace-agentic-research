# Proposed Minimum Compliant Architecture

## Design goals

The architecture must make agentic behavior visible, ensure approval and safety decisions are code-enforced, preserve durable evidence, and remain small enough to test and deploy reliably.

## Components

1. **FastAPI web application** — serves HTML, APIs, and a server-sent event stream. It authenticates/identifies a demo user, validates requests, and exposes plan approval, modification, and cancellation actions.
2. **Research workflow** — a LangGraph state graph with typed state and explicit transitions: validate → plan → persist/pause → approval router → retrieve → evaluate → verify → critic → revise-or-synthesize → citation/output validation → persist.
3. **Model adapter** — structured-output interface for planning, query revision, evidence judgments, criticism, and synthesis. Model output never directly selects privileged tools or marks approval.
4. **Search/fetch adapter** — issues bounded queries, validates URLs/redirects, retrieves limited content, normalizes metadata, and labels all content untrusted.
5. **Evidence store** — keeps immutable source snapshots or permitted excerpts with content hashes, fetch timestamps, canonical URLs, quality/relevance scores, and claim links.
6. **Session store** — atomically stores workflow stage, plan version, approval decision, revision, budgets, and trace references.
7. **Safety policy engine** — deterministic input, URL, state-transition, budget, schema, and citation controls plus optional injection-risk classification.
8. **Event recorder** — writes redacted structured events for UI progress, evaluation traces, latency, usage, cost estimation, and cloud monitoring.
9. **Evaluation runner** — submits versioned cases through the same public workflow interfaces and scores retained artifacts.

## State and trust boundaries

- System/developer policy is immutable application configuration.
- User input is untrusted and may request research, not policy changes.
- Retrieved content is untrusted evidence, stored in a dedicated field with provenance; it is never appended to system instructions.
- Only the authenticated approval endpoint can change `approval_status`, and it must supply the current plan revision/idempotency key.
- Only deterministic workflow code can advance stages, consume budgets, or select the next graph node.
- Model judgments are advisory structured data validated against schemas and policy.

## Core state

```text
ResearchSession
  session_id, user_id, question, status, plan_revision
  plan_tasks[], approval_status, approval_actor, approved_at
  retrieval_iteration, max_iterations, call_budget
  queries[], sources[], evidence_items[], candidate_claims[]
  gaps[], conflicts[], critic_decision
  report, citations[], guardrail_events[]
  usage, latency, trace_id, created_at, updated_at
```

## Enforced workflow

```text
validate -> plan -> persist WAITING_FOR_APPROVAL
                       | approve/modify | reject
                       v                v
                    retrieve         CANCELLED
                       v
                 score + verify
                       v
                     critic
                    /      \
       gap + budget left    sufficient or budget exhausted
                v                       v
        revise actual query       synthesize or safe uncertainty
                |                       v
                +-> retrieve       citation/output validation
                                            v
                                      durable persistence
```

`WAITING_FOR_APPROVAL` cannot route to retrieval. A modified plan increments the revision and requires explicit approval of that revision. On exhausted budgets, synthesis may only state evidence-supported conclusions and disclose unresolved gaps.

## Persistence plan

- **Cloud SQL PostgreSQL:** future official LangGraph production checkpointer for mutable thread state, interrupt/resume, approval decisions, and idempotency.
- **GCS:** future immutable/versioned evidence artifacts, reports, redacted traces, memory exports, and evaluation results. Bucket versioning and retention settings will be evaluated against cost and privacy requirements.
- **Phase 1:** no checkpointer or long-term store. The graph is request-scoped and ends after planning.
- **Local development later:** replaceable test adapters and possibly SQLite for persistence-specific development tests only. Passing local persistence tests will not verify cloud durability.

GCS will not be used as a live SQLite filesystem or custom checkpointer unless a later decision supplies concurrency, atomicity, and restart evidence. Firestore is no longer the default because it would also require custom LangGraph checkpoint integration.

## Safety controls

- Request schema, length, Unicode normalization, and prohibited-action checks.
- Direct injection signals produce a guardrail event and bounded safe handling.
- HTTP(S)-only URL parsing, private/reserved address blocking, DNS rebinding/redirect checks, MIME/size/time limits, and disabled active content.
- Provenance wrappers and content hashes for all retrieved evidence.
- Strict structured model outputs and allowlisted enum transitions.
- Approval, iteration, call, source, content, token, timeout, and cost ceilings enforced outside the model.
- Claim-to-citation mapping plus final URL/source existence checks.
- Secret and sensitive-content redaction before logging.
- Fail closed on ambiguous approval, persistence conflicts, schema failure, or citation validation failure.

## Observability events

At minimum: `request_validated`, `plan_created`, `approval_waiting`, `plan_modified`, `plan_approved`, `plan_rejected`, `query_issued`, `source_retrieved`, `source_blocked`, `evidence_scored`, `claim_verified`, `critic_gap`, `query_revised`, `budget_exhausted`, `report_validated`, `guardrail_triggered`, `session_persisted`, and `workflow_failed`.

Events include IDs, timestamps, duration, attempt counts, decision codes, provider usage, and content hashes—not raw secrets or unnecessary full prompts.

## Deployment shape pending clarification

The core is packaged as one container. The assignment-specific adapter may either run DeepTrace as a Hermes skill/plugin/workspace process or place a Hermes gateway and DeepTrace process in the same Cloud Run Instance if the platform and instructor permit it. Ordinary request-driven Cloud Run remains a portability fallback, not the claimed submission topology.
