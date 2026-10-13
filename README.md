# DeepTrace

DeepTrace is a developing production-ready agentic research and source-verification platform for CSCI 599 Assignment 4. A user will eventually submit a research question, review a generated plan, and—only after approving or modifying that plan—allow the system to iteratively retrieve, assess, verify, and synthesize evidence with traceable citations.

This repository has completed **Phase 7: deterministic/local quantitative evaluation**. A versioned 27-case custom benchmark now measures planning/retrieval termination, self-correction, evidence coverage, citation integrity, HITL policy, and safety behavior through a reproducible CLI. The approval, iterative research, durable-memory, and layered-safety features remain intact. Live-provider research-quality evaluation, deployed adversarial testing, deployment, and a production model remain unfinished.

## Problem

One-shot answer generation can hide weak retrieval, unsupported claims, conflicting sources, and prompt-injection risks. DeepTrace is designed to make the research process inspectable and to stop rather than fabricate when evidence remains insufficient.

## Target solution

The minimum planned workflow is:

1. Validate the research question and establish request limits.
2. Generate a structured research plan.
3. Persist the plan and pause at a real approval checkpoint.
4. On approval, retrieve evidence for each sub-question.
5. Score relevance, quality, conflicts, and coverage.
6. Verify candidate claims against cited evidence.
7. Let a critic identify evidence gaps and revise actual search tasks.
8. Repeat within a deterministic iteration budget.
9. Validate citations and output safety, then persist the report and trace.

## Targeted advanced features

- Agentic RAG with iterative retrieval and source verification
- Multi-step planning with execution-changing self-correction
- Human-in-the-loop plan approval, modification, and cancellation
- Cross-session long-term memory backed by durable cloud storage

All four are verified at the deterministic/local level. Long-term memory is specifically **VERIFIED at the local durable-storage level**; production GCS remains **IMPLEMENTED — UNVERIFIED**. Production provider and deployment verification are still outstanding.

## Current architecture and planned extensions

- **Language:** Python 3.11
- **API and UI host:** FastAPI with Jinja2. HTMX/server-sent events remain optional future additions when interactive approval/progress requires them.
- **Orchestration:** LangGraph with typed state and explicit `plan → request approval → interrupt` stages before query generation. `Command(resume=...)` continues the same checkpointed thread into the Phase 3 retrieve/verify/critic/correct graph or routes rejection directly to cancellation.
- **Workflow checkpoints:** `memory` remains the zero-configuration default; `sqlite` is an official local/test backend and has a tested pending-interrupt restart/resume path; `postgres` selects official `AsyncPostgresSaver` for production. PostgreSQL setup and live multi-worker behavior remain unverified without infrastructure.
- **Current model provider:** a deterministic, credential-free development planner whose UI output is explicitly labeled simulated
- **Default production model candidate:** Gemini through Vertex AI, behind the implemented `PlanModel` abstraction
- **Search provider:** a `SearchProvider` interface with deterministic `.test` fixtures by default and a Tavily HTTP adapter when `TAVILY_API_KEY` is configured. The live adapter is not yet smoke-tested.
- **Evidence processing:** provider snippets are normalized to provenance-rich `Source` objects, canonical-URL deduplicated across iterations, capped at 12 retained sources, and treated as untrusted data. No arbitrary source-page fetching occurs yet.
- **Verification:** deterministic lexical relevance, evidence-length/support, plan-item mapping, instruction-like-content quarantine, and limited domain-category signals. These heuristics do not establish truth or comprehensive source quality.
- **Critic and correction:** every plan item needs at least one accepted supportive source. Structured missing, weak, or rejected-evidence gaps generate up to two distinct follow-up queries. The maximum is two total retrieval passes (initial plus one correction) to bound cost and latency.
- **Citations:** every emitted `[S#]` ID is validated against a retained source object before rendering.
- **Research memory:** `ResearchMemoryRepository` separates user-facing history from graph checkpoints. The filesystem adapter atomically stores bounded schema-v1 JSON for local verification. The GCS adapter uses `research-sessions/{uuid}.json`, ADC, create-only generation preconditions, and `DEEPTRACE_GCS_BUCKET`; its mocked contract passes, but no live bucket was used.
- **Write policy:** completed sessions retain the approved plan, report, citations, bounded source metadata, provider/usage facts, and timestamps. Cancelled sessions retain status and plan metadata but no report, citations, sources, or usage. Failed/incomplete workflows are not promoted to research history; pending workflows belong only to the configured checkpointer.
- **Evaluation:** `deeptrace-eval-v1` contains 27 deterministic cases across six capability categories. The CLI saves schema-validated raw JSON and a generated Markdown summary while preserving failures.
- **Observability:** structured JSON events cover workflow decisions, persistence, and redacted safety interventions. `SafetyEvent` records stage/action/rule IDs and identifiers without inspected payloads, prompts, credentials, or report content. Cloud export remains future work.
- **Deployment candidate:** the assignment-specific Google Cloud Run Instances + Hermes Agent path, pending instructor clarification documented in [docs/DEPLOYMENT_COMPLIANCE.md](docs/DEPLOYMENT_COMPLIANCE.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries and state transitions.

## Safety and guardrails

The Phase 6 pipeline is `normalize → inspect input → typed plan → real HITL → bounded retrieval → inspect/quarantine evidence → verify → critic → citation closure → typed output → validated memory`. High-confidence multi-signal control-bypass requests are rejected; defensively framed safety research is allowed with annotation. Modified plans pass the same protected-control inspection before resume. Retrieved instructions are marked, rejected by verification, excluded from synthesis/citations, and unable to alter fixed graph edges, trusted counters, approval state, or permissions.

Resource controls cap questions at 500 characters, plans at eight items, initial/follow-up queries at 3/2, results per query at 3, retained sources at 12, source content at 1,500 characters, retrieval passes at 2, and memory records at 1 MB. Tavily requests have a bounded configurable timeout. A per-process/IP sliding window defaults to 30 POSTs/minute; shared proxy-level rate limiting remains deployment work.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) and [eval/adversarial_results_local.json](eval/adversarial_results_local.json). Local attacks PI-001/002/003 are verified; the same payloads have **not** been run against a deployed system.

## Evaluation

Run the full deterministic evaluation with:

```powershell
.\.venv\Scripts\python.exe -m eval.run_evaluation --overwrite
```

The methodology and actual Phase 7 results are in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). The versioned dataset is [deeptrace_eval_v1.json](eval/datasets/deeptrace_eval_v1.json), with machine-readable and human-readable outputs under `eval/results/`. This local fixture evaluation does not measure live-web answer quality or production performance.

## Development plan

Each phase ends with tests and retained evidence. See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) and [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md).

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

If Tavily is requested without a key, DeepTrace safely falls back to visibly simulated fixtures. Do not paste keys into source files or chat.

## Running locally

```powershell
.\.venv\Scripts\python.exe main.py
```

Open <http://127.0.0.1:8000>. `GET /health` returns the deployment-oriented health response.

The default planner and search provider are simulated and perform no external calls. The UI labels this mode prominently, and those results must not be described as genuine research.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The suite includes 63 tests. It preserves all Phase 1–6 coverage and tests evaluation dataset validation, metric calculations, zero denominators, expected/actual scoring, failure visibility, serialization/no-silent-overwrite behavior, and derived safety metrics. Reproduce the local adversarial artifact with `python -m adversarial_tests.run_local`.

## Deployment

Not deployed. There is no live URL. Ordinary Cloud Run is not being treated as equivalent to the rubric's “Cloud Run Instances with OpenClaw or Hermes Agent and monitoring.”

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
- Local adversarial success does not satisfy the required deployed-system attack evidence.
- Phase 7 evaluates deterministic workflow behavior only. Live-provider relevance, truthfulness, production latency, and deployed reliability remain unevaluated.
- The exact required relationship between DeepTrace and Hermes/OpenClaw needs instructor confirmation.
- GitHub CLI, Docker, and Google Cloud CLI were not detected locally during Phase 0.

## Repository structure

```text
.
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT_COMPLIANCE.md
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
└── main.py
```
