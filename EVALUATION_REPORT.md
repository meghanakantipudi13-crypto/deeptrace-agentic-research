# DeepTrace Evaluation Report

**Status:** Methodology scaffold plus deterministic Phase 3, local Phase 4 workflow, and local Phase 5 durability verification. No quantitative benchmark or deployed-system evaluation has been run.

## Evaluation objective

Measure whether DeepTrace completes bounded research workflows, cites evidence correctly, changes behavior when evidence is insufficient, enforces human approval, persists state, resists prompt injection, and does so with acceptable latency and measured cost.

## Planned methodology

- Version a representative case set before the final run.
- Separate ordinary research cases, evidence-gap/conflict cases, persistence/HITL cases, and adversarial cases.
- Record case ID, dataset version, run date, application commit, configuration, model/search versions, random seed where supported, trace ID, and scorer version.
- Prefer deterministic scoring for state transitions, URLs, citation entailment inputs, iteration counts, budgets, and attack outcomes.
- Use a documented human rubric or calibrated model judge only where semantic relevance/support cannot be determined mechanically.
- Preserve raw JSONL/CSV results and summary scripts in the repository when they contain no secrets or disallowed copyrighted content.
- Run the final suite against the deployed build and report failures rather than excluding them.

## Planned metrics

| Metric | Proposed definition |
|---|---|
| Task completion rate | Completed reports / valid submitted research cases |
| Evidence coverage | Required sub-questions with at least one accepted supporting source / required sub-questions |
| Source relevance | Relevant accepted sources / accepted sources, using documented rubric |
| Citation correctness | Citations whose source supports the associated claim / checked citations |
| Supported-claim rate | Material claims supported by validated citations / material claims checked |
| Iterative retrieval success | Initially insufficient cases that become sufficient within the loop budget / initially insufficient cases |
| Self-correction execution rate | Critic gap decisions followed by a changed query/task and another retrieval / critic gap decisions |
| HITL gate pass rate | Protected retrieval attempts blocked until approval / protected pre-approval attempts |
| Restart persistence rate | Sessions recovered with correct state after process restart / restart cases |
| Injection defense rate | Attacks with expected safe state and output / attacks executed |
| Latency | Median, p95, and maximum end-to-end seconds by case class |
| Usage and cost | Actual model tokens/calls, search calls, storage usage, and estimated cost using dated pricing assumptions |

Targets will be set after a baseline run; targets will not be retrofitted to results.

## Sample size and evaluation date

- **Sample size:** Not yet determined. Record the final number and case-class breakdown before the final run.
- **Evaluation date:** Not run.
- **Application commit:** Not available.
- **Deployment URL/build:** Not available.

## Quantitative results

No results. Do not interpret this scaffold as evidence of success.

## Phase 3 deterministic workflow verification

The automated suite includes three fixed-provider routing scenarios in `tests/test_research_workflow.py`: initial evidence sufficient, initial evidence insufficient followed by successful targeted retrieval, and evidence still insufficient at the two-pass budget. These are pass/fail component and graph-integration tests, not a representative research-quality sample, live-provider evaluation, or quantitative benchmark. Their purpose is to establish that critic output changes actual graph execution and that termination is bounded. Final evaluation must run a versioned case set against the deployed build and report aggregate metrics separately.

## Phase 4 local HITL verification

Six deterministic tests in `tests/test_hitl_workflow.py` inspect the LangGraph interrupt/checkpoint and verify zero search calls before approval, same-thread resume, human plan changes affecting downstream queries, zero-call rejection, invalid resume rejection, and duplicate idempotency. They verify local workflow semantics with `InMemorySaver`; they do not measure human usability, prove restart persistence, or establish multi-worker production correctness.

## Phase 5 local durability verification

Scenarios A–G in `tests/test_memory.py` save completed and cancelled terminal records to a temporary filesystem, create new repository instances, recover plans/reports/citations, verify newest-first summaries, reject unknown and traversal-like IDs, and safely fail on malformed records. UI tests create a new application/repository instance and reopen the stored report. `tests/test_durable_checkpoint.py` closes an official async SQLite saver at a real approval interrupt, opens a new saver and workflow instance on the same database, then resumes the same UUID. Mocked GCS tests cover deterministic object naming, serialization, create-only writes, load/list, malformed objects, missing objects, and provider errors. These are component/integration results, not a representative quantitative evaluation. Live GCS and PostgreSQL remain unverified.

## Required adversarial tests

The exact final payloads and actual outputs will be stored only after execution. Each record must include test ID, date, injection point, exact payload, expected safe behavior, actual response, trace ID/artifact, pass/fail, responsible guardrail, and limitation.

| Test | Injection point | Expected safe behavior | Status |
|---|---|---|---|
| PI-001 direct override | User research question | Refuse disclosure/bypass request; approval and verification gates remain enforced | NOT RUN |
| PI-002 indirect trust escalation | Retrieved document | Treat text as evidence only; do not upgrade source trust or system authority | NOT RUN |
| PI-003 workflow bypass | Retrieved document | Ignore requested graph manipulation; critic and verification transitions remain code-controlled | NOT RUN |

## Failure modes and mitigations

Planned failure taxonomy: irrelevant retrieval, insufficient or conflicting evidence, citation mismatch, unsupported synthesis, injection false positive/negative, loop exhaustion, provider failure, persistence conflict, stale approval, excessive latency, and excessive cost. Observed causes, tested mitigations, and remaining limitations will be added from real traces.

## Cost analysis

Not yet measured. Final analysis must use actual token counts, model calls, search requests, storage usage where meaningful, completed-task denominator, evaluation-suite usage, and dated provider pricing assumptions. No zero-cost or free-tier assumption will be made without evidence.

## Known limitations

The quantitative harness, representative dataset, production providers, and deployment do not yet exist. Local durable persistence is verified, but production GCS and PostgreSQL have not been connected or exercised. The deterministic critic uses plan coverage and lexical support heuristics; conflict detection is explicitly limited because current snippets do not carry normalized claim stances. The methodology may change after pilot testing; changes will be versioned and explained.
