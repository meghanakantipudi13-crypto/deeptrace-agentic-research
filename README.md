# DeepTrace

DeepTrace is an original agentic research and source-verification application for the CSCI 599 capstone. It is not an extension of the Assignment 3 personal assistant. A user submits a research question, reviews or modifies a generated plan, and explicitly approves it before retrieval begins. The system then retrieves evidence, verifies it, critiques coverage, revises searches when necessary, and produces a citation-checked result.

The repository includes a reproducible local deployment, a 27-case quantitative benchmark, three recorded prompt-injection attacks, and one controlled live Vertex AI planning verification. Tavily, GCS, PostgreSQL, and cloud deployment are not live-verified and are not required for the submission demonstration.

## Problem

One-shot answer generation can hide weak retrieval, unsupported claims, conflicting sources, and prompt-injection risks. DeepTrace is designed to make the research process inspectable and to stop rather than fabricate when evidence remains insufficient.

## Implemented workflow

The workflow is:

1. Validate the research question and establish request limits.
2. Generate a structured research plan.
3. Persist the plan and pause at a real approval checkpoint.
4. On approval, retrieve evidence for each sub-question.
5. Score relevance, quality, conflicts, and coverage.
6. Verify candidate claims against cited evidence.
7. Let a critic identify evidence gaps and revise actual search tasks.
8. Repeat within a deterministic iteration budget.
9. Validate citations and output safety, then persist the report and trace.

## Demonstrated advanced features

- Agentic RAG with iterative retrieval and source verification
- Multi-step planning with execution-changing self-correction
- Human-in-the-loop plan approval, modification, and cancellation
- Cross-session memory backed by bounded local durable storage

All four are verified in the deterministic local deployment. The memory claim is local cross-session persistence, not distributed/cloud memory.

## Capability-to-Code Map

| Category | Claimed Feature / Guardrail / Eval | Source File(s) & Line Numbers | Key Class / Function | Notes / Scope |
|---|---|---|---|---|
| Advanced feature | Cross-session long-term memory | `app/memory/filesystem.py` L22–93; `app/memory/service.py` L11–64; `tests/test_memory.py` L80–184 | `FileSystemResearchMemory`, `record_from_outcome` | Bounded local records survive a process restart; not distributed cloud memory. |
| Advanced feature | Multi-step planning and self-correction | `app/research_workflow.py` L166–188, L467–625; `tests/test_research_workflow.py` L144–207 | `_create_plan`, `_critic`, `_revise_queries` | Critic output changes actual follow-up queries; maximum two retrieval passes. |
| Advanced feature | Human-in-the-loop approval | `app/research_workflow.py` L190–315, L645–815; `tests/test_hitl_workflow.py` L76–210 | `interrupt`, `Command(resume=...)`, `start`, `resume` | Real pause occurs before query generation; modify/cancel/duplicate/invalid paths are tested. |
| Advanced feature | Agentic RAG and source verification | `app/research_workflow.py` L317–625; `tests/test_demo_provider.py` L11–53 | `_generate_queries`, `_retrieve_sources`, `_verify_evidence`, `_synthesize` | Iterative retrieval, verification, quarantine, and citation closure run after approval. |
| Guardrail | Trust-boundary enforcement | `app/safety.py` L103–237; `tests/test_safety.py` L30–153 | `inspect_user_text`, `inspect_retrieved_content`, `enforce_user_text`, `SlidingWindowRateLimiter` | Blocks control-bypass input, validates plan edits, quarantines retrieved instructions, and bounds requests. |
| Evaluation | Three real prompt-injection attacks | `adversarial_tests/attacks.json`; `adversarial_tests/run_local.py` L94–265; `eval/adversarial_results_local.json` | `_run_direct`, `_run_retrieval`, `run_attacks` | Exact injection points, workflow traces, results, and mitigations are preserved. |
| Evaluation | Quantitative custom harness | `eval/run_evaluation.py` L122–730; `eval/datasets/deeptrace_eval_v1.json`; `eval/results/deeptrace_eval_v1_local.json` | `load_dataset`, `calculate_metrics`, `evaluate` | 27 deterministic cases across six categories with schema-validated raw results. |
| Deployment | Reproducible local service and persistence | `scripts/run_demo.ps1`; `app/checkpointing.py` L17–57; `docs/LOCAL_DEPLOYMENT.md` | `open_checkpointer`, FastAPI application | Local alternative topology; no public endpoint or recurring cloud resource is required. |

## Current architecture and planned extensions

- **Language:** Python 3.11
- **API and UI host:** FastAPI with Jinja2. HTMX/server-sent events remain optional future additions when interactive approval/progress requires them.
- **Orchestration:** LangGraph with typed state and explicit `plan → request approval → interrupt` stages before query generation. `Command(resume=...)` continues the same checkpointed thread into the Phase 3 retrieve/verify/critic/correct graph or routes rejection directly to cancellation.
- **Workflow checkpoints:** `memory` remains the zero-configuration default; `sqlite` is an official local/test backend and has a tested pending-interrupt restart/resume path; `postgres` selects official `AsyncPostgresSaver` for production. PostgreSQL setup and live multi-worker behavior remain unverified without infrastructure.
- **Current development model provider:** a deterministic, credential-free planner whose UI output is explicitly labeled simulated
- **Production model provider:** structured Gemini planning through Vertex AI and `google-genai`, behind `PlanModel`; mocked tests and one controlled live structured-planning call pass
- **Search provider:** a `SearchProvider` interface with deterministic `.test` fixtures by default and a Tavily HTTP adapter when `TAVILY_API_KEY` is configured. The live adapter is not yet smoke-tested.
- **Evidence processing:** provider snippets are normalized to provenance-rich `Source` objects, canonical-URL deduplicated across iterations, capped at 12 retained sources, and treated as untrusted data. No arbitrary source-page fetching occurs yet.
- **Verification:** deterministic lexical relevance, evidence-length/support, plan-item mapping, instruction-like-content quarantine, and limited domain-category signals. These heuristics do not establish truth or comprehensive source quality.
- **Critic and correction:** every plan item needs at least one accepted supportive source. Structured missing, weak, or rejected-evidence gaps generate up to two distinct follow-up queries. The maximum is two total retrieval passes (initial plus one correction) to bound cost and latency.
- **Citations:** every emitted `[S#]` ID is validated against a retained source object before rendering.
- **Research memory:** `ResearchMemoryRepository` separates user-facing history from graph checkpoints. The filesystem adapter atomically stores bounded schema-v1 JSON for local verification. The GCS adapter uses `research-sessions/{uuid}.json`, ADC, create-only generation preconditions, and `DEEPTRACE_GCS_BUCKET`; its mocked contract passes, but no live bucket was used.
- **Write policy:** completed sessions retain the approved plan, report, citations, bounded source metadata, provider/usage facts, and timestamps. Cancelled sessions retain status and plan metadata but no report, citations, sources, or usage. Failed/incomplete workflows are not promoted to research history; pending workflows belong only to the configured checkpointer.
- **Evaluation:** `deeptrace-eval-v1` contains 27 deterministic cases across six capability categories. The CLI saves schema-validated raw JSON and a generated Markdown summary while preserving failures.
- **Observability:** structured JSON events cover workflow decisions, persistence, and redacted safety interventions. `SafetyEvent` records stage/action/rule IDs and identifiers without inspected payloads, prompts, credentials, or report content. Cloud export remains future work.
- **Submission deployment:** a reproducible local FastAPI service with filesystem research history and SQLite graph checkpoints; see [docs/LOCAL_DEPLOYMENT.md](docs/LOCAL_DEPLOYMENT.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries and state transitions.

## Safety and guardrails

The Phase 6 pipeline is `normalize → inspect input → typed plan → real HITL → bounded retrieval → inspect/quarantine evidence → verify → critic → citation closure → typed output → validated memory`. High-confidence multi-signal control-bypass requests are rejected; defensively framed safety research is allowed with annotation. Modified plans pass the same protected-control inspection before resume. Retrieved instructions are marked, rejected by verification, excluded from synthesis/citations, and unable to alter fixed graph edges, trusted counters, approval state, or permissions.

Resource controls cap questions at 500 characters, plans at eight items, initial/follow-up queries at 3/2, results per query at 3, retained sources at 12, source content at 1,500 characters, retrieval passes at 2, and memory records at 1 MB. Tavily requests have a bounded configurable timeout. A per-process/IP sliding window defaults to 30 POSTs/minute; shared proxy-level rate limiting remains deployment work.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) and [eval/adversarial_results_local.json](eval/adversarial_results_local.json). Local attacks PI-001/002/003 exercise the actual operating workflow and preserve exact traces and mitigations.

## Evaluation

Run the full deterministic evaluation with:

```powershell
.\.venv\Scripts\python.exe -m eval.run_evaluation --overwrite
```

The methodology and actual Phase 7 results are in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). The versioned dataset is [deeptrace_eval_v1.json](eval/datasets/deeptrace_eval_v1.json), with machine-readable and human-readable outputs under `eval/results/`. This local fixture evaluation does not measure live-web answer quality or production performance.

## Development plan

Each phase ends with tests and retained evidence. See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) and [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md).

Submission materials include the quantitative [evaluation report](EVALUATION_REPORT.md), the individual [process log](PROCESS_LOG.md), the [demo script](docs/DEMO_SCRIPT.md), the [13-slide presentation authoring script](docs/PRESENTATION_OUTLINE.md), and the [submission checklist](SUBMISSION_CHECKLIST.md). The editable deck and recorded MP4 remain user-facing deliverables.

## Local setup

Python 3.11 is required. Runtime and test dependencies are pinned in `pyproject.toml`.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Environment variables

Copy `.env.example` to a local `.env` only after implementation begins. Never commit `.env` or credentials. Production secrets must come from Google Secret Manager or another instructor-approved secret store.

- `SEARCH_PROVIDER=deterministic` uses simulated `.test` fixtures.
- `SEARCH_PROVIDER=tavily` plus `TAVILY_API_KEY` enables the real Tavily adapter.
- `DEEPTRACE_MEMORY_BACKEND=filesystem` uses `DEEPTRACE_MEMORY_DIR` (default `.deeptrace-memory`) locally; `gcs` requires `DEEPTRACE_GCS_BUCKET` and Application Default Credentials.
- `DEEPTRACE_CHECKPOINT_BACKEND=memory|sqlite|postgres` chooses graph state storage. SQLite is local/test-only. PostgreSQL requires `DEEPTRACE_POSTGRES_URI`; run `DEEPTRACE_POSTGRES_SETUP=true` only for controlled initial schema setup.
- `DEEPTRACE_RATE_LIMIT_PER_MINUTE` controls the bounded per-process POST allowance (default 30, maximum 300).

In development, Tavily requested without a key falls back to visibly simulated fixtures. In production, incomplete provider or persistence configuration raises an error and never silently falls back. Do not paste keys into source files or chat.

## Running the submission demo

```powershell
.\scripts\run_demo.ps1
```

Open <http://127.0.0.1:8000>. This development-only configuration performs no external or paid calls and deterministically demonstrates the approval interrupt, a quarantined retrieval instruction, an evidence gap, query revision, a second retrieval pass, cited synthesis, and persistent history. Follow [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) for the 7–8 minute recording.

For the plain deterministic configuration:

```powershell
.\.venv\Scripts\python.exe main.py
```

Open <http://127.0.0.1:8000>. `GET /health` returns the deployment-oriented health response.

The default planner and search provider are simulated and perform no external calls. The UI labels this mode prominently, and those results must not be described as genuine research.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite includes 69 tests. It preserves all prior workflow/evaluation coverage and adds submission-demo regressions that prove visible correction/quarantine and refuse the demo provider in production. Reproduce the local adversarial artifact with `python -m adversarial_tests.run_local`.

## Deployment

The submission deployment is the local FastAPI topology in [docs/LOCAL_DEPLOYMENT.md](docs/LOCAL_DEPLOYMENT.md). It is reproducible and persists across local restarts. The capstone is graded through the recorded system behavior, so no public endpoint is required. Cloud Run, PostgreSQL, GCS, and live Tavily remain optional future production work and are not represented as verified deployment evidence.

## Limitations

- The default mode uses simulated plans and sources. No live Tavily call was made during Phase 6 verification because no credential was configured.
- The preliminary synthesis is extractive and based on search snippets, not full-document analysis.
- Relevance and quality signals are basic deterministic heuristics and cannot establish objective truth.
- Correction is deterministic and limited to two total retrieval passes; conflict detection remains unimplemented beyond an explicit empty/limited signal because snippets do not encode normalized claim stances.
- The default checkpointer is still process-local. Set `sqlite` for local restart testing or `postgres` for the production architecture; the live PostgreSQL path has not been tested.
- The process-local resume lock is only a fast local guard. Checkpoint state remains authoritative, but cross-worker race behavior still needs live PostgreSQL concurrency tests.
- Filesystem memory proves restart semantics on one machine, not Cloud Run durability. GCS is implemented and mock-tested but not connected to a live bucket.
- Phase 6 has no authentication, authorization, CSRF, actor binding, or shared distributed rate-limit subsystem; those controls are required before deployment.
- Injection inspection is lexical and can miss obfuscation or novel phrasing. Fixed graph/state/citation boundaries remain the primary protection.
- The adversarial evidence covers the actual local workflow, not a public multi-user service.
- Phase 7 evaluates deterministic workflow behavior only. Live-provider relevance, truthfulness, production latency, and deployed reliability remain unevaluated.
- Live Vertex evidence covers structured planning only, not full live-web research quality.

## Repository structure

```text
.
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT_COMPLIANCE.md
│   ├── DEMO_SCRIPT.md
│   ├── LOCAL_DEPLOYMENT.md
│   ├── DEVELOPMENT_PLAN.md
│   ├── RISK_REGISTER.md
│   └── THREAT_MODEL.md
├── adversarial_tests/
│   ├── attacks.json
│   └── run_local.py
├── eval/
│   ├── datasets/deeptrace_eval_v1.json
│   ├── results/deeptrace_eval_v1_local.json
│   ├── results/deeptrace_eval_v1_local.md
│   ├── adversarial_results_local.json
│   ├── models.py
│   └── run_evaluation.py
├── app/
│   ├── providers/
│   ├── memory/
│   ├── search/
│   ├── static/
│   ├── templates/
│   ├── main.py
│   ├── models.py
│   ├── research.py
│   ├── research_workflow.py
│   ├── safety.py
│   ├── validation.py
│   └── workflow.py
├── tests/
├── .env.example
├── .gitignore
├── DECISIONS.md
├── EVALUATION_REPORT.md
├── PROCESS_LOG.md
├── pyproject.toml
├── README.md
├── RUBRIC_COMPLIANCE.md
├── SUBMISSION_CHECKLIST.md
├── scripts/run_demo.ps1
└── main.py
```
