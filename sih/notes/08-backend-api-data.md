# 08 — Backend API, the Frozen Contract & Data

**Files:** `backend/app/main.py` (FastAPI), `backend/app/db.py` (data access),
`backend/app/pipeline.py` (the runner), `backend/supabase/schema.sql` (the database).

---

## 8.1 From zero: what an API and a "contract" are

An **API** (Application Programming Interface) is a menu of requests a program exposes.
Ours is an **HTTP/REST API**: the frontend sends `GET /map/tiles` over the web and gets
back JSON. **FastAPI** is a Python web framework that turns a function into an endpoint
(`@app.get("/map/tiles")`).

A **contract** is the *exact agreed shape* of those requests/responses. "Frozen"
means: **we fixed the shapes on day one and promised never to break them**, so the
frontend and backend teams could build in parallel without waiting on each other.

## 8.2 The frozen contract (memorize the shapes)

| Endpoint | Returns |
|---|---|
| `GET /health` | `{status, source}` — `source` is `"mock"` or `"supabase"` |
| `GET /map/tiles` | `[{x, y, z, class, slope, safety_score, zone}]` |
| `GET /rover/path` | `[{t, x, y, heading, mode}]` |
| `GET /sites` | `[{id, x, y, safety_score, rank}]` |
| `GET /boundaries` | `[{type, polyline}]` |

Notice what's **not** exposed: `roughness`, `conf`, `crater_dist_m`. These are consumed
*internally* by scoring and then dropped — they never reach the API. Adding a field is a
deliberate, coordinated contract change, and `tests/test_contract.py` **locks these
exact key sets** at both the endpoint layer and the mock-file layer, so accidental drift
fails CI loudly.

`main.py` is intentionally tiny (~40 lines): five endpoints, each one line delegating to
`db.fetch(...)`. Plus CORS (allow the browser to call it) and the `StripPrefix`
middleware (see 8.6).

## 8.3 From zero: Supabase, Postgres, RLS

- **Postgres** — a relational database (tables of rows). Our tables mirror the contract:
  `tiles`, `rover_path`, `sites`, `boundaries` (`schema.sql`).
- **Supabase** — a hosted Postgres plus an auto-generated API and auth. We use it as the
  persistence layer.
- **RLS (Row-Level Security)** — Postgres rules controlling *who can read/write which
  rows*. Ours: **public read** (the dashboard reads freely, anon), **backend-only
  write** via the **service-role key** (which bypasses RLS). So anyone can *view* the
  map; only the rover/backend can *change* it. That's exactly the trust model you want.

## 8.4 The mock-or-Supabase fallback (`db.py`) — a great design touch

```python
def _client():                      # lru_cached
    if SUPABASE_URL and SUPABASE_KEY: return create_client(...)
    return None                     # not configured → None

def fetch(table):
    return supabase_data if _client() else json.load(mock/<table>.json)
```

**If Supabase is configured, serve live data; otherwise serve `backend/mock/*.json`.**
Why this matters:
- The frontend team never blocks on database provisioning — the API *always* returns
  valid, contract-shaped data.
- The live production deploy works with **zero secrets** (serves mock) — you saw
  `/health → source: mock`.
- It's the same code path, just a different data source. Swapping mock→live is one env
  var, no code change.

`test_db_fallback.py` locks this: with Supabase unset, `_client()` is `None`, `fetch`
returns the mock verbatim, `upsert` is a safe no-op, and `_MOCK_FILE` must cover every
served table (a new endpoint can't silently ship without a fallback).

## 8.5 Persistence — writing pipeline output to Supabase (`db.persist`)

The rover's perception pipeline can *write* its results with `pipeline.py --persist` →
`db.persist(out)`. The subtlety is **idempotency**: the pipeline regenerates the *whole*
map each run, so re-running must not duplicate or accumulate rows. The tables have
different keys, so we handle them differently:
- `tiles` → `upsert(on_conflict="x,y")` (natural key = the cell coordinate).
- `sites` → `upsert(on_conflict="id")`; `rover_path` → `upsert(on_conflict="t")`.
- `boundaries` → has only an auto `id` (no natural key), so a row-set upsert can't dedupe
  → we **delete-all then insert** (full replace).
- Unconfigured → returns all-zero counts, **never raises, never writes**.

Why "full-map replace" semantics? Because the pipeline's output *is* the complete
current map — upserting on natural keys (or replacing) means re-runs overwrite in place,
so nothing stale lingers and nothing duplicates.

## 8.6 The `StripPrefix` middleware — a real prod bug fixed

On Vercel the frontend reaches the backend at `/api/backend/*` (a same-origin rewrite),
but the FastAPI routes are `/health`, `/map/tiles` (no prefix). Locally, Next.js *strips*
the `/api/backend` prefix before proxying; on Vercel's `services` rewrite it **doesn't**,
so the backend received `/api/backend/health` and 404'd. Fix: a tiny ASGI middleware that
strips a leading `/api/backend` if present. Now the backend is **proxy-agnostic** — works
whether or not the upstream strips — with no change to the frozen contract (routes stay
unprefixed). Verified live: all five endpoints respond in production.

*(Lesson worth telling: local-dev and prod had different path-rewriting behaviour, and
only an actual prod `curl` caught it — "it deploys" ≠ "it works.")*

## 8.7 The pipeline runner (`pipeline.py`) — ties it all together

`pipeline.run(scene)` executes the whole flow on a scene fixture:
`segment → derive_geometry → fuse_single → build_cells → scoring → tiles/sites/
boundaries/path`. Flags: `--write` (regenerate `mock/*.json`), `--persist` (write to
Supabase). Scoring is the **only** decision step in the chain; terrain assembly hands it
built `Cell`s and the runner calls `safety_score`/`zone`. This runner is what turned the
system from "hand-written mock literals" into a real computed pipeline.

## 8.8 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| **Freeze the contract day 1** | Frontend + backend build in parallel; no blocking | Flexibility to change shapes later without coordination |
| **Mock-or-Supabase fallback** | API never blocks; deploy works secret-free; swap = 1 env var | A second (mock) source of truth to keep consistent |
| Service-role write / public read RLS | Correct trust model; anyone views, only rover writes | Must guard the service-role key religiously (backend-only) |
| Lean deployed backend (no numpy/cv2) | Fast cold starts, small function, cheap | Real CV can't run *in* the serverless API (it's offline/rover tooling) |
| `StripPrefix` middleware | Backend works behind any proxy, no contract change | A few lines of ASGI plumbing |
| Idempotent `persist` (upsert/replace) | Re-runs don't duplicate/accumulate | Per-table handling complexity (boundaries special-cased) |

## 8.9 Alternatives
- **GraphQL** instead of REST — flexible querying, but overkill for 5 fixed read shapes.
- **Backend writes RLS policy** instead of service-role bypass — more granular, but the
  rover-as-sole-writer model is simpler and correct here.
- **WebSockets/SSE for live streaming** — nice for a *live* rover feed; unnecessary for
  the current pull-based dashboard, a clear future upgrade.
- **Serve CV from the API** — rejected: keeps the function fat and slow; perception is
  offline/rover work, the API only *serves* results.

## 8.10 Q&A
**Q: Why freeze the contract?** So both teams build against a fixed shape in parallel and
never block each other; a test locks it so drift fails CI.

**Q: How does the app run without a database?** `db.py` falls back to `mock/*.json` when
Supabase env vars are unset — same code path, different source. Prod currently serves
mock (0 secrets needed).

**Q: How do you keep the service-role key safe?** It lives only in backend env, never in
`NEXT_PUBLIC_*`, never in the frontend bundle, never committed — CI even greps for a
committed key. Public read / backend-write via RLS.

**Q: What made the prod backend 404, and how'd you fix it?** Vercel's `services` rewrite
forwards the full `/api/backend/*` path unstripped; FastAPI routes are unprefixed. A
`StripPrefix` ASGI middleware makes the backend proxy-agnostic. Caught by an actual prod
`curl`, not by "it built."
