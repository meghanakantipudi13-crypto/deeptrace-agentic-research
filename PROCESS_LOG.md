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

## Final per-member narrative

Not yet written. Replace this section near submission time with 200–300 factual words per team member based on the notes above and subsequent dated entries.
