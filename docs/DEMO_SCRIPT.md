# DeepTrace Demo Script (7–8 minutes)

Record the actual browser and terminal. Keep the deterministic demo configuration visible and do not describe simulated evidence as live web research.

## 0:00–0:40 — Problem and originality

- State that DeepTrace is an original research-verification agent, not an Assignment 3 personal-assistant extension.
- Show the repository and explain the problem: one-shot research can hide weak evidence, unsupported citations, and prompt injection.

## 0:40–2:10 — Planning and real human approval

- Start with `scripts/run_demo.ps1` and open the application.
- Submit: `What evidence should a university evaluate before adopting generative AI tutoring?`
- Show **Research Plan Awaiting Approval** and the notice that external research has not started.
- Modify one plan item, save it, and approve.
- Explain that LangGraph interrupted after planning and resumed the same checkpointed workflow.

## 2:10–4:15 — Agentic RAG and self-correction

- Show initial queries and retrieval pass 1.
- Point out the instruction-like source was quarantined and excluded from citations.
- Show the critic's evidence gap, revised query, second retrieval pass, verification, and final cited result.
- Emphasize that code-owned graph routing—not retrieved/model text—controls execution.

## 4:15–5:15 — Guardrail evidence

- Show the rejected/quarantined source and its safety metadata.
- Briefly show the three recorded adversarial cases in `eval/adversarial_results_local.json`.
- State that prompt filtering is layered with typed state, fixed graph edges, bounded resources, and citation closure.

## 5:15–6:15 — Cross-session memory

- Open **Research History** and the completed record.
- Stop and restart the server; reload history to show the record survives the process restart.
- Explain that this is local cross-session persistence, not cloud/distributed memory.

## 6:15–7:15 — Evaluation and costs

- Show `EVALUATION_REPORT.md`: 27/27 cases, 100% citation validity, three attacks mitigated.
- Show the measured Vertex planning smoke evidence and clearly separate it from deterministic benchmark results.
- State the measured call's token count/cost estimate and the $0/week local infrastructure estimate.

## 7:15–8:00 — Limitations and close

- Name the main limitations: simulated demo retrieval, snippet-level evidence, heuristic verification, local single-user persistence, and no live Tavily/deployed-cloud test.
- End on the four demonstrated advanced features: planning/self-correction, HITL, agentic RAG, and cross-session memory.

## Recording checklist

- Keep the recording between 5 and 10 minutes.
- Demonstrate behavior; do not substitute slides for the application.
- Trigger all four claimed features and at least one guardrail.
- Avoid showing `.env`, ADC files, tokens, API keys, or personal browser/account data.
- Verify audio, 1080p readability, and that the final MP4 opens before upload.
