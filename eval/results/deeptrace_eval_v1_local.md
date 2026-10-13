# DeepTrace Deterministic Evaluation v1

**Scope:** Local deterministic capability evaluation; not live web-research quality or deployed performance.

**Timestamp (UTC):** 2026-10-13T05:00:01.163086+00:00

**Dataset:** `deeptrace-eval-v1`

**Cases:** 27

**Provider mode:** `deterministic_local`

**Git HEAD at execution:** `c05e1a314366b88d5c763f23df7cbe3150552137` (worktree dirty: `true`)

## Dataset

| Category | Cases |
|---|---:|
| citation_integrity | 4 |
| hitl_policy | 5 |
| initial_sufficient | 6 |
| persistent_insufficiency | 4 |
| safety_adversarial | 3 |
| self_correction | 5 |

## Core results

| Metric | Result |
|---|---:|
| Task completion rate | 100.0% (27/27) |
| Expected-termination accuracy | 100.0% |
| Self-correction success rate | 100.0% |
| Evidence coverage | 90.244% (37/41) |
| Citation validity rate | 100.0% (39/39) |
| Unsupported citations accepted | 0 |
| HITL enforcement rate | 100.0% |
| Safety attack defense rate | 100.0% (3/3) |
| Bounded-termination rate | 100.0% |
| Unexpected error rate | 0.0% (0/27) |

## Deterministic performance and resources

The latency sample contains 22 completed research-result workflows. These local fixture timings do not predict production latency.

| Metric | Result |
|---|---:|
| Average workflow latency | 0.786 ms |
| Median workflow latency | 0.707 ms |
| Nearest-rank p95 workflow latency | 1.086 ms |
| Average retrieval passes | 1.409 |
| Average search calls | 2.273 |
| Average retained sources | 2.273 |
| External model calls | 0 |
| Provider credits | unavailable/not applicable |
| Token usage | unavailable/not applicable |

## Failures

- No dataset cases failed in this deterministic run.

## Safety and cost boundaries

Safety defense is derived from `eval/adversarial_results_local.json`, not manually entered. The three attacks were local; deployed adversarial execution remains open.

Measured deterministic paid-provider cost was **$0.00** because no paid API, model, storage, or infrastructure calls occurred. This is not a production cost estimate. Production analysis requires actual token counts, Tavily usage, storage operations, and infrastructure runtime with dated prices.
