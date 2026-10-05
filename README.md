# DeepTrace

DeepTrace is a developing production-ready agentic research and source-verification platform for CSCI 599 Assignment 4. A user will eventually submit a research question, review a generated plan, and—only after approving or modifying that plan—allow the system to iteratively retrieve, assess, verify, and synthesize evidence with traceable citations.

This repository has completed **Phase 3: bounded iterative retrieval and self-correction**. The runnable application validates a question, plans research, retrieves and verifies evidence, uses a structured critic to detect plan-coverage gaps, conditionally revises queries, and performs at most one additional retrieval pass before citation-safe synthesis. HITL approval, persistent memory, the complete safety subsystem, deployment, and a production model remain unimplemented. Status claims are tracked in [RUBRIC_COMPLIANCE.md](RUBRIC_COMPLIANCE.md).

## Problem

One-shot answer generation can hide weak retrieval, unsupported claims, conflicting sources, and prompt-injection risks. DeepTrace is designed to make the research process inspectable and to stop rather than fabricate when evidence remains insufficient.

## Target solution

The minimum planned workflow is:

1. Validate the research question and establish request limits.
2. Generate a structured research plan.
3. Persist the plan and pause at a real approval checkpoint.
4. On approval, retrieve evidence for each sub-question.
5. score relevance, quality, conflicts, and coverage.
6. Verify candidate claims against cited evidence.
7. Let a critic identify evidence gaps and revise actual search tasks.
8. Repeat within a deterministic iteration budget.
9. Validate citations and output safety, then persist the report and trace.

## Targeted advanced features

- Agentic RAG with iterative retrieval and source verification
- Multi-step planning with execution-changing self-correction
- Human-in-the-loop plan approval, modification, and cancellation
- Cross-session long-term memory backed by durable cloud storage

The first two are verified at the deterministic workflow level in Phase 3. HITL and durable memory remain targets. Production/live-provider verification is still outstanding; see the compliance tracker for exact evidence.

## Current architecture and planned extensions

- **Language:** Python 3.11
- **API and UI host:** FastAPI with Jinja2. HTMX/server-sent events remain optional future additions when interactive approval/progress requires them.
- **Orchestration:** LangGraph with typed state and explicit `plan → query → retrieve → verify → critic` stages. Conditional edges route sufficient evidence to synthesis or insufficient evidence through targeted query revision and another real retrieval pass.
- **Current model provider:** a deterministic, credential-free development planner whose UI output is explicitly labeled simulated
- **Default production model candidate:** Gemini through Vertex AI, behind the implemented `PlanModel` abstraction
- **Search provider:** a `SearchProvider` interface with deterministic `.test` fixtures by default and a Tavily HTTP adapter when `TAVILY_API_KEY` is configured. The live adapter is not yet smoke-tested.
- **Evidence processing:** provider snippets are normalized to provenance-rich `Source` objects, canonical-URL deduplicated across iterations, capped at 12 retained sources, and treated as untrusted data. No arbitrary source-page fetching occurs yet.
- **Verification:** deterministic lexical relevance, evidence-length/support, plan-item mapping, instruction-like-content quarantine, and limited domain-category signals. These heuristics do not establish truth or comprehensive source quality.
- **Critic and correction:** every plan item needs at least one accepted supportive source. Structured missing, weak, or rejected-evidence gaps generate up to two distinct follow-up queries. The maximum is two total retrieval passes (initial plus one correction) to bound cost and latency.
- **Citations:** every emitted `[S#]` ID is validated against a retained source object before rendering.
- **Future durable state:** an official LangGraph PostgreSQL checkpointer for mutable workflow/HITL state plus the required Google Cloud Storage bucket for evidence, reports, traces, and cross-session memory artifacts. Neither is implemented.
- **Evaluation:** repeatable custom harness with versioned fixtures and raw JSONL/CSV results
- **Observability:** structured JSON events cover iteration number, critic decisions, gap counts, selected routes, follow-up queries, added/accepted evidence, termination reason, cumulative provider usage, and latency without logging external document contents. Cloud export remains future work.
- **Deployment candidate:** the assignment-specific Google Cloud Run Instances + Hermes Agent path, pending instructor clarification documented in [docs/DEPLOYMENT_COMPLIANCE.md](docs/DEPLOYMENT_COMPLIANCE.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries and state transitions.

## Safety and guardrails

Retrieved content stays in typed source fields and cannot directly select graph edges, change iteration budgets, force synthesis, or create citation IDs. Trusted critic state controls routing. Obvious instruction-like text is annotated and excluded from synthesis, including attempts to mark evidence sufficient or change the loop. A delimiter contract exists for future model prompts. This is not the complete assignment safety subsystem, and the three required deployed attacks have not been run.

## Evaluation

The proposed methodology and honest placeholders are in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). Quantitative results, adversarial outcomes, costs, and deployment claims will be added only after actual runs.

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

The suite includes 21 tests. Three deterministic workflow scenarios prove immediate sufficiency, successful correction after a targeted second retrieval, and safe termination at the iteration budget. Additional coverage includes duplicate query suppression, cross-iteration source deduplication and retention, malicious routing instructions, citation integrity, provider invocation, Tavily request parsing, health/UI behavior, and all Phase 1/2 foundations.

## Deployment

Not deployed. There is no live URL. Ordinary Cloud Run is not being treated as equivalent to the rubric's “Cloud Run Instances with OpenClaw or Hermes Agent and monitoring.”

## Limitations

- The default mode uses simulated plans and sources. No live Tavily call was made during Phase 3 verification because no credential was configured.
- The preliminary synthesis is extractive and based on search snippets, not full-document analysis.
- Relevance and quality signals are basic deterministic heuristics and cannot establish objective truth.
- Correction is deterministic and limited to two total retrieval passes; conflict detection remains unimplemented beyond an explicit empty/limited signal because snippets do not encode normalized claim stances.
- There is no approval checkpoint, persistence, complete safety subsystem, or evaluation harness.
- The exact required relationship between DeepTrace and Hermes/OpenClaw needs instructor confirmation.
- GitHub CLI, Docker, and Google Cloud CLI were not detected locally during Phase 0.

## Repository structure

```text
.
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT_COMPLIANCE.md
│   ├── DEVELOPMENT_PLAN.md
│   └── RISK_REGISTER.md
├── app/
│   ├── providers/
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
