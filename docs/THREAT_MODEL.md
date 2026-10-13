# DeepTrace Safety Threat Model

Last reviewed: 2026-10-12. Scope: Phase 6 local implementation. This is not a deployment penetration test.

## Protected properties

DeepTrace must not reveal privileged prompts or credentials, let untrusted text approve or route a workflow, skip verification/critic stages, change trusted resource limits, create unsupported citations, write arbitrary memory, or represent cancelled/insufficient research as verified evidence.

## Applicable attack surface

| Surface | Applicable risk | Enforced controls | Known limitation |
|---|---|---|---|
| Research question | Direct instruction override, prompt extraction, approval/verification bypass, permission/routing manipulation | Unicode normalization, control removal, 500-character limit, named-rule inspection, multi-signal rejection, redacted event | Lexical patterns can miss obfuscation and can annotate ambiguous wording |
| Human-modified plan | Malicious instructions hidden in title, purpose, or evidence requirements | Pydantic item/count/length bounds plus the same protected-control inspection before `Command(resume=...)` | Semantic manipulation without recognizable control language may pass as data |
| Retrieved results | Fake system messages, trust escalation, fake citations, critic/iteration/routing/approval manipulation | HTTP(S) normalization, provenance, instruction inspection, quarantine, verifier rejection, fixed graph edges/counters, citation closure | Heuristic detector has false-negative risk; no full-page fetch isolation yet |
| HITL route | Unknown, malformed, stale, cancelled, completed, model- or source-driven resume | Canonical UUID, checkpoint status/interrupt validation, typed decision schema, explicit POST, duplicate rejection | Authentication, authorization, CSRF, actor binding, and multi-worker race testing await deployment |
| Persistent memory | Traversal/object-name injection, corrupt schema, oversized record, persisted instruction gaining authority | Canonical UUID object names, resolved filesystem containment, schema v1 with forbidden extras, 1 MB cap, atomic local write, create-only GCS write, no retrieved body persistence | Live bucket IAM, retention, encryption policy, and GCS failure behavior are unverified |
| Output/citations | Fabricated citation, quarantined evidence presented as support, false certainty | Claims use accepted sources only; citation IDs/metadata must close over retained sources; incomplete critic state is disclosed | Deterministic relevance/support heuristics do not establish truth |
| Resource use | Oversized input/plans/results, query explosion, correction loop, repeated POSTs, provider stalls | Schema limits, 3 initial queries, 2 follow-ups, 3 results/query, 12 sources, 1,500 characters/source, 2 retrieval passes, provider timeout, 1 MB memory records, 30 POSTs/minute/process | Rate limit is per-process and IP-based; production proxy/shared limits are still required |

## Layered enforcement

```text
normalized user input -> injection policy -> typed planning -> real HITL interrupt
-> validated human decision -> bounded query generation -> provider timeout
-> untrusted-content inspection -> provenance + quarantine -> verification
-> application-owned critic/routes/counters -> accepted-evidence-only synthesis
-> citation closure -> typed result -> schema-validated durable memory
```

No single prompt is the security boundary. Current deterministic providers do not send retrieved content to a model. If a future model receives evidence, `format_untrusted_evidence()` supplies a dedicated untrusted-data envelope and instruction preamble; the verifier, graph, limits, and citation validator remain authoritative outside the model.

## Safety events

`SafetyEvent` records event type, stage, UTC timestamp, workflow/subject identifiers when applicable, action, named rule IDs, and a concise reason. It excludes inspected payloads, prompts, credentials, headers, chain-of-thought, and complete reports. Events are logged, displayed in the UI, and retained with terminal memory records.

## Decision policy

- No rule match: allow.
- Ambiguous single-signal or defensively framed research: allow with annotation and no authority.
- Multi-signal imperative control bypass or instruction override: block before workflow creation/resume.
- Any instruction-like retrieved content: quarantine from synthesis, then continue through ordinary verification and critic routing.

The one benign Phase 6 control containing quoted attack language was accepted with annotation. This is not sufficient to quantify detector false-positive or false-negative rates; that requires a larger labeled evaluation set in Phase 7.
