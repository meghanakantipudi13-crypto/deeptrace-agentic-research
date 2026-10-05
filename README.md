# DeepTrace

DeepTrace is a developing production-ready agentic research and source-verification platform for CSCI 599 Assignment 4. A user will eventually submit a research question, review a generated plan, and—only after approving or modifying that plan—allow the system to iteratively retrieve, assess, verify, and synthesize evidence with traceable citations.

This repository has completed **Phase 1: minimal observable planning workflow**. The runnable application accepts and validates a question, sends it through a real three-node LangGraph workflow, creates a structured deterministic research plan, and renders that plan in a FastAPI/Jinja interface. It intentionally stops there. No retrieval, approval workflow, source verification, self-correction, persistent memory, or production model call is implemented. Status claims are tracked in [RUBRIC_COMPLIANCE.md](RUBRIC_COMPLIANCE.md).

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

These are targets, not current implementation claims.

## Current architecture and planned extensions

- **Language:** Python 3.11
- **API and UI host:** FastAPI with Jinja2. HTMX/server-sent events remain optional future additions when interactive approval/progress requires them.
- **Orchestration:** LangGraph with typed state and explicit `start_workflow → create_plan → finish_workflow` edges. Checkpointed pauses and correction loops are future work.
- **Current model provider:** a deterministic, credential-free development planner whose UI output is explicitly labeled simulated
- **Default production model candidate:** Gemini through Vertex AI, behind the implemented `PlanModel` abstraction
- **Search candidate:** Tavily Search API behind an internal search adapter; final selection requires a cost/reliability spike
- **Future content processing:** restricted HTTP fetcher plus deterministic text extraction; retrieved text will always be untrusted data
- **Future durable state:** an official LangGraph PostgreSQL checkpointer for mutable workflow/HITL state plus the required Google Cloud Storage bucket for evidence, reports, traces, and cross-session memory artifacts. Neither is implemented in Phase 1.
- **Evaluation:** repeatable custom harness with versioned fixtures and raw JSONL/CSV results
- **Observability:** structured JSON events now cover requests and Phase 1 graph nodes without logging question content. Cloud Logging/Monitoring export remains future deployment work.
- **Deployment candidate:** the assignment-specific Google Cloud Run Instances + Hermes Agent path, pending instructor clarification documented in [docs/DEPLOYMENT_COMPLIANCE.md](docs/DEPLOYMENT_COMPLIANCE.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries and state transitions.

## Safety and guardrails

Phase 1 implements only foundational question validation: Unicode normalization, malformed control-character removal, blank rejection, a 500-character limit, and user-friendly errors. This is not the assignment safety subsystem. Future layered controls include injection detection, strict separation of instructions from retrieved content, URL restrictions, graph-enforced gates, budgets, and citation validation. The three mandatory attacks have not been run.

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

## Running locally

```powershell
.\.venv\Scripts\python.exe main.py
```

Open <http://127.0.0.1:8000>. `GET /health` returns the deployment-oriented health response.

The default planner is simulated and performs no external model or search calls. Its results must not be described as completed research.

## Testing

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Phase 1 has eight automated tests covering health/UI, input validation, provider injection, LangGraph nodes, structured plan output, and the deliberate workflow boundary. Later phases will add HITL, persistence/restart, RAG, self-correction, safety/adversarial, evaluation, and deployment tests.

## Deployment

Not deployed. There is no live URL. Ordinary Cloud Run is not being treated as equivalent to the rubric's “Cloud Run Instances with OpenClaw or Hermes Agent and monitoring.”

## Limitations

- The application produces only a plan; it does not conduct research.
- The current planner is simulated. Vertex AI and search providers are not implemented or locked.
- There is no approval checkpoint, retrieval, verification, self-correction, persistence, safety subsystem, or evaluation harness.
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
│   ├── static/
│   ├── templates/
│   ├── main.py
│   ├── models.py
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
