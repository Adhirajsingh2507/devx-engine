# ORBIT-TRUST

**A defensible review — before the deadline — for satellite conjunction analysts.**

Satellite teams don't need another collision *warning*. They get plenty. What
they need is to decide, under a clock, *which* warning deserves attention, whether
the evidence actually supports it, and what a proposed maneuver does to the **rest
of the fleet** before someone commits to it.

ORBIT-TRUST is an evidence-and-response review workspace built on one rule:

> **The deterministic core is authoritative. The AI agent never decides — it only
> assembles evidence, and every word it produces is host-validated or thrown away.**

*Synthetic-data hackathon demo. Honest about what it does and doesn't do — see
[Scope & honesty](#scope--honesty).*

---

## The moment that sells it

A queue sorted by reported collision probability hides the two things that
actually bite:

1. **A lower reported probability can sit next to unresolved evidence and a review
   deadline.** Sorting by Pc alone buries it.
2. **The three-object reversal.** An analyst compares two supplied response
   candidates for a conjunction between satellites **A and B**. Candidate one
   clearly improves A–B — so a Pc-only tool says "take it." ORBIT-TRUST's
   deterministic fleet engine shows that the same maneuver creates a **new
   A–C concern**. The improvement is a regression once you look at the whole fleet.

That reversal is not a slide. It's a passing acceptance test (`T25`/`T26`) driven
by the fleet comparison engine. Deterministic math catches the trap; the bounded
agent helps draft the evidence request around it.

---

## Why it's built to win

- **Trustworthy by construction.** Every number, finding, and template comes from
  the deterministic core. The Google ADK ↔ Groq agent gets a read-only, allowlisted
  tool set (ID-only args, 4 KiB result cap, bounded loop) and may only *select and
  order facts that already exist*. Its proposal is rejected unless it passes a host
  validator. Provider down? It falls back to a deterministic selection with a
  labeled reason and **loses no calculations** (`R13`).
- **Evidence audited separately from urgency.** Two independent status fields —
  "is this urgent?" and "is the evidence complete?" — so an urgent, under-evidenced
  case stays visible instead of being sorted away (`R03`, `R05`).
- **A real numerical core, reference-checked.** A Rust + PyO3 batch engine
  (projection + Gauss–Legendre / periodic-trapezoid polar quadrature with a
  two-grid convergence gate) matches an independent pure-Python oracle across
  `T01–T10`. Measured on 2000 problems: sequential Python **3400 ms** →
  parallel Rust **483 ms** (6.8×), warm cache **83 ms**.
- **Provenance and reproducibility.** Canonical digests, a report ledger with
  dedup / revision / conflict handling (`T16–T18`), and an export bundle that
  reproduces the assessment from its inputs, assumptions, and method (`R15`).
- **Scientific honesty as a feature.** It refuses to fake precision — underflow
  returns `below_computable_precision`, not a confident zero; non-converged
  quadrature surfaces `numerical_nonconvergence` instead of a number.

---

## Architecture at a glance

```
                 evidence in                        response out
   ESA CSV / ─────────────►  ┌───────────────────────────┐ ─────────► export bundle
   encounter JSON            │   DETERMINISTIC CORE       │            (reproducible,
                             │   — authoritative —        │             provenanced)
                             │                            │
                             │  numerics.py  Pc oracle    │
                             │  orbit_core   Rust batch    │
                             │  policy       P0–P3 triage  │
                             │  assessment   findings      │
                             │  fleet        A–B/A–C       │
                             │  economics    expected loss │
                             │  reentry      exposure box  │
                             └────────────┬───────────────┘
                                          │ facts only (IDs, findings)
                                          ▼
                             ┌───────────────────────────┐
                             │   BOUNDED AGENT (ADK/Groq) │  selects & orders evidence,
                             │   read-only · allowlisted  │  drafts one request template
                             │   quota'd · sanitized      │
                             └────────────┬───────────────┘
                                          │ proposal
                                          ▼
                                   HOST VALIDATOR  ──► reject → deterministic fallback
                                          │ accept
                                          ▼
                                   accepted packet
```

Nothing the model emits reaches an accepted packet without passing
`agent.validate_selection`. The agent is a research assistant, not a decision-maker.

---

## Honest status

This is a **backend + numerical core + bounded agent + deploy path**, verified end
to end. The judge-facing web console is the next milestone and is **not built yet** —
today the product is exercised through its API and its acceptance tests.

| Area | State | Evidence |
| --- | --- | --- |
| Reference / acceptance suites | ✅ **13 of 14 green** on the pure-Python path (`T01–T33`) | `tests/reference/` — run them below |
| Rust production core (`orbit_core`) | ✅ built, imported, validated vs oracle | `test_rust_core.py` (needs the native wheel); benchmark in `deploy/benchmark.py` |
| FastAPI surface | ✅ boots; health, capabilities, full core loop | `orbit_trust/api.py`, `test_service.py` |
| Bounded ADK ↔ Groq agent | ✅ live path + deterministic fallback | `N3_SPIKE_REPORT.md`, `docs/n3_live_trace.json` |
| Supabase persistence | ⏳ migrations `0001–0007` applied & seeded on the live project; store swap is the remaining M1 work | `supabase/migrations/` |
| Vercel deploy | ⏳ config tested; separate project + public URL pending owner setup | `vercel.json`, `deploy/` |
| Web console (M6) | ❌ not started — API-first for now | — |

Full milestone/test detail: **`docs/BUILD_STATUS.md`** (PASS / FAIL / BLOCKED
recorded honestly — synthetic fixtures are never reported as customer outcomes).

---

## Quickstart

Prereqs: Python 3.12 (3.10 also runs the pure-Python path). Rust is optional and
only needed for the native core.

```bash
cd orbit-trust
pip install -r requirements.txt

# 1. Prove the science: independent numerical oracle + invariance checks
python3 tests/reference/test_numerics.py        # OK: T01–T06, T10

# 2. Run the whole acceptance suite (13/14 green without the Rust wheel)
for t in tests/reference/test_*.py; do python3 "$t"; done

# 3. Boot the API
python3 -m uvicorn app:app --reload
#   GET /api/v1/health         → {"status":"ok", ...}
#   GET /api/v1/capabilities   → engine, policy version, groq_enabled, live smoke Pc
```

Every request is scoped by an `X-Demo-User` identity and an `X-Workspace-Id`
header; `POST /api/v1/workspaces/demo` creates a workspace, then import a bundle
from `data/fixtures/` and walk the core loop (`test_service.py` is the reference
sequence). Live agent runs need Groq/Supabase credentials — see **`docs/SETUP.md`**.

---

## Scope & honesty

The pitch is only as strong as what it refuses to claim.

- **It is not a tracking or screening network.** It assesses *supplied* encounters
  over a *supplied* catalogue and time interval; it does not discover objects.
- **It cannot prevent or execute a collision-avoidance maneuver.** All maneuver-like
  actions are simulation records. Acknowledgement is not execution.
- **The physics is one declared model** — short linear Gaussian independent encounters
  — not arbitrary orbital propagation.
- **Financial figures are conditional models,** labeled as such. A warning does not
  "save" a spacecraft's value; there is no guaranteed-savings claim.
- **The reentry sandbox reports exposure under a supplied footprint.** It is not a
  predicted crash location and cannot change orbital queue priority.
- **All data is synthetic** and persistently labeled as such.

Language shown to users follows the same discipline: "Review now,"
"Evidence incomplete," "Calculation unsupported," "Estimated change in expected
loss" — never "Safe satellite," "Collision certain," or an agent-agreement
confidence percentage.

---

## Tech

Python 3.12 · FastAPI · Rust + PyO3 (maturin) · Google ADK + LiteLLM + Groq
(bounded, optional) · Supabase (Postgres + RLS + atomic RPCs) · Vercel Python
Functions.

Prior-work reuse is disclosed in **`SOURCE_REUSE.md`** (terrasight, Finora, sajawat)
— adapted patterns, not copied secrets or business logic. Full specification lives
in `../main project/orbit_trust_handoff/` (docs 00–19); this directory is the
implementation, scoped entirely to `orbit-trust/` and never touching the sibling
`3d-game/` app.

## Map

```
app.py                 FastAPI Vercel entrypoint
orbit_trust/           API, numerics, domain, policy, agent, persistence
  api.py               liveness · compute cores · workspace core loop
  numerics.py          independent Pc reference oracle
  service.py / store.py  workspace domain ops · in-memory store (Supabase swaps in)
  agent.py             bounded investigate() with host-validated fallback
  investigator.py      live ADK ↔ Groq two-stage workflow
  quota.py / sanitize.py  run/token budgets · injection & contact sanitization
crates/orbit_core/     Rust + PyO3 numerical batch core (built via maturin)
contracts/             canonical JSON Schema
data/fixtures/         synthetic bundles + expected outputs
tests/reference/       independent numerical & acceptance checks (T01–T33)
supabase/migrations/   tables · RLS · grants · atomic RPCs (0001–0007)
deploy/                Vercel runbook · benchmark
docs/BUILD_STATUS.md   live, honestly-recorded status
```
