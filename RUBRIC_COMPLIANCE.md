# Rubric Compliance Tracker

Last reviewed: 2026-10-04

Status vocabulary is restricted to: **NOT STARTED**, **IN PROGRESS**, **IMPLEMENTED — UNVERIFIED**, **VERIFIED**, and **BLOCKED**. `VERIFIED` requires objective evidence, not merely code or documentation.

## Requirement map

| Requirement | Planned implementation | Status | Verification evidence |
|---|---|---:|---|
| Original agentic application | DeepTrace research and source-verification workflow | IN PROGRESS | Phase 4 runnable approve/modify/reject plus iterative workflow; memory, deployment, and final evaluation remain absent |
| Assignment 3+ complexity | Stateful plan/approve/retrieve/verify/critic/correct/synthesize graph | IN PROGRESS | Local interrupt/resume and conditional correction verified; durable persistence absent |
| At least 3 advanced features | Four features listed below | VERIFIED | Three selected features verified locally with deterministic providers; long-term memory remains unimplemented |
| Agentic RAG | Iterative query generation, retrieval, evidence scoring, claim verification | VERIFIED | 2026-10-04 `tests/test_research_workflow.py::test_scenario_b_insufficient_evidence_triggers_targeted_correction`: expected targeted second retrieval; actual 2 passes, critic false→true, cited synthesis, PASS. Deterministic provider only; live provider remains unverified |
| Planning/self-correction | Typed plan plus critic route that changes subsequent retrieval | VERIFIED | 2026-10-04 Scenario B expected/actual changed query and second retrieval, PASS; `test_scenario_c_remains_insufficient_and_stops_at_budget` expected/actual 2-pass safe stop, PASS |
| Human-in-the-loop | Interruptible approve/modify/cancel gate before retrieval | VERIFIED | 2026-10-05 `tests/test_hitl_workflow.py` Scenarios A–F: real interrupt, zero pre-approval calls, same-thread resume, modified-plan query change, zero-call reject, invalid/duplicate rejection; 6/6 PASS. Local `InMemorySaver` only—not production persistence |
| Long-term memory | Cross-session history/artifacts in PostgreSQL/GCS; restart test required | NOT STARTED | Architecture decision only; no persistence |
| Safety subsystem | Layered deterministic and model-assisted controls | IN PROGRESS | Typed untrusted-content boundary and instruction annotation only |
| Injection attack #1 | Direct user instruction override/system-prompt extraction | NOT STARTED | No attack run |
| Injection attack #2 | Indirect injection embedded in retrieved content | NOT STARTED | No attack run |
| Injection attack #3 | Retrieved attempt to skip critic/verification workflow | NOT STARTED | No attack run |
| Quantitative evaluation | Capability-matched repeatable custom harness | NOT STARTED | None |
| Sample size/date | Recorded in raw run metadata and report | NOT STARTED | None |
| Failure modes | Failure taxonomy plus observed failures | IN PROGRESS | Initial risks only; no observed application failures |
| Mitigations | Tested controls linked to failures | IN PROGRESS | Deterministic routing, loop-budget, citation, and instruction-quarantine controls tested; full safety/evaluation work absent |
| Cost analysis | Token/API/storage/latency counters and pricing assumptions | IN PROGRESS | Search/result/call/credit and latency facts captured; no dollar analysis |
| Approved deployment | Cloud Run Instances + Hermes/OpenClaw topology | BLOCKED | Instructor clarification required; see deployment document |
| Monitoring | Structured logs, Cloud Monitoring dashboard and alert | IN PROGRESS | Phase 4 workflow/interrupt/decision/modification/resume/reject/duplicate plus Phase 3 research events; no cloud monitoring |
| Live URL | TA-accessible protected deployment | NOT STARTED | No URL |
| GitHub repository | `deeptrace-agentic-research` | VERIFIED | <https://github.com/meghanakantipudi13-crypto/deeptrace-agentic-research> |
| Phase 1 planning foundation | FastAPI/Jinja UI + real LangGraph planning graph | VERIFIED | 8 automated tests and local HTTP smoke test on 2026-10-04 |
| Phase 2 retrieval foundation | Query/retrieve/normalize/verify/cite/synthesize graph | VERIFIED | 18 automated tests and local deterministic HTTP smoke test on 2026-10-04 |
| Phase 3 iterative correction | Critic/gap/revise/retrieve/reevaluate loop | VERIFIED | 21-test suite includes Scenarios A/B/C in `tests/test_research_workflow.py`; deterministic providers only, 2026-10-04 |
| Phase 4 local HITL | LangGraph interrupt/checkpoint/resume approval gate | VERIFIED | 30-test suite includes HITL Scenarios A–F, approval UI paths, and approved Phase 3 regressions; local deterministic verification, 2026-10-05 |
| Tavily live search adapter | Direct HTTP `SearchProvider` implementation | IMPLEMENTED — UNVERIFIED | Mock HTTP contract passed; no `TAVILY_API_KEY`, so no live call |
| Citation mapping | `[S#]` IDs validated against retained sources | VERIFIED | Deterministic citation mapping and nonexistent-ID rejection tests |
| Retrieved-content structural boundary | Untrusted typed content cannot alter graph routing or loop controls | VERIFIED | Scenario B embeds sufficiency/iteration/synthesis/citation manipulation; critic remains insufficient and executes the bounded correction route |
| Foundational input validation | Normalize, reject blank, enforce 500-character limit | VERIFIED | Automated valid/empty/over-length/normalization tests |
| Health endpoint | `GET /health` | VERIFIED | Automated test plus Phase 4 local HTTP 200 on 2026-10-05 |
| README | Accurate current documentation | IN PROGRESS | Phase 4 approval/checkpointer/run/test limitations documented; final results incomplete |
| Demo | 5–10 minute MP4 showing end-to-end run and guardrail | NOT STARTED | None |
| Presentation | 10+ slides covering required topics | NOT STARTED | None |
| Evaluation report | Markdown, optionally exported to PDF | IN PROGRESS | Honest scaffold only; no results |
| PROCESS_LOG | Final 200–300 words per member | IN PROGRESS | Chronological notes started; final narrative not written |

## Mandatory categories

### Four selected advanced features

1. Agentic RAG with iterative retrieval and source verification.
2. Multi-step planning with execution-changing self-correction.
3. Human-in-the-loop research-plan approval, modification, and cancellation.
4. Durable long-term memory across process restarts and user sessions.

No claim is made for browser automation, A2A multi-agent collaboration, or hybrid cloud/local routing.

### Safety requirements

- An implemented, tested subsystem—not documentation alone.
- Retrieved content treated as untrusted data and unable to control graph state, permissions, approval, or policy.
- At least three distinct attacks executed against the deployed system with exact payloads, actual responses/traces, dates, pass/fail, responsible controls, and limitations.
- Deterministic resource limits and safe uncertainty when evidence remains inadequate.

### Evaluation requirements

- Quantitative, repeatable methodology with sample size and date.
- Raw results retained where practical.
- Metrics covering research completion, evidence/citation quality, self-correction, safety, latency, usage, and cost.
- Significant failures, mitigations, and remaining limitations documented honestly.

### Deployment requirements

- One of the explicitly permitted deployment paths.
- Live URL accessible to graders.
- Monitoring evidence.
- For the preferred Google path: Cloud Run **Instances** with OpenClaw or Hermes Agent, not an assumed-equivalent ordinary Cloud Run service.
- GCS-backed durable storage for Cloud Run Instance persistence.

### Six deliverables

1. Source code through GitHub or ZIP.
2. Live deployment URL.
3. Five-to-ten-minute demo MP4.
4. Technical presentation with at least 10 slides.
5. Evaluation report in PDF or Markdown.
6. `PROCESS_LOG.md`, 200–300 words per member.

## Evidence promotion rule

Before moving any row to `VERIFIED`, record the relevant test/run identifier, date, artifact path or URL, expected behavior, actual behavior, and pass/fail. Deployment and GitHub rows additionally require independently reachable URLs.
