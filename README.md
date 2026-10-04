# DeepTrace

DeepTrace is a planned production-ready agentic research and source-verification platform for CSCI 599 Assignment 4. A user will submit a research question, review a generated plan, and—only after approving or modifying that plan—allow the system to iteratively retrieve, assess, verify, and synthesize evidence with traceable citations.

This repository is currently in **Phase 0: repository and architecture planning**. No application feature is implemented or verified yet. Status claims are tracked in [RUBRIC_COMPLIANCE.md](RUBRIC_COMPLIANCE.md).

## Problem

One-shot answer generation can hide weak retrieval, unsupported claims, conflicting sources, and prompt-injection risks. DeepTrace is designed to make the research process inspectable and to stop rather than fabricate when evidence remains insufficient.

## Proposed solution

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

## Proposed architecture and stack

- **Language:** Python 3.11
- **API and UI host:** FastAPI with Jinja2/HTMX and server-sent events, keeping one deployable service while making workflow transitions visible
- **Orchestration:** LangGraph for typed graph state, bounded routing, checkpointed pauses, and explicit correction loops
- **Default cloud model candidate:** Gemini through Vertex AI, behind an internal model adapter
- **Search candidate:** Tavily Search API behind an internal search adapter; final selection requires a cost/reliability spike
- **Content processing:** restricted HTTP fetcher plus deterministic text extraction; retrieved text is always untrusted data
- **Durable state:** Firestore for transactional session/approval state and a required Google Cloud Storage bucket for reports, evidence snapshots, traces, and cross-session memory artifacts
- **Evaluation:** repeatable custom harness with versioned fixtures and raw JSONL/CSV results
- **Observability:** structured event logs and metrics exported to Google Cloud Logging/Monitoring; optional external tracing only after privacy review
- **Deployment candidate:** the assignment-specific Google Cloud Run Instances + Hermes Agent path, pending instructor clarification documented in [docs/DEPLOYMENT_COMPLIANCE.md](docs/DEPLOYMENT_COMPLIANCE.md)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component boundaries and state transitions.

## Safety and guardrails

The planned layered controls include input length/type checks, direct-injection detection, strict separation of instructions from retrieved content, URL/redirect restrictions, content-size limits, structured model outputs, graph-enforced approval and verification gates, maximum loop/call budgets, citation validation, safe failure behavior, and secret-safe structured logging. The three mandatory attacks will be run against the deployed system; no results exist yet.

## Evaluation

The proposed methodology and honest placeholders are in [EVALUATION_REPORT.md](EVALUATION_REPORT.md). Quantitative results, adversarial outcomes, costs, and deployment claims will be added only after actual runs.

## Development plan

Each phase ends with tests and retained evidence. See [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) and [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md).

## Local setup

There is no runnable application yet. Phase 1 will add a pinned dependency manifest, application skeleton, and verified setup commands. The local machine currently has Git and Node.js; a Python 3.11 launcher entry exists, but interpreter execution must be rechecked when Phase 1 begins.

## Environment variables

Copy `.env.example` to a local `.env` only after implementation begins. Never commit `.env` or credentials. Production secrets must come from Google Secret Manager or another instructor-approved secret store.

## Testing

No test suite exists yet. Planned layers are unit, workflow, HITL, persistence/restart, RAG, forced self-correction, safety/adversarial, evaluation, and deployment smoke tests.

## Deployment

Not deployed. There is no live URL. Ordinary Cloud Run is not being treated as equivalent to the rubric's “Cloud Run Instances with OpenClaw or Hermes Agent and monitoring.”

## Limitations

- No application code or tests exist yet.
- Model and search providers are recommendations, not locked dependencies.
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
├── .env.example
├── .gitignore
├── DECISIONS.md
├── EVALUATION_REPORT.md
├── PROCESS_LOG.md
├── README.md
└── RUBRIC_COMPLIANCE.md
```

Application directories will be added only when Phase 1 begins.
