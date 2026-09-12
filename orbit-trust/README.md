# ORBIT-TRUST

Evidence-and-response review workspace for satellite conjunction analysts.
Deterministic core (Rust/Python) is authoritative; bounded ADK/Groq agents only
select evidence and pick templates. Synthetic-data hackathon demo.

Full specification: the in-repo [`specification/`](specification/START_HERE.md)
handoff (docs 00-19). This directory is the implementation, scoped entirely to
`orbit-trust/` and built alongside — never touching — the `3d-game/` app.

## Layout (doc 04)
```
app.py               FastAPI Vercel entrypoint (exports the instance)
orbit_trust/         Python API, numerics, domain, persistence, policy, ADK
  api.py             FastAPI surface: liveness, compute cores, workspace core loop
  service.py         workspace domain ops (import/queue/assess/actions/investigate)
  store.py           in-memory workspace store (Supabase-backed store swaps in here)
  agent.py           bounded investigate fallback (Groq/ADK slots behind investigate)
  numerics.py        independent Pc reference oracle (doc 06/12)
crates/orbit_core/   Rust + PyO3 production math core (built via maturin)
contracts/           canonical JSON Schema (+ generated OpenAPI snapshot later)
data/fixtures/       synthetic bundles and expected outputs
tests/reference/     independent numerical checks (T01-T15)
tests/e2e/           browser/workflow checks (later)
supabase/migrations/ tables, RLS, grants, atomic RPCs
vendor/wheels/       reproducible native wheel + build manifest
deploy/              Vercel runbook / tested config
docs/BUILD_STATUS.md live status; game-baseline.txt preservation record
```

## Run locally (what works now)
```bash
cd orbit-trust
python3 tests/reference/test_numerics.py          # numerical oracle self-check
python3 -m uvicorn app:app --reload               # API: /api/v1/health, /api/v1/capabilities
```

## Status
See `docs/BUILD_STATUS.md`. M0 scaffold: reference oracle + FastAPI health run;
Rust wheel, Supabase and Groq spikes are BLOCKED on toolchain/credentials.
