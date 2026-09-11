# Hackathon Q&A — Multi-Agent Personal CFO

Questions a **hackathon judge** is likely to ask, plus a demo script and the
pitch talking points. Tuned for the *Build with Gemma 4 / GDG TIU Buildathon*
judging criteria: problem, impact, Gemma 4 integration, technical approach, story.

---

## 1. The 30-second pitch

Managing money means juggling a budgeting app, an investment app, a bills app, and
a bank portal — and none of them explain *why*. Our **Multi-Agent Personal CFO** is
one AI that acts like a company's finance department: specialized agents (budget,
bills, loans, fraud, investments, tax) collaborate under an orchestrator, a Judge
validates every recommendation, and **Gemma 4** turns raw numbers into a clear,
explainable answer to questions like "Can I afford this?" — with the math done
deterministically so it's always correct.

---

## 2. Judge-facing Q&A

**Q1. What problem are you solving and why does it matter?**
Financial data is fragmented across apps and gives raw numbers, not guidance. People
make big decisions — a loan, a large purchase — without seeing the full picture, and
fall for fraud. We unify budgeting, bills, loans, investments, tax and fraud into one
explainable assistant that answers real questions instantly.

**Q2. How exactly is Gemma 4 used? (they will push on this)**
Gemma 4 is the reasoning core, three ways: (1) **native function calling** — it
decides which specialist agents to invoke; (2) **explanation** — it turns
deterministic results into a clear recommendation; (3) **conversation** — it resolves
follow-ups like "why?" and "what if ₹50k?". Crucially, Gemma never does arithmetic —
that's deterministic Python — which is exactly what makes financial advice
trustworthy.

**Q3. Isn't this just a chatbot with a system prompt?**
No. A single chatbot can't show *how* it reached an answer. Here you literally watch
the orchestrator select agents, each agent's deterministic result, a Judge validating
against hard financial rules, and — when needed — a revision loop. The multi-agent
structure is visible and the math is auditable.

**Q4. Why should we trust the numbers?**
Every number is computed by a deterministic engine and carries its formula and
inputs. The Judge enforces hard rules (EMI-to-income ≤ 40%, a 3-month emergency-fund
floor, fraud thresholds). If you challenge a figure, the system explains the exact
calculation instead of the model guessing.

**Q5. Show me it actually working / that it's not faked.**
[Live demo — see script below.] The key proof: edit the savings figure in the Edit
Data tab, ask the *same* affordability question again, and the recommendation
changes — because the deterministic engine recomputed on the new data.

**Q6. What's the real-world impact?**
Financial inclusion and better decisions: instant, explainable guidance for students,
salaried workers, freelancers, families and small businesses who can't afford a
financial advisor — plus proactive fraud warnings before a payment is made.

**Q7. Does it run on-device / low resource? (Gemma's edge story)**
The 12B model runs on free Kaggle T4 GPUs in 4-bit. The E2B/E4B Gemma 4 variants run
on a laptop or high-end phone — the same architecture drops onto edge hardware, which
matters for privacy and low-connectivity users.

**Q8. What did you build in 24 hours vs. what's future work?**
Built: the full multi-agent pipeline, deterministic engine, Judge reflection, intent
routing, multi-turn conversation, runtime-editable data, and a working UI on real
Gemma 4. Future: live bank integration (Account Aggregator/Plaid), auth, multimodal
receipt/statement scanning, and more agents (insurance, retirement).

**Q9. How is this different from CRED / Groww / INDmoney / YNAB?**
Those are single-function and don't reason across domains or explain decisions. Ours
unifies budgeting, investments, loans, bills, tax and fraud under one explainable,
multi-agent AI that answers "can I afford this?" holistically.

**Q10. What was the hardest technical challenge?**
Making a 12B model both *correct* and *fast* on free GPUs: we moved all math out of
the model into deterministic code, split the Judge's verdict so good answers aren't
flagged, and added intent routing so simple questions use 0–1 model calls instead of
the full pipeline.

---

## 3. Demo script (3–4 minutes)

1. **Dashboard** — "Here's the user's financial position: income, expenses,
   disposable, savings, CIBIL, emergency fund — all deterministic."
2. **AI Advisor — decision** — Ask *"Can I afford a ₹90,000 iPhone?"* Point at the
   agent activity panel: affordability + loan agents fire, the Judge flags that
   paying outright breaks the emergency fund (transaction_safe = No, risk = caution),
   and Gemma recommends EMI. "The model chose the agents and explained; the numbers
   are Python."
3. **Follow-up (conversation)** — Ask *"Why not?"* — it answers conversationally from
   the previous findings, not a fresh analysis.
4. **What-if** — Ask *"What if it cost ₹50,000?"* — it recomputes.
5. **Fraud** — Ask *"Is it safe to pay on apple-sale-90off.xyz?"* — Fraud agent flags
   CRITICAL; note the answer is correct AND response-valid even though the transaction
   is unsafe (the split verdict).
6. **Edit Data → propagation (the money shot)** — Change savings to ₹5,00,000, Save,
   re-ask the iPhone question. Now it's "affordable outright." "The edit flowed
   straight into the deterministic engine and the next AI answer — no restart."
7. **Fast path** — Ask *"What is my CIBIL score?"* — instant, deterministic, zero
   model calls. "Not every question needs a 12B generation."

---

## 4. Anticipated "gotcha" questions

**Q11. What if Gemma calls the wrong agent or bad arguments?**
The router falls back to the full pipeline when unsure, agents validate their
arguments, and the Judge requires at least one usable finding — otherwise it requests
a single revision. Worst case is a retry, not a wrong number.

**Q12. Where's the data coming from — is it real?**
It's realistic mock data standing in for an Account Aggregator/Plaid feed. The store
is the integration seam; swapping in a live connector doesn't touch the agents or
engine.

**Q13. How do you handle latency in the demo?**
Staged progress feedback in the UI, intent routing so most questions are cheap, and
2 generations max for a normal decision. We also report real T4 timings in the
notebook.

**Q14. Is any of the user's private reasoning exposed?**
No. The raw model chain-of-thought is stripped server-side; the UI only shows safe
execution metadata (agents, result summaries, Judge verdict).

**Q15. Can it scale beyond a demo?**
Yes — the design is modular: per-user state store, a shared batched inference service,
and per-user cache. The agent/engine layer is unchanged by scaling.

---

## 5. Scoring cheat-sheet (map answers to criteria)

| Judging criterion | Your strongest evidence |
|---|---|
| Problem & importance | Fragmented finance apps, no explanations, fraud risk |
| Gemma 4 integration | Native function calling + explanation + multi-turn; math kept out of the model |
| Technical excellence | Deterministic engine, Judge reflection, intent routing, provenance |
| Working prototype | Live edit → recompute demo; runs on free T4 |
| Impact | Financial inclusion + fraud prevention + explainability |
| Story | "A finance department in software, and it explains itself" |
