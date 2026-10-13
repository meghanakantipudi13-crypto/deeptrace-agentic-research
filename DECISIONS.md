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

- **Status:** Accepted; Phase 4 interrupt/resume plus conditional correction graph implemented with local-only checkpointing
- **Context:** Planning, pausing, correction, and resumption must affect execution and be testable.
- **Options considered:** Hand-written state machine; generic agent loop; LangGraph.
- **Decision:** LangGraph with typed state, explicit nodes/routes, persisted stage transitions, and deterministic iteration limits.
- **Rationale:** Graph edges make approval and correction paths observable. LangGraph interrupts/checkpointing are designed for resumable HITL, but durable storage must be configured rather than using in-memory savers.
- **Rubric impact:** Directly supports planning/self-correction, HITL, and trace evidence.
- **Tradeoffs:** Framework semantics and version pinning require targeted tests; graph nodes do not imply A2A multi-agent compliance.

## ADR-004 — Use provider adapters; select Tavily for production search

- **Status:** Tavily adapter implemented — live behavior unverified; model provider still proposed
- **Context:** The system needs structured generation and web retrieval while keeping costs measurable and deployment credentials manageable.
- **Options considered:** Direct OpenAI API; Vertex AI Gemini; local model; Google Programmable Search; Tavily.
- **Decision:** Keep Gemini via Vertex AI as the production model candidate. Use Tavily as the initial production search provider behind a `SearchProvider`, implemented with direct `httpx` calls rather than a provider SDK. Keep deterministic `.test` fixtures as the credential-free default.
- **Rationale:** Tavily returns bounded source-attributed snippets, URLs, relevance scores, and optional usage credits suitable for citation mapping. Direct HTTP avoids another dependency and preserves replaceability. A mocked HTTP contract test exists, but live relevance, reliability, latency, and cost remain unverified until a credentialed smoke test.
- **Rubric impact:** Enables usage accounting and reproducible retrieval while avoiding provider lock-in.
- **Tradeoffs:** Two external services add cost and failure modes; provider terms and current pricing must be captured at evaluation time.

## ADR-005 — Use PostgreSQL checkpoints plus GCS artifacts; do not use Firestore by default

- **Status:** Accepted architecture; not implemented in Phase 1
- **Context:** Cloud Run filesystems are not durable, future HITL must survive restarts, and the assignment explicitly requires a GCS bucket for long-term memory on Cloud Run Instances. LangGraph distinguishes thread checkpoints used for HITL from cross-thread long-term stores.
- **Options considered:** GCS only with generation preconditions; Firestore plus GCS; Cloud SQL PostgreSQL plus GCS; local SQLite.
- **Decision:** Do not add Firestore by default. Use LangGraph's supported PostgreSQL checkpointer for mutable graph/thread state, interrupt/resume checkpoints, approval status, and idempotency. Use GCS for immutable, versioned user-facing research-session records required by the assignment. Phase 5 implements both production adapters/configuration but does not claim live-cloud verification.
- **Rationale:** GCS provides strong object consistency and conditional writes but no atomic multi-object transaction, so using it as a checkpointer would require a bespoke concurrency-sensitive adapter. Firestore provides transactions but still needs custom LangGraph checkpoint integration. PostgreSQL has an official LangGraph saver, making it the lowest-risk path for reliable interrupts despite adding a managed database. GCS remains necessary for the rubric and artifact storage.
- **Rubric impact:** Preserves GCS-backed durable memory while selecting a supported checkpoint path for genuine restart-safe HITL.
- **Tradeoffs:** Two managed storage services remain. Cloud SQL adds cost and operations, and compatibility with the final Cloud Run Instances/Hermes topology must be validated before implementation. If the instructor requires GCS alone, this ADR must be revisited with explicit concurrency tests.

## ADR-006 — Treat every retrieved byte as untrusted data

- **Status:** Foundational content boundary implemented; complete safety phase pending
- **Context:** Direct and indirect prompt injection are mandatory test cases.
- **Options considered:** Prompt-only warning; single injection classifier; layered deterministic and model-assisted controls.
- **Decision:** Keep instructions and retrieved content in distinct typed fields; never concatenate retrieved text into system instructions; normalize and provenance-tag snippets; enforce static graph gates in code; validate URL schemes and citation mappings; annotate obvious instruction-like content and exclude it from synthesis. Later safety work must add full URL/fetch controls, broader detection, budgets, and deployed attacks.
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

- **Status:** Phase 4 approval/interrupt/resume plus iteration/critic/route events implemented; cloud export proposed
- **Context:** Traces must demonstrate workflow transitions without leaking secrets or full sensitive content.
- **Options considered:** Plain logs; LangSmith only; structured event model exported to Cloud Logging/Monitoring.
- **Decision:** Emit redacted JSON events with request/session IDs, stage, attempt, decision codes, latency, token counts, provider calls, and guardrail events. Build a Cloud Monitoring dashboard and at least one failure/latency alert. External tracing remains optional.
- **Rationale:** Produces deployment evidence using the selected cloud while keeping evaluation artifacts portable.
- **Rubric impact:** Supports monitoring, cost analysis, demo visibility, and debugging.
- **Tradeoffs:** Redaction and log-retention policies require tests and configuration.

## ADR-009 — Cap Phase 3 at two retrieval passes

- **Status:** Accepted and deterministically verified
- **Context:** Self-correction must change execution without creating an unbounded latency/cost loop.
- **Options considered:** One pass; two total passes; three or more passes; dynamic model-controlled budget.
- **Decision:** Permit one initial retrieval pass and at most one targeted correction pass. Trusted application state—not retrieved content or model prose—owns the counter and maximum. Stop with `evidence_sufficient`, `max_iterations_reached`, `no_new_queries`, `no_new_evidence`, or `provider_failure`, then synthesize only supported evidence with uncertainty when gaps remain.
- **Rationale:** Two passes are sufficient to prove real correction while placing a small deterministic ceiling on search calls, latency, and exposure to malicious content. Later measured evaluation may justify changing the constant.
- **Rubric impact:** Provides execution-changing self-correction and safe bounded termination evidence.
- **Tradeoffs:** One correction may be insufficient for difficult live research; the current critic uses deterministic coverage heuristics and cannot robustly detect semantic conflicts.

## ADR-010 — Use LangGraph interrupt/Command with InMemorySaver for Phase 4

- **Status:** Accepted and locally verified on LangGraph 1.2.12
- **Context:** The approval gate must pause actual graph execution after planning and before query generation, while Phase 4 explicitly excludes production persistence.
- **Options considered:** Frontend-only flag; return-and-rerun simulation; deprecated node interrupt APIs; current `interrupt()`/`Command(resume=...)` with in-memory, SQLite, or PostgreSQL checkpointing.
- **Decision:** Compile the graph with `InMemorySaver`, invoke it with a UUID `thread_id`, call `interrupt()` inside `approval_checkpoint`, and resume the same thread with a schema-validated `Command(resume=...)`. Route `approve` and `modify` to query generation; route `reject` directly to cancellation. Serialize resume handling with one application-instance lock and reject any thread not actively interrupted.
- **Versioned references:** LangGraph 1.2.12 [`interrupt()`](https://reference.langchain.com/python/langgraph/types/interrupt) and [`InMemorySaver`](https://reference.langchain.com/python/langgraph/checkpoint/memory/InMemorySaver) references reviewed on 2026-10-05.
- **Rationale:** This is the smallest checkpointer supported by the installed version and directly proves LangGraph pause/resume semantics without adding Phase 5 infrastructure. It follows the current official API rather than deprecated `NodeInterrupt` patterns.
- **Rubric impact:** Verifies local HITL semantics, plan modification affecting execution, zero retrieval before approval, and safe rejection/duplicate handling.
- **Tradeoffs:** Checkpoints disappear on restart, are unavailable to other processes, and do not provide transactional multi-worker idempotency. Phase 5 must replace this with the selected PostgreSQL checkpointer and add restart/concurrency evidence; GCS remains required for durable artifacts and long-term memory.

## ADR-011 — Separate graph checkpoints from versioned research memory

- **Status:** Accepted and implemented in Phase 5; production backends unverified
- **Context:** A LangGraph checkpoint is mutable execution state for one thread, while a user-facing research record is a bounded terminal artifact intended for later browsing. The assignment additionally requires GCS-backed long-term memory on Cloud Run Instances.
- **Options considered:** GCS as a custom LangGraph checkpointer; PostgreSQL alone for both concerns; Firestore plus GCS; official PostgreSQL checkpoints plus GCS research records; local-only SQLite/filesystem.
- **Decision:** Keep two interfaces. `open_checkpointer()` selects `InMemorySaver` for zero-configuration tests, official `AsyncSqliteSaver` for local restart verification, or official `AsyncPostgresSaver` for production. `ResearchMemoryRepository` independently selects atomic filesystem JSON locally or GCS schema-v1 JSON in production. GCS object names are derived only from canonical UUIDs and uploads use `if_generation_match=0` to reject accidental overwrite. Production authentication uses Google Application Default Credentials. PostgreSQL schema setup is an explicit controlled flag.
- **Versioned references:** LangGraph 1.2.12 core, `langgraph-checkpoint-sqlite` 3.1.1, `langgraph-checkpoint-postgres` 3.1.2, and `google-cloud-storage` 3.16.0; official references reviewed 2026-10-05.
- **Rationale:** PostgreSQL is the officially supported async production saver and supplies checkpoint semantics that object storage should not reimplement. GCS directly satisfies the Cloud Run Instances memory constraint without coupling application services to its SDK. SQLite and filesystem providers make restart behavior testable without cloud credentials while remaining clearly non-production.
- **Memory policy:** Completed runs retain question, approved plan, plan-modified flag, provider mode, report, citations, bounded source metadata, usage, timestamps, and termination. Cancelled runs retain explicit cancellation and plan metadata but no report/evidence. Failed and incomplete workflows are not research-history records; pending workflows live only in the checkpointer.
- **Safety/privacy:** Schema version 1 forbids unknown fields, canonical UUIDs prevent path/object-name injection, records are capped at 1 MB, filesystem writes are atomic, corrupt records fail closed, and prompts, retrieved body text, secrets, headers, and credentials are excluded.
- **Verification:** Local filesystem recreation, new-application history reload, and SQLite pending-interrupt recovery pass. GCS behavior is mock-tested. Live GCS, PostgreSQL setup/recovery, and cross-worker resume races remain unverified.
- **Tradeoffs:** Production still uses two services. Create-only GCS writes make duplicate persistence fail visibly instead of silently replacing history. PostgreSQL correctness under the final Cloud Run/Hermes topology and transactional double-resume behavior require deployment-phase integration tests.

## ADR-012 — Use layered deterministic safety with scored input policy and evidence quarantine

- **Status:** Accepted and locally verified in Phase 6
- **Context:** DeepTrace accepts user text, human plan edits, external snippets, durable records, and workflow identifiers. A single model prompt cannot protect approval, routing, budgets, citations, or persistence, and the final rubric requires three deployed prompt-injection attempts.
- **Options considered:** Prompt-only instruction; reject on any security keyword; LLM classifier as sole gate; deterministic named rules plus structural graph/schema/citation controls; large external security gateway.
- **Decision:** Use a layered pipeline. Normalize and bound text; reject high-confidence imperative/multi-signal protected-control attacks; annotate defensively framed or ambiguous content; validate plan edits before resume; quarantine any instruction-like retrieved source; keep approval, routes, counters, verification, critic, and citation construction in trusted code; persist only typed bounded metadata; emit redacted `SafetyEvent` objects; and add a small per-process/IP POST limit while reserving shared rate limiting for deployment.
- **Prompt/context rule:** Current deterministic synthesis does not call a model with external content. Any future model context must use the explicit untrusted-evidence envelope and policy preamble in `format_untrusted_evidence()`; prompt separation supplements rather than replaces deterministic enforcement.
- **Rationale:** Named rules make local attacks reproducible and demonstrable, while fixed graph/state/schema controls protect critical invariants when lexical detection misses a novel attack. Defensive framing avoids rejecting every occurrence of words such as “ignore” or “system.”
- **Evidence:** PI-001 direct injection blocked before workflow/search; PI-002 indirect source quarantined and excluded while critic correction continued; PI-003 could not approve, change max iterations, skip critic, or create S999. One benign quoted-injection research question was accepted with annotation. Results are serialized in `eval/adversarial_results_local.json`.
- **Limitations:** Lexical rules have unmeasured false-negative/false-positive rates; one benign control is not a benchmark. Application rate limiting is process-local. Authentication, CSRF, actor authorization, distributed limits, live-provider behavior, and attacks against the deployed URL remain unverified/not started.

## ADR-013 — Use a versioned capability-matched deterministic evaluation harness

- **Status:** Accepted and locally verified in Phase 7
- **Context:** Generic language benchmarks do not directly measure DeepTrace's graph termination, evidence-gap correction, citation closure, HITL boundary, and application-owned safety invariants.
- **Decision:** Use a strict JSON dataset with 27 cases across six categories and a CLI that runs the real local workflow, compares typed expected/actual state, derives Phase 6 safety counts from its canonical artifact, aggregates metrics, retains failures, and writes raw JSON plus Markdown. Refuse silent artifact overwrites unless `--overwrite` is explicit.
- **Scoring:** Prefer deterministic state and provenance assertions. Evidence coverage includes designed persistent gaps in the denominator. Latency uses instrumented in-process workflow time and is labeled non-production. Zero-denominator metrics return unavailable rather than an invented value.
- **Rationale:** The harness is reproducible, auditable, inexpensive, and matched to capabilities already implemented without adding product behavior.
- **Evidence:** `deeptrace-eval-v1` executed all 27 cases: 27 passed expected behavior, 23/23 termination matches, 5/5 correction successes, 37/41 supported plan items, 39/39 valid citations, 0 unsupported citations, 5/5 HITL cases, 3/3 locally defended attacks, 4/4 bounded insufficiency cases, and 0 unexpected errors.
- **Limitations:** Synthetic snippets cannot establish factual correctness, semantic relevance, live-provider behavior, production latency/cost, deployment reliability, or broad adversarial robustness. A later live/deployed evaluation must remain separate and versioned.
