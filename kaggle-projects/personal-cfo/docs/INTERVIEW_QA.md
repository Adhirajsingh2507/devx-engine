# Interview Q&A — Multi-Agent Personal CFO

Technical interview questions an engineer might ask about **this project**, with
model answers. Grouped by theme. Use them to prepare; the answers are specific to
how the system is actually built.

---

## A. System design & architecture

**Q1. Walk me through the architecture in 60 seconds.**
A router classifies each message; a real financial decision goes to an Orchestrator
that prompts Gemma 4 with 7 specialist agents exposed as tools. Gemma emits native
function calls, each agent runs deterministic math in a Python engine, a rule-based
Judge validates the findings, and Gemma writes one explainable answer. Conversation
memory lets follow-ups reuse prior findings. All financial data is editable at
runtime and read by the engine at call time.

**Q2. Why a multi-agent design instead of one big prompt?**
Separation of concerns and explainability. Each agent has one job and one tool, so
the "trace" of which agents fired *is* the reasoning shown to the user. It's also
extensible — adding an Insurance agent is a new function + schema, no redesign.

**Q3. Why did you NOT use LangGraph / CrewAI?**
Gemma 4 has native function calling. Building directly on it means the tool-call
decisions are the orchestration — fewer moving parts, no framework lag on a newly
released model's multimodal/tool paths, and a cleaner story ("we used the model's
own capability"). The tradeoff is I hand-rolled the ReAct + reflection loop, which
is ~150 lines and fully under my control.

**Q4. How does the Orchestrator decide which agents to call?**
It doesn't hard-code that — Gemma does, via function calling. The Orchestrator hands
Gemma the tool schemas and the query; Gemma returns calls like
`check_affordability{amount:90000}`. The Orchestrator just executes them and feeds
results back. That's the Planning + ReAct pattern.

---

## B. Correctness & the LLM boundary

**Q5. LLMs are bad at arithmetic. How do you guarantee correct numbers?**
The LLM never does arithmetic. Every number comes from `finance_engine` (pure
Python) and is passed to Gemma as a tool result. Gemma only explains it. There's a
centralized formatter, and outputs carry calculation provenance, so a number can
always be traced to a formula and inputs.

**Q6. Tell me about a real numerical bug you fixed.**
A ₹50 purchase against ₹1,80,000 savings displayed as "0.0%" because of a premature
`round(x, 1)`. I built adaptive percentage formatting: ≥1% → 1 dp, ≥0.01% → 2 dp,
smaller → enough precision to remain non-zero. ₹50/₹1,80,000 now shows 0.03%, and I
keep full precision internally, rounding only for display.

**Q7. How do you stop the model from hallucinating financial advice?**
Two guardrails. First, the deterministic engine owns all facts. Second, a rule-based
Judge validates findings against hard limits (EMI-to-income ≤ 40%, emergency-fund
floor, fraud threshold) and assigns confidence. The Judge's pass/fail is never
delegated to the model.

**Q8. What does the Judge actually check, and why is its verdict split?**
It checks: EMI ratio within limit, purchase doesn't breach the 3-month emergency
fund, no HIGH/CRITICAL fraud, and that at least one agent ran. It returns two
separate booleans: `response_ok` (is the answer well-founded) and
`transaction_safe` (is the purchase safe). Without the split, a correct "don't pay
this scam" answer would show as "rejected," which is misleading.

---

## C. Conversation & state

**Q9. How do follow-ups like "why?" or "what if ₹50k?" work?**
Per-session bounded memory stores each turn's structured findings + verdict + the
data version used. "Why?" routes to an explanation path that reuses the last
findings and asks Gemma for a short conversational explanation using only those
stored numbers (1 generation, no re-planning). "What if ₹50k?" routes to a decision
with conversation context so Gemma re-runs the tools with the new amount.

**Q10. How do you bound context growth?**
Only the last N turns are kept, and only the most recent turn keeps full findings;
older turns collapse to a one-line decision summary. `context_block()` emits a
compact, reference-resolvable summary — never the raw chain-of-thought.

**Q11. What happens if the user edits their data mid-conversation?**
Every turn records the store's `version()`. If it changed since an earlier turn,
`context_block` appends a note telling the model to recompute rather than reuse old
numbers. The engine always reads current data, so recomputation is automatic.

---

## D. Performance

**Q12. The 12B model on T4 is slow. How did you make it usable?**
Intent routing: lookups ("what's my CIBIL?") are deterministic with 0 generations;
explanations are 1; a normal decision is 2 (planning + synthesis). I removed the
automatic second planning pass — revision fires only when the Judge finds no usable
findings. Token budgets differ by stage (short for tool-selection, moderate for
synthesis). The dashboard is cached by data version. And the model loads exactly
once.

**Q13. How do you measure that, not just claim it?**
The Orchestrator records per-stage wall-clock and a generation counter on every
request (exposed for debug, hidden from the UI). There's a test that asserts the
generation count per intent, and a notebook cell that prints real T4 timings.

**Q14. Why cache the dashboard, and how do you avoid staleness?**
The dashboard is pure deterministic computation, so recomputing on every poll is
waste. It's cached keyed by the store's `version()`, which bumps on every write —
so any edit invalidates the cache immediately.

---

## E. Model loading & infra

**Q15. You hit `module 'bitsandbytes' has no attribute 'functional'`. Diagnose it.**
That's a broken bitsandbytes install — the CUDA backend didn't load, leaving a stub
without `functional`/`nn`. Fix: clean `--no-cache-dir` reinstall of a pinned
version, plus a runtime health check. If it's still broken, the loader falls back to
fp16 sharded across both T4s — same instruction-tuned checkpoint, never the base
model.

**Q16. The 12B didn't fit one GPU. How did you place it?**
4-bit NF4 (~7 GB) fits a single T4. I pass an explicit `max_memory` map so
`device_map="auto"` shards across both T4s instead of over-filling GPU 0 (which had
caused an OOM where GPU 1 was left with ~80 MiB). The fp16 fallback (~24 GB) shards
12/12 across the two cards.

**Q17. How is the model reused across UI events?**
A service singleton holds one Orchestrator wrapping one loaded model. The notebook
injects the already-loaded model via `set_orchestrator`, so no UI action, edit, or
API call ever instantiates a second model.

---

## F. Software engineering

**Q18. How do you keep the notebook and the repo in sync?**
The notebook is *generated* from `src/` by `build_notebook.py` using `%%writefile`
cells. Source is the single truth; regenerating rebuilds the notebook, so they can't
drift.

**Q19. How do you test a system whose core is a 12B model you can't run locally?**
Three backends behind one interface: `transformers` (real), `echo` (silent stub),
and `demo` (a CPU stub that keyword-routes to the real agents). The whole pipeline —
routing, agents, judge, conversation, editing, generation counts — is tested on
`demo` with zero GPU. Real answer quality and wall-clock are validated on Kaggle.
The UI is tested headless with Playwright.

**Q20. How does validation work end-to-end?**
Every edit goes through Pydantic models (`schemas.py`): no negative money, CIBIL in
300–900, positive amounts, valid ISO dates. Errors surface inline in the UI. The
store only mutates after validation passes.

**Q21. What's your security posture on the model's reasoning?**
The raw chain-of-thought is stripped from the trace before it leaves the backend.
The UI only sees safe execution metadata — which agents ran, deterministic result
summaries, the Judge verdict, confidence, advisories.

---

## G. Tradeoffs & scale

**Q22. Biggest weakness of the current design?**
Data is mocked — there's no live bank connection. The architecture is
connector-ready (the store is the seam), but a real Account Aggregator/Plaid
integration, auth, and per-user isolation are future work.

**Q23. How would you scale this to many users?**
Sessions and the store are per-process/in-memory now. I'd move state to a
per-user store (Redis/Postgres), keep the model behind a batched inference service
(e.g. vLLM) shared across users, and make the dashboard cache per-user keyed by
their data version.

**Q24. If routing misclassifies a query, what happens?**
It's conservative: when unsure it falls back to DECISION (the full pipeline), so a
real question is never under-served. The worst case is spending 2 generations on
something that could have been 0 — a latency cost, not a correctness one.
