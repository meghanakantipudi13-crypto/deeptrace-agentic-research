# Architecture Decision Log

Decisions marked **Proposed** are not locked until the Phase 0 review is approved.

## ADR-001 — Keep the application core independent of deployment runtime

- **Status:** Proposed
- **Context:** The rubric names Cloud Run Instances with OpenClaw or Hermes Agent, but the exact integration boundary is not stated.
- **Options considered:** Build directly into Hermes; build an independent ordinary Cloud Run app; define a portable core plus deployment adapter.
- **Decision:** Use a framework-neutral domain core and provider interfaces, with a thin Hermes/OpenClaw deployment adapter added after instructor clarification.
- **Rationale:** Prevents an ambiguous deployment requirement from contaminating workflow logic while preserving a compliant integration path.
- **Rubric impact:** Reduces deployment risk without claiming compliance early.
- **Tradeoffs:** Adds one adapter boundary and may require a small integration spike.

## ADR-002 — Use Python 3.11, FastAPI, and a minimal server-rendered UI

- **Status:** Proposed
- **Context:** The grader must clearly see state transitions; a separate frontend would add deployment and synchronization work.
- **Options considered:** Streamlit; FastAPI plus React; FastAPI plus Jinja2/HTMX/SSE.
- **Decision:** FastAPI with Jinja2/HTMX and server-sent events.
- **Rationale:** One container can provide typed APIs, real approval actions, event streaming, and a clean demo UI without a second build/deploy pipeline.
- **Rubric impact:** Supports visible HITL, workflow observability, and a reliable demo.
- **Tradeoffs:** Less visual flexibility than a full SPA; SSE reconnection and accessibility still require tests.

## ADR-003 — Use LangGraph for explicit bounded orchestration

- **Status:** Proposed
- **Context:** Planning, pausing, correction, and resumption must affect execution and be testable.
- **Options considered:** Hand-written state machine; generic agent loop; LangGraph.
- **Decision:** LangGraph with typed state, explicit nodes/routes, persisted stage transitions, and deterministic iteration limits.
- **Rationale:** Graph edges make approval and correction paths observable. LangGraph interrupts/checkpointing are designed for resumable HITL, but durable storage must be configured rather than using in-memory savers.
- **Rubric impact:** Directly supports planning/self-correction, HITL, and trace evidence.
- **Tradeoffs:** Framework semantics and version pinning require targeted tests; graph nodes do not imply A2A multi-agent compliance.

## ADR-004 — Use provider adapters; prefer Vertex AI and evaluate Tavily

- **Status:** Proposed
- **Context:** The system needs structured generation and web retrieval while keeping costs measurable and deployment credentials manageable.
- **Options considered:** Direct OpenAI API; Vertex AI Gemini; local model; Google Programmable Search; Tavily.
- **Decision:** Default model candidate is Gemini via Vertex AI. Search candidate is Tavily behind a `SearchProvider`; run an early reliability/cost spike before locking it.
- **Rationale:** Vertex AI aligns credentials and monitoring with Google deployment. Tavily offers source-oriented search with low integration complexity, but must earn selection through measured citation/source quality.
- **Rubric impact:** Enables usage accounting and reproducible retrieval while avoiding provider lock-in.
- **Tradeoffs:** Two external services add cost and failure modes; provider terms and current pricing must be captured at evaluation time.

## ADR-005 — Separate transactional workflow state from immutable artifacts

- **Status:** Proposed
- **Context:** Cloud Run filesystems are not durable, HITL state must survive restarts, and the assignment explicitly requires a GCS bucket for long-term memory on Cloud Run Instances.
- **Options considered:** Local SQLite; SQLite on GCS FUSE; Cloud SQL; Firestore plus GCS.
- **Decision:** Use Firestore for sessions, approval status, idempotency, and current workflow metadata; use GCS for versioned reports, evidence snapshots, traces, evaluation artifacts, and memory exports. Use local SQLite or filesystem adapters only in development tests.
- **Rationale:** Avoids SQLite locking problems on object storage and satisfies the explicit bucket constraint while preserving transactional gates.
- **Rubric impact:** Supports real restart-safe HITL and long-term memory.
- **Tradeoffs:** Two persistence APIs and emulator/fake adapters are needed. Instructor should confirm Firestore alongside GCS is acceptable.

## ADR-006 — Treat every retrieved byte as untrusted data

- **Status:** Proposed
- **Context:** Direct and indirect prompt injection are mandatory test cases.
- **Options considered:** Prompt-only warning; single injection classifier; layered deterministic and model-assisted controls.
- **Decision:** Keep instructions and retrieved content in distinct typed fields; never concatenate retrieved text into system instructions; sanitize and delimit content; enforce graph gates in code; validate URLs, schemas, citations, budgets, and transitions deterministically; use an injection detector only as an additional signal.
- **Rationale:** A model cannot authorize bypassing code-enforced workflow policy.
- **Rubric impact:** Creates defensible controls for all three required attacks.
- **Tradeoffs:** False positives and false negatives remain and must be measured.

## ADR-007 — Use a capability-matched custom evaluation harness

- **Status:** Proposed
- **Context:** General computer-use benchmarks do not directly measure DeepTrace's research and verification behavior.
- **Options considered:** OSWorld/WebArena only; hosted trace metrics only; custom deterministic/LLM-judge hybrid harness.
- **Decision:** Use versioned cases with deterministic checks wherever possible and blinded rubric-based judging only for semantic quality; retain raw inputs, outputs, traces, and scorer versions.
- **Rationale:** Metrics can directly measure evidence coverage, citation correctness, loop behavior, safety, latency, and cost.
- **Rubric impact:** Supports quantitative evaluation and honest failure analysis.
- **Tradeoffs:** Human review or calibrated judging is required for ambiguous claims.

## ADR-008 — Use cloud-native structured observability

- **Status:** Proposed
- **Context:** Traces must demonstrate workflow transitions without leaking secrets or full sensitive content.
- **Options considered:** Plain logs; LangSmith only; structured event model exported to Cloud Logging/Monitoring.
- **Decision:** Emit redacted JSON events with request/session IDs, stage, attempt, decision codes, latency, token counts, provider calls, and guardrail events. Build a Cloud Monitoring dashboard and at least one failure/latency alert. External tracing remains optional.
- **Rationale:** Produces deployment evidence using the selected cloud while keeping evaluation artifacts portable.
- **Rubric impact:** Supports monitoring, cost analysis, demo visibility, and debugging.
- **Tradeoffs:** Redaction and log-retention policies require tests and configuration.
