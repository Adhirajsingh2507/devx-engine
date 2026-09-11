# Multi-Agent Personal CFO — Architecture

> An AI personal-finance advisor built as a **finance department in software**:
> an Orchestrator plans which specialist agents to consult, a **deterministic
> Python engine** does every calculation, and a **Judge** validates the result
> (Reflection). **Gemma 4 12B-IT** does all reasoning, planning and explanation —
> never arithmetic.

---

## 1. One-paragraph summary

The user asks a financial question ("Can I afford a ₹90,000 iPhone?"). An **intent
router** decides how much machinery the question needs. For a real decision, the
**Orchestrator** prompts Gemma 4 with the available agents as *tools*; Gemma emits
native function calls; each **agent** runs deterministic math in `finance_engine`;
a rule-based **Judge** validates the findings and splits the verdict into "is the
answer sound?" vs "is the transaction safe?"; then Gemma writes one explainable
answer. Conversation memory makes follow-ups ("why?", "what if ₹50k?") resolve
against the *real prior numbers*. All financial data is editable at runtime and
flows straight back into the engine.

---

## 2. High-level flow

```
                    User question (+ session id)
                              │
                     ┌────────▼─────────┐
                     │   router.py       │  intent classification
                     └────────┬─────────┘
        ┌──────────────┬──────┴───────┬──────────────┬─────────────┐
        ▼              ▼              ▼              ▼             ▼
   FAST_DATA     FOLLOWUP_EXPLAIN   FRAUD        DECISION /     (COMPLEX)
   0 Gemma gens  1 Gemma gen        1 Gemma gen  WHATIF          full
   deterministic reuse findings     fraud+judge  2 Gemma gens    pipeline
        │              │              │              │             │
        └──────────────┴──────────────┴──────┬───────┴─────────────┘
                                              ▼
                            ┌─────────────────────────────┐
                            │  Orchestrator (orchestrator) │
                            │  plan → agents → Judge →      │
                            │  synthesise, with timings     │
                            └───────────────┬──────────────┘
                        tool calls          │        findings
             ┌───────┬─────────┬────────────┼───────┬────────┬────────┐
             ▼       ▼         ▼            ▼       ▼        ▼        ▼
          Budget   Bills     Loan        Fraud  Afford   Invest    Tax    (agents.py)
             └───────┴─────────┴────────────┴───────┴────────┴────────┘
                                              ▼
                            ┌─────────────────────────────┐
                            │  finance_engine.py           │ DETERMINISTIC math
                            │  + formatting.py (₹, %, prov) │ (no LLM)
                            └───────────────┬──────────────┘
                                            ▼
                            ┌─────────────────────────────┐
                            │  financial_store.py          │ mutable, versioned,
                            │  (JSON persistence)          │ JSON-persisted
                            └─────────────────────────────┘
```

---

## 3. Module map

| Module | Responsibility |
|---|---|
| `mock_data.py` | Seed profile / transactions / bills / investments + static fraud intel |
| `financial_store.py` | **Mutable** data layer; CRUD + `replace` + `reset`; JSON persistence; a `version()` counter that bumps on every write |
| `formatting.py` | Centralized `fmt_inr` (Indian grouping), adaptive `fmt_pct`, `pct()`/`calc()` provenance — the single source of number formatting |
| `finance_engine.py` | All deterministic math (EMI, ratios, affordability, emergency fund, fraud scoring, tax). Reads the store at call time; full precision internally |
| `agents.py` | 7 specialist agents, each a Python function + a Gemma tool schema |
| `judge.py` | Rule-based Reflection: `response_ok` vs `transaction_safe`, `risk_level`, confidence, advisories |
| `router.py` | Intent classification → FAST_DATA / FOLLOWUP_EXPLAIN / FOLLOWUP_WHATIF / FRAUD / DECISION / COMPLEX |
| `conversation.py` | Bounded per-session memory (structured findings + verdict + data version); `context_block()` for reference resolution |
| `orchestrator.py` | Dispatcher per intent; ReAct planning; bounded revision; token budgets; per-stage timings + generation counts |
| `llm.py` | Swappable Gemma client (`transformers` 4-bit / fp16 fallback, `echo`, `demo`); tool-call parser; special-token `scrub` |
| `schemas.py` | Pydantic validation for all edits |
| `service.py` | Shared singleton (one loaded model); session helpers; dashboard cache keyed by data version; strips raw reasoning |
| `api.py` | FastAPI REST layer + serves the SPA: `/advise`, `/dashboard`, `/financial-data` CRUD, `/conversation/*` |
| `web/` | **Single-page web app**: AI Advisor (multi-turn) · Dashboard sections · Edit-data drawer (no build step) |

---

## 4. Key design decisions

**Gemma reasons, Python calculates.** No LLM ever computes a number. Every rupee
and percentage comes from `finance_engine`, so results are auditable and
reproducible. This is the mitigation for "AI-generated inaccuracies."

**Native function calling, not a framework.** The Orchestrator uses Gemma 4's own
tool-calling (`<|tool_call>call:name{args}<tool_call|>`) parsed by a small regex —
no LangGraph/CrewAI. The tool-call decisions *are* the multi-agent trace.

**Judge splits two axes.** `response_ok` (is the answer well-founded) is separate
from `transaction_safe` (is the purchase safe). A correct "do NOT pay this scam"
reply is `response_ok=True` **and** `transaction_safe=False` — never a misleading
"rejected."

**Intent routing for latency.** Not every message needs the 12B model. Lookups are
answered deterministically (0 generations); explanations reuse prior findings
(1 generation); a normal decision is 2 (planning + synthesis). Revision fires only
when the Judge finds no usable findings.

**Bounded reflection.** The revision loop is capped (≤2 iterations) so a slow model
can't spin forever.

**Provenance.** Numeric outputs carry raw value + display string + a `calculation`
block, so "how did you get 0.03%?" is answered from stored math, not re-invented.

**Adaptive percentage formatting.** ≥1% → 1 dp; ≥0.01% → 2 dp; smaller → enough
precision to stay non-zero (fixes ₹50 / ₹1,80,000 rendering as "0.0%").

**Runtime-editable data.** The engine reads a mutable store at call time, so edits
in the UI immediately change every metric and the next answer — no model reload.

---

## 5. Request lifecycle (a DECISION)

1. `router.classify` → DECISION.
2. Orchestrator builds a system prompt from the **current** profile + optional
   conversation context, sends the query with the 7 tool schemas (`PLAN_TOKENS`).
3. Gemma returns tool calls; each agent runs deterministic math.
4. `judge.evaluate(findings)` → verdict (response_ok / transaction_safe / risk /
   confidence / advisories).
5. Revision only if `response_ok` is False (no findings).
6. Gemma writes the final explainable answer (`SYNTH_TOKENS`).
7. The turn (user, answer, structured findings, verdict, data version) is stored in
   conversation memory. Raw reasoning is stripped before the payload leaves the
   backend.

**Cost:** normal decision = **2** Gemma generations; fast data = **0**;
explanation follow-up = **1**; fraud = **1**.

---

## 6. Deployment

- **Model:** `google/gemma-4-12B-it`, 4-bit NF4 on Kaggle **T4×2** (fp16 sharded
  fallback if bitsandbytes is unhealthy). Loads **once** via `service.set_orchestrator`.
- **UI:** FastAPI (`uvicorn`) serves the `web/` SPA; a token-free **cloudflared**
  quick tunnel prints a public `…trycloudflare.com` URL.
- **Backend swap:** `GEMMA_BACKEND=auto|transformers|echo|demo`.
- **Reproducibility:** notebook generated from `src/` + `web/` by `build_notebook.py`
  (`%%writefile` cells) so notebook and repo never drift.

---

## 7. Design patterns → research grounding

Grounded in *Agentic AI in Finance: A Comprehensive Overview* (Luqman et al.):

| Paper concept | This system |
|---|---|
| Reflection (§4.1) | Judge loop |
| Tool Use + Computation (§4.1 / §4.3) | Agents → deterministic engine |
| Planning (§4.1) | Orchestrator selecting agents |
| Multi-Agent Collaboration (§4.1) | The whole system |
| Reasoning · Memory · Tools (§4.2) | Gemma 4 · conversation memory · agent tools |
| ReAct (§4.1) | Plan → act loop |
| Risk: incorrect transactions (§5.2) | Deterministic math + Judge validation |

---

## 8. What is mock vs real

- **Mock:** financial data (profile/transactions/bills/investments) and fraud
  intel. Architecture is "Account Aggregator / Plaid-ready" — the interface exists,
  the connector is future work.
- **Real:** Gemma 4 reasoning, native function calling, all deterministic math, the
  Judge, conversation memory, intent routing, and runtime editing.
