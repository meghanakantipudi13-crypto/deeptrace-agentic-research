# Process Log

The final submission requires a factual 200–300 word narrative per team member. Until implementation is complete, this file keeps chronological notes and does not pretend to be the final narrative.

## Development notes

### 2026-10-04 — Phase 0 initialization

- Read the Assignment 4 master instructions and treated the rubric as the source of truth.
- Inspected an empty project directory. It was not a Git repository.
- Detected Git 2.52.0 and Node.js 24.18.0. A Python 3.11 launcher entry exists, but invoking that interpreter was denied in the current sandbox and must be rechecked in Phase 1. GitHub CLI, Docker, and Google Cloud CLI were not detected.
- Confirmed global Git author name and email are configured without recording their values.
- Drafted the compliance tracker, decision log, evaluation scaffold, architecture, deployment ambiguity analysis, risk register, and phased development plan.
- Chose no final model/search/deployment implementation. Recommended provider adapters and recorded the Cloud Run Instances/Hermes integration question as a blocker that needs instructor clarification.
- Initialized local Git and prepared the truthful documentation-only initial milestone. No application code, feature verification, evaluation result, deployment, live URL, or GitHub remote was claimed.

### 2026-10-04 — Phase 1 planning workflow foundation

- Reconfirmed `main` was clean and synchronized with `origin/main` at the Phase 0 commit.
- Diagnosed Python execution: Python 3.11.4 was correctly installed; only the managed sandbox blocked the user-profile interpreter, so project Python commands used scoped runtime approval.
- Revisited persistence. Selected a future official LangGraph PostgreSQL checkpointer for mutable HITL state plus GCS for rubric-required durable artifacts/memory, replacing the proposed Firestore default. No persistence was implemented in Phase 1.
- Added a pinned Python project, FastAPI/Jinja interface, deterministic `PlanModel` implementation, foundational input validation, structured JSON logging, `/health`, and a real three-node LangGraph workflow that intentionally stops after planning.
- Added eight automated tests. All passed on Python 3.11.4 with pytest 9.1.1.
- Started the local server on port 8765 and verified `/health`, the home page, and a form submission over HTTP. The returned page displayed a structured plan, a simulated-output warning, and an explicit statement that no retrieval or verification occurred.
- No advanced feature, safety subsystem, persistence, evaluation result, deployment, or live URL was claimed complete.

### 2026-10-04 — Phase 2 retrieval and verification foundation

- Reconfirmed the clean Phase 1 commit and ran its eight tests before modification; all passed.
- Selected Tavily behind a provider-neutral interface and implemented it through direct HTTP to avoid an unnecessary SDK. Added deterministic `.test` fixtures for development. No Tavily credential was present, so no live search result was claimed.
- Added a seven-node LangGraph path: plan, derive up to three queries, make one bounded retrieval pass, normalize/deduplicate up to eight sources, verify evidence, synthesize an extractive preliminary result, and finish.
- Added typed source, verification, citation, preliminary-result, and usage models. Search calls, result counts, deduplication, retained sources, optional provider credits, per-node latency, and overall latency are recorded without fabricated costs.
- Added a structural safety boundary for untrusted snippets. Instruction-like content is annotated, reaches the verifier, cannot alter static graph routing, and is excluded from synthesis. This was component testing, not a final adversarial attack.
- Expanded the UI to show plan, queries, sources, verification, citations, provider mode, metrics, workflow events, and the explicit single-pass boundary.
- Expanded the suite from eight to 18 tests. A local deterministic smoke test returned HTTP 200 for health, home, and research submission and visibly labeled simulated mode.

### 2026-10-04 — Phase 3 bounded iterative self-correction

- Reconfirmed the clean Phase 2 commit and all 18 baseline tests before modification.
- Added a structured evidence-sufficiency critic that requires supportive coverage for every plan item and records missing, weak, or rejected evidence, confidence, unsupported plan items, recommendations, and the current conflict-detection limitation.
- Added conditional LangGraph routes from critic to synthesis or query revision, then from revision through the same retrieval and verification nodes. Evidence, provenance, citations, queries, usage, and iteration traces accumulate rather than being replaced.
- Set a trusted maximum of two total retrieval passes. The graph records evidence-sufficient, maximum-iterations, no-new-query, no-new-evidence, and provider-failure termination conditions and synthesizes uncertainty when gaps remain.
- Added deterministic Scenarios A, B, and C. They prove immediate sufficiency, a malicious/insufficient first pass followed by targeted successful retrieval, and safe budget exhaustion. The complete suite passed 21 tests. Local HTTP smoke checks returned 200 for health, home, and research and rendered the Phase 3 trace and termination state.
- Updated the UI to expose iteration counts, query causes, new/accepted sources, critic decisions, selected route, and termination reason without displaying hidden reasoning.

### 2026-10-05 — Phase 4 human-in-the-loop approval

- Reconfirmed the clean Phase 3 commit and all 21 baseline tests. Reviewed the installed LangGraph 1.2.12 APIs and current official interrupt, command-resume, thread, and in-memory checkpointer documentation.
- Compiled the research graph with `InMemorySaver`, inserted request/interrupt nodes after planning, and used a UUID `thread_id` to resume the exact checkpoint with `Command(resume=...)`. Query generation and every search-related node remain downstream of the approval router.
- Added schema-validated approve, modify, and reject decisions. Human modifications replace the plan steps used by query generation. Rejection routes directly to a terminal cancelled state with zero search calls and no synthetic result.
- Added one-instance resume serialization and checkpoint-state validation to reject unknown, completed, cancelled, malformed, or duplicate approvals. Documented that this is not transactional multi-worker idempotency or durable memory.
- Added six checkpoint-level HITL scenarios and approval UI tests while preserving the approved Phase 3 self-correction scenarios. The suite passed 30 tests. Local HTTP smoke checks showed an interrupted page with zero search calls, successful same-workflow approval followed by a result, and cancellation with zero search calls and no result.

### 2026-10-05 — Phase 5 durable cross-session research memory

- Reconfirmed `main`, clean synchronization at `824dc94`, and all 30 baseline tests. Re-evaluated official LangGraph checkpoint choices and kept PostgreSQL plus GCS because graph checkpoints and user-facing memory have different consistency and access requirements.
- Added a typed `ResearchMemoryRepository`, schema-v1 terminal records, atomic filesystem storage, and a GCS provider using canonical UUID object names, Application Default Credentials, a 1 MB cap, and create-only generation preconditions. Completed runs retain bounded useful output; cancelled runs retain no fabricated report; failed/incomplete runs are not promoted to history.
- Added `/history` list/detail pages and automatic terminal-session saves. Structured events cover memory saves, loads, lists, failures, and checkpoint backend selection without logging report content.
- Added configurable in-memory, official async SQLite, and official async PostgreSQL checkpoint lifecycles. SQLite proved that a pending real interrupt survives saver/workflow recreation and resumes the same UUID. PostgreSQL and live GCS remain implemented but unverified because no infrastructure was configured.
- Added long-term-memory Scenarios A–G, mocked GCS adapter tests, history UI tests, and restart-safe HITL coverage while preserving all prior workflow tests. The suite reached 46 passing tests before final verification.

## Final per-member narrative

Not yet written. Replace this section near submission time with 200–300 factual words per team member based on the notes above and subsequent dated entries.
