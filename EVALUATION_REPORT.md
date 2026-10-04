# DeepTrace Evaluation Report

**Status:** Methodology scaffold only. No application or deployed-system evaluation has been run.

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

The application, harness, dataset, and deployment do not yet exist. The methodology may change after pilot testing; changes will be versioned and explained.
