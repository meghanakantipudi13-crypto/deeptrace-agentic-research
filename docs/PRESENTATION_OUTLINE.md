# Technical Presentation — 13-Slide Authoring Script

Use this script to create the editable deck when Spaces/Slides creation is available. Keep the register technical, use a 16:9 layout, and prefer editable diagrams/tables over screenshots except where the actual UI is evidence.

## 1. DeepTrace

**Agentic research with approval, correction, and source verification**

CSCI 599 Capstone · Meghana Kantipudi

Visual: minimal title slide with `PLAN → APPROVE → VERIFY → CORRECT → CITE`.

## 2. Problem and originality

- One-shot research hides evidence gaps and unsupported citations.
- Retrieved text may contain instructions designed to redirect an agent.
- DeepTrace is an original research-verification system, not an Assignment 3 personal-assistant extension.
- Design goal: make decisions inspectable and fail safely when evidence remains insufficient.

## 3. Architecture

Editable diagram: `Question → Validate → Plan → HITL interrupt → Query → Retrieve → Verify → Critic ↺ Revise → Citation-checked synthesis → History`.

Side labels: FastAPI/Jinja UI; LangGraph typed state; SQLite checkpoints; filesystem research memory; provider interfaces.

## 4. Design decisions

| Decision | Rationale | Consequence |
|---|---|---|
| Typed LangGraph state | Make control transitions explicit | Model/retrieved text cannot select graph edges |
| Real interrupt/resume | Approval must protect execution | Zero search calls before approval |
| Separate checkpoint/history stores | Mutable workflow and terminal records have different needs | Clear persistence lifecycle |
| Bounded deterministic demo | Reproducible grading evidence | Simulated retrieval is visibly labeled |

## 5. Four advanced capabilities

1. Multi-step planning and execution-changing self-correction
2. Human-in-the-loop approve / modify / cancel
3. Agentic RAG with verification and citation closure
4. Cross-session local research memory

Footer: all four verified in the local deterministic deployment; cloud durability is not claimed.

## 6. HITL and memory sequence

Sequence diagram: user submits → graph plans → interrupt saved → UI shows plan → user modifies/approves → same thread resumes → terminal record saved → server restarts → history reloads.

Evidence: unknown workflow rejected; duplicate approval cannot execute twice; cancellation causes zero retrieval.

## 7. Agentic RAG and self-correction

- Pass 1: initial queries; one instruction-like source quarantined; critic finds missing evidence.
- Pass 2: revised query targets the gap; safe evidence accepted; critic marks coverage sufficient; synthesis cites only retained sources.

Bound: maximum two retrieval passes.

## 8. Safety and trust boundaries

`Normalize → inspect input/plan → explicit approval → inspect/quarantine retrieval → fixed routing/budgets → citation closure → bounded persistence`

- Retrieved content cannot approve, change counters, skip verification, or mint citation IDs.
- Safety events contain identifiers/rule IDs, not prompts, secrets, or evidence bodies.
- Rate, length, query, result, source, and iteration limits bound resource use.

## 9. Three real prompt-injection attacks

| Attack | Injection point | Actual result |
|---|---|---|
| PI-001 override/exfiltration | user question | rejected before workflow; 0 search calls |
| PI-002 false trust/skip verification | retrieved source | quarantined; safe second pass; malicious source not cited |
| PI-003 alter approval/counter/citation | retrieved source | approval retained; fixed budget; fake S999 absent |

Result: 3/3 unsafe objectives prevented in the operating local workflow.

## 10. Evaluation methodology

- Versioned `deeptrace-eval-v1` dataset; 27 cases; complete enumeration.
- Six categories: initial sufficiency, correction, bounded insufficiency, citations, safety, HITL.
- Same workflow with deterministic providers; schema-validated expected/actual results.
- Scope: graph-policy correctness, not live-web truth or human relevance judgment.

## 11. Quantitative results

- task completion: 27/27 (100%)
- self-correction: 5/5 (100%)
- HITL enforcement: 5/5 (100%)
- citation validity: 39/39 (100%); unsupported citations: 0
- safety attacks: 3/3 mitigated
- evidence coverage: 37/41 (90.244%); four designed gaps disclosed safely

## 12. Deployment and cost

- Justified local FastAPI deployment; no public URL required for video-based grading.
- SQLite checkpoints + filesystem history survive process restarts.
- Deterministic evaluation cost: $0.
- Vertex planning call: 415 input + 248 output = 663 tokens; estimated $0.00037225.
- 100 equivalent planning calls/week: about $0.0372; local billed infrastructure: $0/week.

Footnote: pricing snapshot 2026-11-19; estimate covers planning only.

## 13. Limitations and future improvements

Current limitations: simulated submission retrieval; live Tavily unverified; snippet-level evidence; heuristic verification; two-pass ceiling; single-machine/single-user persistence; no authentication or distributed concurrency.

Future work: human-judged live-web benchmark; conflict detection; authenticated multi-user service; shared persistence; broader adversarial corpus; controlled Tavily/GCS/PostgreSQL integration only when justified.

Close: DeepTrace demonstrates four end-to-end agentic capabilities with measurable safety and evaluation evidence.
