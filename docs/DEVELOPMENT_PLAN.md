# Testable Development Phases

## Phase 0 — Repository and architecture

- **Objective:** Establish truthful governance, compliance mapping, minimum architecture, risks, and Git workflow.
- **Components:** README, rubric tracker, ADRs, evaluation scaffold, process notes, risk/deployment documents, `.gitignore`, `.env.example`.
- **Rubric addressed:** Project governance, GitHub readiness, documentation foundation, deployment analysis.
- **Tests/checks:** File review, Markdown/link scan, Git diff/status, staged secret-pattern scan.
- **Completion evidence:** Documentation-only initial commit; no application claims.

## Phase 1 — Minimal observable workflow skeleton

- **Objective:** Run a deterministic end-to-end graph using fake providers.
- **Components:** Typed session state, FastAPI/UI shell, validate/plan/approve/retrieve/verify/critic/synthesize nodes, structured event recorder, dependency pinning.
- **Rubric addressed:** Originality/complexity foundation and observability.
- **Tests:** Unit tests for state schemas/router; one fake-provider workflow test; event-order assertion.
- **Completion evidence:** Local run and passing tests tied to a commit.

## Phase 2 — Planning and real HITL

- **Objective:** Persist a generated plan and prevent protected work until approve/modify/cancel.
- **Components:** Plan schema/versioning, approval endpoint/UI, pause/resume, idempotency.
- **Rubric addressed:** Multi-step planning and HITL.
- **Tests:** No retrieval before approval; modified plan requires approval of new revision; cancel stays terminal; resume after process restart.
- **Completion evidence:** Test trace with zero pre-approval search calls and correct transitions.

## Phase 3 — Agentic retrieval and evidence model

- **Objective:** Retrieve multiple provenance-rich sources per approved task.
- **Components:** Search/fetch adapters, URL safety, extraction, evidence/source schemas, relevance/quality scoring.
- **Rubric addressed:** Agentic RAG and safety.
- **Tests:** Mocked provider contracts; SSRF/redirect/size tests; fixed-corpus relevance cases; citation provenance round-trip.
- **Completion evidence:** Passing tests and a trace linking plan tasks to sources/evidence.

## Phase 4 — Verification and execution-changing self-correction

- **Objective:** Detect gaps/conflicts/unsupported claims and change actual retrieval within limits.
- **Components:** Claim-evidence verifier, critic rubric, query reviser, loop budget, safe uncertainty path, citation validator.
- **Rubric addressed:** Source verification and planning/self-correction.
- **Tests:** Forced insufficiency triggers a changed second query; conflict retained; max-iteration stop; unsupported citation rejected.
- **Completion evidence:** Trace comparing iteration inputs and critic decisions.

## Phase 5 — Durable cross-session memory

- **Objective:** Recover history, reports, and resumable sessions after process restart.
- **Components:** Firestore/GCS adapters, local fakes, session list/detail UI, retention/redaction policy.
- **Rubric addressed:** Long-term memory and Cloud Run persistence constraint.
- **Tests:** New-process recovery; optimistic concurrency; stale approval rejection; storage outage behavior.
- **Completion evidence:** Restart test and GCS/Firestore object/record metadata without secrets.

## Phase 6 — Layered safety subsystem

- **Objective:** Enforce trust boundaries and resource/tool limits.
- **Components:** Input/injection controls, untrusted-content wrappers, state policy, output/citation validation, budgets, redacted logs.
- **Rubric addressed:** Safety, ethics, alignment.
- **Tests:** Benign/malicious input unit set; retrieved instruction cannot alter state; logging secret canary absent; loop/cost caps.
- **Completion evidence:** Safety test report; still not the required deployed attacks.

## Phase 7 — Evaluation harness and instrumentation

- **Objective:** Produce repeatable quantitative results and measured usage/cost inputs.
- **Components:** Versioned cases, runner, scorers, raw JSONL/CSV, summary generation, dated pricing config.
- **Rubric addressed:** Evaluation/results, failure modes, cost analysis.
- **Tests:** Scorer unit tests; reproducible fixture run; schema validation; aggregate recomputation.
- **Completion evidence:** Pilot results clearly labeled pilot and linked to commit/config.

## Phase 8 — Deployed adversarial evaluation

- **Objective:** Execute and preserve at least three required attacks plus benign controls.
- **Components:** Exact payload fixtures, trace capture, expected/actual records, limitation review.
- **Rubric addressed:** Mandatory prompt-injection testing and safety evidence.
- **Tests:** PI-001, PI-002, PI-003 against deployed build; repeat runs where methodology requires.
- **Completion evidence:** Raw traces/results with date, build, pass/fail, guardrail, and limitations.

## Phase 9 — Assignment-compliant deployment and monitoring

- **Objective:** Produce a stable grader URL on the instructor-confirmed topology.
- **Components:** Container, Cloud Run Instance/Hermes integration, GCS, Firestore, Secret Manager, IAM, Cloud Logging/Monitoring.
- **Rubric addressed:** Deployment, persistence, monitoring, live URL.
- **Tests:** Health/readiness, external URL, end-to-end run, restart persistence, concurrency, alert test, secret scan.
- **Completion evidence:** Deployment revision/config, smoke-test output, monitor evidence, reachable URL.

## Phase 10 — Final evaluation and submission package

- **Objective:** Freeze a release and complete all six deliverables without stale claims.
- **Components:** Final evaluation, README/compliance update, failure/cost report, process log, 10+ slide deck, 5–10 minute demo script/video, release tag.
- **Rubric addressed:** All categories and deliverables.
- **Tests/checks:** Full suite on release commit; URL check from outside account; docs-to-code audit; slide count; video duration/content checklist; process-log word count; repository secret scan.
- **Completion evidence:** Tagged commit, current GitHub repository, live URL, raw/final evaluation artifacts, deck, video, final report, and accurate compliance tracker.

## Milestone rule

At each phase boundary: inspect changes, run the phase checks, preserve evidence, update `RUBRIC_COMPLIANCE.md`, reconcile docs with reality, scan for secrets, commit with a truthful message, and push only when an authenticated remote exists.
