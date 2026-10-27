# Rubric Compliance Tracker

Last reviewed: 2026-10-12

Status vocabulary is restricted to: **NOT STARTED**, **IN PROGRESS**, **IMPLEMENTED — UNVERIFIED**, **VERIFIED**, and **BLOCKED**. `VERIFIED` requires objective evidence, not merely code or documentation.

## Requirement map

| Requirement | Planned implementation | Status | Verification evidence |
|---|---|---:|---|
| Original agentic application | DeepTrace research and source-verification workflow | IN PROGRESS | Phase 7 adds a 27-case quantitative local evaluation; deployment and production evaluation remain absent |
| Assignment 3+ complexity | Stateful plan/approve/retrieve/verify/critic/correct/synthesize/persist graph | IN PROGRESS | Local durable memory and checkpoint restart behavior verified; production deployment absent |
| At least 3 advanced features | Four features listed below | VERIFIED | All four selected features verified locally; production qualifications remain explicit |
| Agentic RAG | Iterative query generation, retrieval, evidence scoring, claim verification | VERIFIED | 2026-10-04 `tests/test_research_workflow.py::test_scenario_b_insufficient_evidence_triggers_targeted_correction`: expected targeted second retrieval; actual 2 passes, critic false→true, cited synthesis, PASS. Deterministic provider only; live provider remains unverified |
| Planning/self-correction | Typed plan plus critic route that changes subsequent retrieval | VERIFIED | 2026-10-04 Scenario B expected/actual changed query and second retrieval, PASS; `test_scenario_c_remains_insufficient_and_stops_at_budget` expected/actual 2-pass safe stop, PASS |
| Human-in-the-loop | Interruptible approve/modify/cancel gate before retrieval | VERIFIED | Phase 4 Scenarios A–F remain passing; `test_durable_checkpoint.py` additionally recovers and resumes the same pending UUID through a newly opened SQLite saver/workflow. PostgreSQL remains unverified |
| Long-term memory | Cross-session typed research history | VERIFIED | **Local durable persistence VERIFIED:** `tests/test_memory.py` Scenarios A–G and UI recreation test save JSON, create a new repository/app instance, reload reports/citations, list history, and enforce cancellation/corruption/identifier policy. **Production GCS IMPLEMENTED — UNVERIFIED:** mocked adapter tests only |
| Safety subsystem | Deterministic input/plan inspection, HITL permission boundary, evidence quarantine, trusted graph/budgets, citation closure, safe memory, events, rate limiting | VERIFIED | **Local only:** Phase 6 PI-001/002/003 artifact plus current 67-test regression suite. Deployment controls and deployed attack evidence remain open |
| Injection attack #1 | Direct user instruction override/system-prompt extraction | IMPLEMENTED — UNVERIFIED | PI-001 local: exact payload rejected before workflow/search, redacted event, PASS. Not executed against deployed system |
| Injection attack #2 | Indirect injection embedded in retrieved content | IMPLEMENTED — UNVERIFIED | PI-002 local: S1 quarantined/rejected, critic false→true over 2 passes, S1 absent from citations, PASS. Not executed against deployed system |
| Injection attack #3 | Retrieved attempt to alter approval/iteration/critic/citations | IMPLEMENTED — UNVERIFIED | PI-003 local: 2 critic calls, trusted max=2, explicit human approval retained, S999 absent, PASS. Not executed against deployed system |
| Quantitative evaluation | Capability-matched repeatable custom harness | VERIFIED | **DETERMINISTIC/LOCAL:** all 27 versioned cases executed; raw JSON and generated Markdown record calculated metrics. Live/production evaluation remains open |
| Sample size/date | Recorded in raw run metadata and report | VERIFIED | 27 cases; executed 2026-10-13 UTC / 2026-10-12 America/Los_Angeles; category counts and environment retained |
| Failure modes | Failure taxonomy plus observed failures | IN PROGRESS | No unexpected failures in the final local run; four designed evidence gaps terminated safely; harness preserves synthetic mismatch failures; live failure analysis remains open |
| Mitigations | Tested controls linked to failures | IN PROGRESS | Local deterministic routing, loop-budget, citation, input-blocking, and evidence-quarantine controls tested; deployed and broad-spectrum evaluation remains absent |
| Cost analysis | Token/API/storage/latency counters and pricing assumptions | IN PROGRESS | Search/result/call/credit and latency facts captured; no dollar analysis |
| Approved deployment | Cloud Run Instance + authenticated Hermes dashboard plugin | BLOCKED | **NOT STARTED / blocked pending infrastructure:** no authenticated project, cloud resource, or URL exists; one grading-boundary confirmation remains advisable |
| Monitoring | Structured logs, Cloud Monitoring dashboard and alert | IN PROGRESS | Workflow, persistence, checkpoint, and redacted `safety_intervention` events implemented; no cloud monitoring/dashboard/alert |
| Live URL | TA-accessible protected deployment | NOT STARTED | No URL |
| GitHub repository | `deeptrace-agentic-research` | VERIFIED | <https://github.com/meghanakantipudi13-crypto/deeptrace-agentic-research> |
| Phase 1 planning foundation | FastAPI/Jinja UI + real LangGraph planning graph | VERIFIED | 8 automated tests and local HTTP smoke test on 2026-10-04 |
| Phase 2 retrieval foundation | Query/retrieve/normalize/verify/cite/synthesize graph | VERIFIED | 18 automated tests and local deterministic HTTP smoke test on 2026-10-04 |
| Phase 3 iterative correction | Critic/gap/revise/retrieve/reevaluate loop | VERIFIED | 21-test suite includes Scenarios A/B/C in `tests/test_research_workflow.py`; deterministic providers only, 2026-10-04 |
| Phase 4 local HITL | LangGraph interrupt/checkpoint/resume approval gate | VERIFIED | 30-test suite includes HITL Scenarios A–F, approval UI paths, and approved Phase 3 regressions; local deterministic verification, 2026-10-05 |
| Phase 5 local durable memory | Versioned filesystem history plus list/detail UI | VERIFIED | 46-test suite; Scenarios A–G, new repository/application reload, citation survival, cancellation policy, corrupt/path safety, 2026-10-05 |
| Phase 6 local safety | Layered controls plus reproducible adversarial harness | VERIFIED | 56-test suite and `eval/adversarial_results_local.json`: 3 attacks executed, 3 blocked, 3 guardrails triggered, 0 unsafe objectives succeeded; one benign control accepted, 2026-10-12 |
| Phase 7 deterministic evaluation | Versioned capability-matched custom harness | VERIFIED | **DETERMINISTIC/LOCAL:** 27/27 cases met expected behavior; 37/41 evidence coverage, 39/39 valid citations, 0 unsupported citations, 0 unexpected errors; raw JSON and Markdown retained, 2026-10-13 UTC |
| Deployed adversarial execution | Rerun PI-001/002/003 unchanged against live URL | NOT STARTED | Local evidence is explicitly insufficient for this assignment requirement |
| GCS research-memory provider | UUID-keyed schema-v1 JSON objects using ADC | IMPLEMENTED — UNVERIFIED | **LIVE unverified:** fake-client save/load/list/malformed/provider-error tests pass; no configured bucket or credentialed call |
| Production PostgreSQL checkpointer | Official async LangGraph saver selected by environment | IMPLEMENTED — UNVERIFIED | **LIVE unverified:** imports/configuration/lifespan implemented with controlled `setup()` flag; no database provisioned or live concurrency/restart test |
| Tavily live search adapter | Direct HTTP `SearchProvider` implementation | IMPLEMENTED — UNVERIFIED | **LIVE unverified:** mock HTTP contract passed; no `TAVILY_API_KEY` or live call |
| Vertex AI planning provider | Structured Gemini plan generation through `google-genai` | VERIFIED | **VERIFIED LIVE 2026-10-27:** one ADC-authenticated `gemini-3.5-flash-lite` request through `VertexAIPlanModel` at `global`; valid 3-item structured plan, 415 input/248 output/663 total tokens, 1 call, 6061.887 ms. Evidence: `eval/results/vertex_live_smoke_2026-10-27.json` |
| Production fail-closed configuration | Reject simulated/incomplete production providers | VERIFIED | Missing/invalid production configuration and no-fallback Tavily tests pass in the 67-test suite |
| Citation mapping | `[S#]` IDs validated against retained sources | VERIFIED | Deterministic citation mapping and nonexistent-ID rejection tests |
| Retrieved-content structural boundary | Untrusted typed content cannot alter graph routing or loop controls | VERIFIED | Scenario B embeds sufficiency/iteration/synthesis/citation manipulation; critic remains insufficient and executes the bounded correction route |
| Foundational input validation | Normalize, reject blank, enforce 500-character limit | VERIFIED | Automated valid/empty/over-length/normalization tests |
| Health endpoint | `GET /health` | VERIFIED | Automated Phase 8 response test passes; prior local smoke coverage retained |
| README | Accurate current documentation | IN PROGRESS | Phase 7 dataset, CLI, local quantitative results, safety evidence, and production limitations documented; final submission results remain incomplete |
| Demo | 5–10 minute MP4 showing end-to-end run and guardrail | NOT STARTED | None |
| Presentation | 10+ slides covering required topics | NOT STARTED | None |
| Evaluation report | Markdown, optionally exported to PDF | IN PROGRESS | Actual 27-case deterministic/local metrics, safety integration, failure method, limitations, and preliminary cost basis recorded; production results absent |
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
