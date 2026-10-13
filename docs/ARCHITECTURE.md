# Proposed Minimum Compliant Architecture

## Design goals

The architecture must make agentic behavior visible, ensure approval and safety decisions are code-enforced, preserve durable evidence, and remain small enough to test and deploy reliably.

## Components

1. **FastAPI web application** — serves HTML, validates requests, rate-limits mutating routes within one process, and exposes plan approval, modification, cancellation, and history actions. Authentication/authorization remains deployment work.
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

### Current Phase 6 graph

```text
START -> start -> plan -> request approval -> approval_checkpoint interrupt
                                      PAUSED (zero search calls)
                         approve/modify | reject
                                        v
                  generate bounded queries | cancel -> END
                            -> retrieve
      -> normalize/deduplicate -> verify accumulated sources -> critic
          | sufficient / terminal reason -> citation-safe synthesis -> finish -> END
          | gap + budget remains -> revise gap-targeted queries
                                    -> retrieve -> verify -> critic
```

The graph accepts a configured LangGraph saver; a UUID `thread_id` identifies the checkpoint. `interrupt()` surfaces a safe plan payload and `Command(resume=...)` supplies a validated human decision to that same thread. Only approve/modify can cross into query generation. The maximum remains two retrieval passes. Retrieved content occurs after approval and cannot select approval or research routes, set sufficiency, alter counters, or increase limits.

### Target full workflow

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

## Persistence architecture

Workflow persistence and long-term research memory are deliberately separate:

- **Workflow checkpoints:** application lifespan configuration selects `memory`, `sqlite`, or `postgres`. Memory is process-local. Official async SQLite is local/test-only and has a verified close/reopen pending-interrupt resume test. Official `AsyncPostgresSaver` is the production architecture, configured with `DEEPTRACE_POSTGRES_URI` and an explicit one-time setup flag. No live PostgreSQL instance was tested.
- **Research memory:** application code depends on `ResearchMemoryRepository`, not cloud APIs. Filesystem memory writes one atomic, bounded schema-v1 JSON file per canonical UUID and proves a new repository/application instance can list and reload prior results. GCS writes the same model to `research-sessions/{uuid}.json` with a create-only generation precondition and Application Default Credentials. Mock tests pass; live GCS is unverified.
- **Terminal policy:** completed and cancelled sessions are saved. Cancellation is a distinct record with no report, citations, sources, or usage. Failed/incomplete runs are not promoted to history. Pending approval remains checkpoint state rather than a research record.

GCS is not a custom LangGraph checkpointer. PostgreSQL/SQLite are not treated as the user-facing history API. This avoids bespoke object-store concurrency logic and keeps the explicit GCS assignment requirement visible.

## Safety controls

- NFKC normalization, malformed-control removal, typed schemas, string/item limits, and named direct-injection rules.
- Multi-signal imperative control bypass is blocked; defensively framed safety research is allowed with annotation rather than keyword censorship.
- Modified plans are bounded and inspected before the interrupted graph receives `Command(resume=...)`.
- Search results accept only canonical HTTP(S) URLs, retain provenance, truncate content, identify instruction-like text, and quarantine it from synthesis. Deep fetching, redirect/DNS/SSRF defenses are not yet applicable because DeepTrace consumes provider snippets only.
- Approval, graph edges, critic decisions, iteration counters, query/result/source limits, and provider timeout are application-owned. Retrieved/model text cannot set them.
- Accepted-evidence-only synthesis and citation closure reject unknown IDs or metadata that differs from retained sources. Incomplete evidence remains explicitly uncertain.
- UUID/path/object-name validation, schema v1, a 1 MB record ceiling, and omission of retrieved bodies prevent persisted content from gaining authority.
- Per-process/IP POST limiting supplies a local abuse bound; a shared authenticated deployment limit remains required.
- `SafetyEvent` and JSON logs contain identifiers, stage, action, rules, and reasons—not inspected payloads, prompts, credentials, headers, or chain-of-thought.

The full applied threat model and limitations are in `docs/THREAT_MODEL.md`.

## Observability events

Implemented events cover request/workflow stages, approval transitions, critic routes, persistence operations, checkpoint selection, provider failures, and `safety_intervention`. Events include IDs, timestamps, duration, counts, decision codes, provider facts, and named safety rules—not raw secrets, evidence bodies, or unnecessary prompts. Cloud export/dashboard/alerting remain future deployment work.

## Evaluation boundary

Phase 7 adds an offline evaluation package, not a runtime application component. A versioned JSON dataset drives deterministic plan/search adapters through the same `ResearchWorkflow`; scorers compare public typed outputs and state facts, then serialize raw case results and aggregate metrics. Safety cases read the canonical Phase 6 artifact. Evaluation code does not alter graph routes, providers, UI behavior, or persistence. Local fixture timings and outcomes are kept distinct from future live-provider and deployed evaluation.

## Phase 8 production boundary

Development remains deterministic by default. Production selects a structured Vertex/Gemini planner, Tavily retrieval, GCS research memory, and the official PostgreSQL LangGraph saver. `DEEPTRACE_ENV=production` validates this entire set before the app is created and disables simulated fallback. Model identity, input/output/total tokens, call count, and latency flow from the planning response into typed usage metadata without logging prompts.

The target host is the distinct preview Cloud Run Instance resource. Hermes owns ingress and the authenticated dashboard; DeepTrace is exposed through Hermes' documented dashboard plugin/backend router mechanism. GCS persists terminal research records, while PostgreSQL persists mutable graph checkpoints. Cloud Logging/Monitoring consume structured events under the `cloud_run_instance` resource. This packaging and all cloud calls remain unverified until tooling, credentials, secrets, and a project are available.
