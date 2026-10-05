# Architecture Decision Log

Statuses distinguish accepted architecture from later implementation. An accepted decision is not proof that every capability it describes is implemented.

## ADR-001 — Keep the application core independent of deployment runtime

- **Status:** Accepted; deployment adapter remains unresolved
- **Context:** The rubric names Cloud Run Instances with OpenClaw or Hermes Agent, but the exact integration boundary is not stated.
- **Options considered:** Build directly into Hermes; build an independent ordinary Cloud Run app; define a portable core plus deployment adapter.
- **Decision:** Use a framework-neutral domain core and provider interfaces, with a thin Hermes/OpenClaw deployment adapter added after instructor clarification.
- **Rationale:** Prevents an ambiguous deployment requirement from contaminating workflow logic while preserving a compliant integration path.
- **Rubric impact:** Reduces deployment risk without claiming compliance early.
- **Tradeoffs:** Adds one adapter boundary and may require a small integration spike.

## ADR-002 — Use Python 3.11, FastAPI, and a minimal server-rendered UI

- **Status:** Accepted; FastAPI/Jinja implemented in Phase 1
- **Context:** The grader must clearly see state transitions; a separate frontend would add deployment and synchronization work.
- **Options considered:** Streamlit; FastAPI plus React; FastAPI plus Jinja2/HTMX/SSE.
- **Decision:** FastAPI with Jinja2 now; add HTMX and server-sent events only when later interactive approval/progress behavior needs them.
- **Rationale:** One container can provide typed APIs, real approval actions, event streaming, and a clean demo UI without a second build/deploy pipeline.
- **Rubric impact:** Supports visible HITL, workflow observability, and a reliable demo.
- **Tradeoffs:** Less visual flexibility than a full SPA; SSE reconnection and accessibility still require tests.

## ADR-003 — Use LangGraph for explicit bounded orchestration

- **Status:** Accepted; Phase 1 graph implemented without persistence
- **Context:** Planning, pausing, correction, and resumption must affect execution and be testable.
- **Options considered:** Hand-written state machine; generic agent loop; LangGraph.
- **Decision:** LangGraph with typed state, explicit nodes/routes, persisted stage transitions, and deterministic iteration limits.
- **Rationale:** Graph edges make approval and correction paths observable. LangGraph interrupts/checkpointing are designed for resumable HITL, but durable storage must be configured rather than using in-memory savers.
- **Rubric impact:** Directly supports planning/self-correction, HITL, and trace evidence.
- **Tradeoffs:** Framework semantics and version pinning require targeted tests; graph nodes do not imply A2A multi-agent compliance.

## ADR-004 — Use provider adapters; prefer Vertex AI and evaluate Tavily

- **Status:** Provider seam implemented; production providers still proposed
- **Context:** The system needs structured generation and web retrieval while keeping costs measurable and deployment credentials manageable.
- **Options considered:** Direct OpenAI API; Vertex AI Gemini; local model; Google Programmable Search; Tavily.
- **Decision:** Default model candidate is Gemini via Vertex AI. Search candidate is Tavily behind a `SearchProvider`; run an early reliability/cost spike before locking it.
- **Rationale:** Vertex AI aligns credentials and monitoring with Google deployment. Tavily offers source-oriented search with low integration complexity, but must earn selection through measured citation/source quality.
- **Rubric impact:** Enables usage accounting and reproducible retrieval while avoiding provider lock-in.
- **Tradeoffs:** Two external services add cost and failure modes; provider terms and current pricing must be captured at evaluation time.

## ADR-005 — Use PostgreSQL checkpoints plus GCS artifacts; do not use Firestore by default

- **Status:** Accepted architecture; not implemented in Phase 1
- **Context:** Cloud Run filesystems are not durable, future HITL must survive restarts, and the assignment explicitly requires a GCS bucket for long-term memory on Cloud Run Instances. LangGraph distinguishes thread checkpoints used for HITL from cross-thread long-term stores.
- **Options considered:** GCS only with generation preconditions; Firestore plus GCS; Cloud SQL PostgreSQL plus GCS; local SQLite.
- **Decision:** Do not add Firestore by default. In the persistence phase, use LangGraph's supported PostgreSQL checkpointer for mutable graph/thread state, interrupt/resume checkpoints, approval status, and idempotency. Use GCS for immutable or versioned evidence snapshots, reports, redacted traces, evaluation artifacts, and cross-session memory exports required by the assignment. Implement neither store in Phase 1.
- **Rationale:** GCS provides strong object consistency and conditional writes but no atomic multi-object transaction, so using it as a checkpointer would require a bespoke concurrency-sensitive adapter. Firestore provides transactions but still needs custom LangGraph checkpoint integration. PostgreSQL has an official LangGraph saver, making it the lowest-risk path for reliable interrupts despite adding a managed database. GCS remains necessary for the rubric and artifact storage.
- **Rubric impact:** Preserves GCS-backed durable memory while selecting a supported checkpoint path for genuine restart-safe HITL.
- **Tradeoffs:** Two managed storage services remain. Cloud SQL adds cost and operations, and compatibility with the final Cloud Run Instances/Hermes topology must be validated before implementation. If the instructor requires GCS alone, this ADR must be revisited with explicit concurrency tests.

## ADR-006 — Treat every retrieved byte as untrusted data

- **Status:** Proposed for later safety phase
- **Context:** Direct and indirect prompt injection are mandatory test cases.
- **Options considered:** Prompt-only warning; single injection classifier; layered deterministic and model-assisted controls.
- **Decision:** Keep instructions and retrieved content in distinct typed fields; never concatenate retrieved text into system instructions; sanitize and delimit content; enforce graph gates in code; validate URLs, schemas, citations, budgets, and transitions deterministically; use an injection detector only as an additional signal.
- **Rationale:** A model cannot authorize bypassing code-enforced workflow policy.
- **Rubric impact:** Creates defensible controls for all three required attacks.
- **Tradeoffs:** False positives and false negatives remain and must be measured.

## ADR-007 — Use a capability-matched custom evaluation harness

- **Status:** Proposed for later evaluation phase
- **Context:** General computer-use benchmarks do not directly measure DeepTrace's research and verification behavior.
- **Options considered:** OSWorld/WebArena only; hosted trace metrics only; custom deterministic/LLM-judge hybrid harness.
- **Decision:** Use versioned cases with deterministic checks wherever possible and blinded rubric-based judging only for semantic quality; retain raw inputs, outputs, traces, and scorer versions.
- **Rationale:** Metrics can directly measure evidence coverage, citation correctness, loop behavior, safety, latency, and cost.
- **Rubric impact:** Supports quantitative evaluation and honest failure analysis.
- **Tradeoffs:** Human review or calibrated judging is required for ambiguous claims.

## ADR-008 — Use cloud-native structured observability

- **Status:** Structured local events implemented; cloud export proposed
- **Context:** Traces must demonstrate workflow transitions without leaking secrets or full sensitive content.
- **Options considered:** Plain logs; LangSmith only; structured event model exported to Cloud Logging/Monitoring.
- **Decision:** Emit redacted JSON events with request/session IDs, stage, attempt, decision codes, latency, token counts, provider calls, and guardrail events. Build a Cloud Monitoring dashboard and at least one failure/latency alert. External tracing remains optional.
- **Rationale:** Produces deployment evidence using the selected cloud while keeping evaluation artifacts portable.
- **Rubric impact:** Supports monitoring, cost analysis, demo visibility, and debugging.
- **Tradeoffs:** Redaction and log-retention policies require tests and configuration.
