# Total Cost to Run This as a Product — Everything

> Full cost of ownership: domain, GCP hosting, database, auth, CDN, email, and
> the LLM API. **LLM prices are live (2026-08-04); GCP/infra are reasonable 2026
> estimates** — GCP bills by exact usage, so treat infra rows as ranges, not
> quotes. Assumes the chosen stack: **hosted LLM API, manual/user-entered data,
> no GPU** (see `PRODUCT_ARCHITECTURE.md` and `COST_ANALYSIS.md`).

## TL;DR — all-in monthly cost by stage

Using **Claude Haiku 4.5** as the balanced default model (swap in the cheaper
Gemini 2.5 Flash-Lite to cut the LLM line ~10×):

| Stage | Users | LLM | GCP + infra | Domain | **Total / mo** |
|---|---|---|---|---|---|
| **Pre-launch** | 0–10 | ~$0 | ~$0–10 (free tiers) | ~$1 | **~$1–15** |
| **Soft launch** | 100 | ~$35 | ~$45–70 | ~$1 | **~$80–105** |
| **Growth** | 1,000 | ~$345 | ~$130–230 | ~$1 | **~$475–575** |
| **Scale** | 10,000 | ~$3,450 | ~$600–1,100 | ~$1 | **~$4,050–4,550** |

On **Gemini 2.5 Flash-Lite** the LLM line drops to ~$0 / ~$3 / ~$31 / ~$310 — at
which point **infra, not the model, is your biggest cost.**

**You can launch for ~$1/month** (just the domain) using free tiers everywhere
until you have real users. No GPU means no idle burn — that's the whole point of
the hosted-API choice.

---

## One-time costs (build)

| Item | Cost |
|---|---|
| The app itself | **$0** — the hackathon code exists; productizing is the 4-stage migration in `PRODUCT_ARCHITECTURE.md` |
| Domain, first year (`.com`) | **~$12/yr** |
| Domain, first year (`.ai`) | **~$60–90/yr** (if you want a `.ai` brand) |
| Logo / design | **$0** — the SPA already has a UI |
| TLS / SSL cert | **$0** — Google-managed cert on Cloud Run / Firebase, auto-renewed |
| **Total cash to launch** | **~$12** (`.com`) — the rest is your own build time |

Build time (DIY): the 4 migration stages are ~1–2 focused weeks of work. If you
contracted it out instead, ballpark $3k–8k — but you don't need to; you have the
code and the plan.

---

## Recurring monthly — GCP stack, itemized

| Component | GCP service | Free tier | Small paid | Note |
|---|---|---|---|---|
| App tier (FastAPI) | **Cloud Run** | 2M req/mo free; scales to zero | ~$15–40 | keep 1 instance warm to avoid cold starts |
| Database | **Cloud SQL (Postgres)** | none (db-f1-micro ~$9) | ~$25–80 | or **Neon/Supabase free tier** to start ($0) |
| Static SPA hosting | **Firebase Hosting** | 10GB + 360MB/day free | ~$0–5 | serves `web/` on a global CDN |
| CDN / egress | **Cloud CDN** (via Firebase) | included above | ~$0–30 | grows with traffic |
| Auth | **Firebase Auth / Identity Platform** | very generous free | ~$0 until large | don't build login yourself |
| Secrets | **Secret Manager** | ~free | ~$0–1 | holds the LLM API key |
| Email (password reset, alerts) | SendGrid/Mailgun | ~100/day free | ~$0–15 | transactional only |
| Logging / monitoring | **Cloud Logging/Monitoring** | 50GB/mo free | ~$0–30 | mostly free at small scale |
| **Infra subtotal** | | **~$0–10** | **~$45–230** | scales with users |

**Cheapest viable stack:** Cloud Run (scale-to-zero) + **Neon/Supabase free
Postgres** + Firebase Hosting + Firebase Auth = **~$0/mo infra** until you
outgrow the free tiers. Move Postgres to Cloud SQL when you need backups/HA.

---

## Recurring monthly — LLM API

Per-query ≈ 3,000 input + 550 output tokens, 1–3 calls (see `COST_ANALYSIS.md`).
Monthly LLM cost at 60 queries per active user:

| Users | Gemini 2.5 Flash-Lite | Claude Haiku 4.5 | Claude Sonnet 5 |
|---|---|---|---|
| 100 | ~$3 | ~$35 | ~$104 |
| 1,000 | ~$31 | ~$345 | ~$1,038 |
| 10,000 | ~$310 | ~$3,450 | ~$10,380 |

Prompt-caching the tool-schema prefix roughly halves the input half of these.

---

## The two realistic budgets

### Lean (bootstrapping, free tiers, cheap model)
Cloud Run scale-to-zero · Neon free Postgres · Firebase Hosting+Auth free ·
Gemini 2.5 Flash-Lite · `.com` domain.

| Users | **Total / mo** |
|---|---|
| 0–10 | **~$1** (domain only) |
| 100 | **~$10–20** |
| 1,000 | **~$60–100** |

### Comfortable (production, Haiku, managed DB with backups)
Cloud Run warm · Cloud SQL small · Firebase Hosting+Auth · Haiku 4.5 · email ·
monitoring.

| Users | **Total / mo** |
|---|---|
| 100 | **~$80–105** |
| 1,000 | **~$475–575** |
| 10,000 | **~$4,050–4,550** |

---

## What it means for pricing the product

At $5/user/month:

| Users | Revenue | Cost (comfortable) | Gross margin |
|---|---|---|---|
| 100 | $500 | ~$100 | ~80% |
| 1,000 | $5,000 | ~$525 | ~90% |
| 10,000 | $50,000 | ~$4,300 | ~91% |

High-margin SaaS shape. The deterministic finance engine + rule-based Judge keep
LLM spend low, and with no GPU there's no fixed infra floor to carry before you
have users.

---

## Assumptions & caveats

- **60 queries/active-user/month** — a personal CFO is bursty, not daily. Heavy
  users (150/mo) roughly 2.5× the LLM line; light users (20/mo) roughly ⅓.
- **GCP figures are estimates** — Cloud Run and Cloud SQL bill by exact vCPU/RAM/
  requests/storage. Real bills depend on traffic shape; re-price with the
  [GCP calculator](https://cloud.google.com/products/calculator) before committing.
- **LLM prices are live 2026-08-04** but drift — re-pull before quoting.
- **No bank connectors** (manual data). Real Account-Aggregator/Plaid access adds
  per-call connector fees + compliance cost, out of scope here.
- **Excludes** your own labor, marketing/ad spend, and any paid analytics.
