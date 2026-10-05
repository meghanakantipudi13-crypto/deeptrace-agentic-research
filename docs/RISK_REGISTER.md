# Initial Risk Register

| Risk | Impact | Early mitigation | Evidence needed |
|---|---|---|---|
| Ambiguous Hermes/OpenClaw deployment boundary | A functional app may still be noncompliant | Ask the five documented instructor questions before locking deployment; keep core portable | Written clarification plus deployed topology review |
| Cloud Run Instance beta availability/quota | Deployment could fail late | Run a Phase 0/1 account and region feasibility check as soon as tools/credentials are available | Successful minimal instance spike and cost estimate |
| Non-durable or corrupt state | HITL/memory claims fail after restart | Official LangGraph PostgreSQL checkpointer for mutable state; GCS for versioned artifacts; never put live SQLite locks on GCS FUSE | Process/instance restart and concurrency tests |
| Decorative HITL | Retrieval proceeds without genuine approval | Code-enforced state gate, plan revision checks, idempotent approval endpoint | Negative test proving zero retrieval calls before approval |
| Self-correction only in prose | Advanced feature does not affect execution | Implemented typed critic and conditional router create changed queries and increment trusted iteration state | Scenario B trace/test showing a targeted second retrieval and reevaluation; repeat with live provider later |
| Poor or conflicting retrieval | Unsupported reports and weak metrics | Query decomposition, source quality rubric, diversity checks, conflict representation, safe uncertainty | Fixed-corpus and live-web evaluation cases |
| Indirect prompt injection | Retrieved text manipulates policy/workflow | Trust separation, sanitization, graph-enforced gates, injection signals, exact adversarial tests | PI-002 and PI-003 traces against deployment |
| Injection detector false positives/negatives | Blocks valid research or misses attacks | Use detector as layered signal, not sole authority; measure both attack and benign cases | Confusion matrix and reviewed failures |
| Citation mismatch | Report appears sourced but claims are unsupported | Claim-evidence mapping, quote/span metadata where lawful, final validator | Citation correctness sample with human audit |
| Provider/API outage or drift | Demo failure and irreproducible evaluation | Adapters, timeouts/retries with caps, pinned versions where possible, cached licensed fixtures for tests | Failure-injection tests and provider metadata |
| Live Tavily behavior unverified | Mock contract may not expose account, relevance, quota, or latency problems | Run one bounded credentialed smoke test without recording the key before relying on live search | Dated request metadata, provider response, latency, and usage credits |
| Deterministic verifier is shallow | Lexical overlap may accept weak context or reject paraphrases | Treat scores as preliminary signals; later add calibrated model/human rubric and measure errors | Labeled relevance set and false-positive/negative analysis |
| Search snippets omit source context | Preliminary claims may lack full-document support | Label output preliminary; add restricted source fetching/extraction and span-level evidence later | Citation audit against fetched source text |
| Uncontrolled loops/cost | Budget exhaustion or runaway spend | Maximum two total retrieval passes; capped queries/results/sources; application-owned counters | Scenario C loop-exhaustion test plus future measured live cost records |
| Shallow sufficiency critic | Lexical coverage can misclassify strong paraphrases, weak mentions, or conflicts | Require explicit plan coverage, disclose heuristic status, terminate with uncertainty, later calibrate against labeled cases/model review | Scenario A/B/C state assertions now; future relevance/conflict benchmark and human audit |
| External web safety/SSRF | Internal network access or malicious payloads | URL/IP/redirect/MIME/size validation and isolated text extraction | Unit tests covering private IPs, redirects, and oversized content |
| Sensitive data in traces/repository | Security incident and grading penalty | Redaction, `.gitignore`, secret scan before commits/pushes, minimal retention | Secret scan output and logging tests |
| Evaluation bias or tiny sample | Weak quantitative evidence | Freeze case set/methodology before final run; report class counts and failures | Dataset version, sample size, raw results, scorer calibration |
| Demo complexity | Required behaviors are not visible in 5–10 minutes | UI event timeline, deterministic demo scenario, one visible guardrail | Rehearsed script and recorded dry run |
