# Cost Analysis — Productized (hosted API, manual data, no GPU)

> **Live prices** per 1M tokens, pulled 2026-08-04. Anthropic from the internal
> `claude-api` pricing table (cached 2026-06-24); Gemini from
> ai.google.dev/gemini-api/docs/pricing. Prices drift — the token model is the
> durable part; re-pull before quoting to investors. All token math is grounded
> in the actual code.

## Why this thing is cheap to run

Two structural facts from the code:

- **The Judge is rule-based** (`judge.py`) — it does **0 LLM calls**.
- **All arithmetic is deterministic Python** (`finance_engine.py`) — the LLM
  never does math.

So the model is used only to **pick tools** and **write prose**. That's the
whole reason a small/mid model is enough, and it's the single biggest cost lever.

## LLM calls per query (from `orchestrator.py`)

| Intent | LLM calls | Output cap |
|---|---|---|
| `FOLLOWUP_EXPLAIN` | 1 (reuses prior findings) | 260 |
| `FRAUD` | 1 synthesis (Judge is deterministic) | 260 |
| `DECISION / WHATIF / COMPLEX` | 1 plan + 1 synth (**+1 plan only if reflection revises**, bounded ≤2) | 200 / 340 |

**Typical DECISION query = 2 calls; worst case = 3.**

## Tokens per query (estimate)

The plan turn carries the 7 tool JSON-schemas + system prompt; synthesis carries
compact deterministic findings. Reasonable estimate for a typical DECISION query:

| Turn | Input tokens | Output tokens |
|---|---|---|
| Plan (7 tool schemas + system + query + context) | ~2,000 | ~200 |
| Synthesis (findings + query, no schemas) | ~1,000 | ~340 |
| **Total per query** | **~3,000 in** | **~550 out** |

## Cost per query, by model (live prices, ~3,000 in + 550 out)

| Model | $/1M in | $/1M out | **$/query** | Fit for this product |
|---|---|---|---|---|
| Gemini 2.5 Flash-Lite | 0.10 | 0.40 | **~$0.0005** | cheapest; math is deterministic so likely sufficient |
| Gemini 2.5 Flash | 0.30 | 2.50 | **~$0.0023** | cheap + a step up in phrasing quality |
| Claude Haiku 4.5 | 1.00 | 5.00 | **~$0.0058** | strong balanced default |
| Gemini 2.5 Pro (≤200k) | 1.25 | 10.00 | **~$0.0091** | Pro-grade reasoning if you want it |
| Claude Sonnet 5 (intro→8/31) | 2.00 | 10.00 | **~$0.0115** | premium phrasing, intro pricing |
| Gemini 3.1 Pro (≤200k) | 2.00 | 12.00 | **~$0.0126** | frontier Gemini |
| Claude Sonnet 5 (standard) | 3.00 | 15.00 | **~$0.0173** | premium default for a finance product |
| Claude Opus 4.8 | 5.00 | 25.00 | **~$0.029** | overkill — the model isn't doing the arithmetic |

**Recommended launch default: Gemini 2.5 Flash-Lite or Claude Haiku 4.5.** The
LLM only selects tools and phrases answers, so a small model is the right call;
move up only if answer quality demands it.

## Monthly cost per active user

Assuming per-user query volume (a personal CFO is bursty, not daily):

| Usage | queries/mo | Flash-Lite | Gemini 2.5 Flash | Haiku 4.5 | Sonnet 5 (std) |
|---|---|---|---|---|---|
| Light | 20 | ~$0.01 | ~$0.05 | ~$0.12 | ~$0.35 |
| Moderate | 60 | ~$0.03 | ~$0.14 | ~$0.35 | ~$1.04 |
| Heavy | 150 | ~$0.08 | ~$0.35 | ~$0.86 | ~$2.59 |

LLM cost per user is **cents to low single dollars**. At a $5–9/mo price point the
LLM is a rounding error against revenue.

## Scenario: 1,000 active users, 60 queries/mo (60k queries)

| Line item | Flash-Lite | Haiku 4.5 | Sonnet 5 (std) |
|---|---|---|---|
| LLM tokens | ~$31 | ~$345 | ~$1,038 |
| App tier (2–3 containers) | ~$50–150 | same | same |
| Managed Postgres (small) | ~$25–50 | same | same |
| CDN / static SPA | ~$0–10 | same | same |
| Auth provider (≤10k MAU) | ~$0 | same | same |
| **Total / mo** | **~$110–240** | **~$430–550** | **~$1,110–1,250** |

At $5/mo × 1,000 users = **$5,000 revenue** → **~75–98% gross margin** depending on
model tier. High-margin SaaS shape, because the expensive part (the math) is free.

## Fixed floor at launch (near-zero users)

No GPU means no idle burn. Everything has a free tier:

| Component | Free-tier path | Paid small |
|---|---|---|
| App hosting | Fly/Render/Railway free | ~$5–25/mo |
| Postgres | Supabase / Neon free | ~$25/mo |
| Static SPA | Cloudflare Pages / Vercel free | ~$0 |
| Auth | Clerk/Supabase free (≤5–10k MAU) | per-MAU after |
| **Floor** | **~$0/mo** | **~$25–50/mo** |

You can run the whole product at **~$0/mo** until you have real users. The old
Kaggle deployment had a hard GPU dependency; this has none.

## Cost levers, ranked

1. **Model tier** — ~20× swing ($0.0008 → $0.018/query). Because math is
   deterministic and the Judge is rule-based, start **small** and only move up a
   tier if answer *phrasing/tool-selection* quality demands it. Biggest lever.
2. **Prompt-cache the static prefix** — the 7 tool schemas + system prompt are
   identical every call and dominate the plan turn's input. Cached-input is ~10×
   cheaper: Gemini 2.5 Flash-Lite $0.10→$0.01, Haiku 4.5 $1.00→~$0.10. Roughly
   **halves total input cost** since the plan turn is schema-heavy.
3. **Router already avoids work** — `FOLLOWUP`/`FRAUD` are 1 call, Judge is 0.
   The architecture is already token-frugal; don't add speculative LLM steps.
4. **Reflection is bounded ≤2** — worst case adds one plan turn, so cost is
   capped and predictable, not open-ended.
5. **Output already capped** (200/340/260) — no further squeezing needed.

## Bottom line

- **Marginal cost per user: cents/month** (small model) to ~$1–3/month (mid).
- **Fixed floor: ~$0** until you have users — no GPU to idle.
- **Dominant cost is LLM tokens**, and the deterministic core keeps that small
  and lets you use a cheap model. This is a **high-margin** product shape.

---

_Sources (pulled 2026-08-04): Anthropic — internal `claude-api` pricing table
(cached 2026-06-24); Gemini — [ai.google.dev/gemini-api/docs/pricing](https://ai.google.dev/gemini-api/docs/pricing).
Batch API on both providers is 50% off if you ever move non-interactive work
(e.g. nightly report generation) off the live path._
