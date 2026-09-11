# 11 — DevOps & Deployment (and the real bugs we hit)

**Files:** `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`,
`vercel.json`, `.github/workflows/{ci,deploy}.yml`, `scripts/validate-terrasight.sh`,
`DEPLOY.md`.

---

## 11.1 From zero: the words

- **Docker / container** — package an app + its exact dependencies into an image that
  runs identically anywhere. A `Dockerfile` is the recipe.
- **CI (Continuous Integration)** — automatically run tests on every push/PR so broken
  code can't merge. Ours is **GitHub Actions** (`ci.yml`).
- **CD (Continuous Deployment)** — automatically deploy. Ours is a *guarded, manual*
  workflow (`deploy.yml`).
- **Vercel** — a hosting platform that builds and serves web apps (great for Next.js;
  also runs Python functions).

## 11.2 Two deploy paths

**Vercel (recommended)** — one project, the **`services` framework**: the root
`vercel.json` declares two services in one project — `frontend` (Next.js) and `backend`
(FastAPI `app.main:app`) — plus a rewrite so `/api/backend/*` routes to the backend
service (same-origin, no separate domain). Set `SUPABASE_URL/KEY` on the project for live
data; unset → mock.

**Docker (self-host)** — `docker-compose up` runs two containers:
- **backend image is lean**: installs `requirements.txt` **only** (FastAPI/uvicorn/
  supabase), *never* `requirements-cv.txt` (numpy/opencv) — because `app.main` never
  imports the perception pipeline. Verified: no numpy/opencv/torch in the 287 MB image.
- **frontend image**: multi-stage Next.js **standalone** build (lean runtime), sets
  `NEXT_OUTPUT=standalone`, receives only the public `NEXT_PUBLIC_API_URL`.

## 11.3 The validation gate (`validate-terrasight.sh`)

One script, the single source of truth, run locally *and* in CI. It runs: Python syntax,
imports, the scoring self-check, the **safety regression suite**, every pipeline stage
self-check, fixtures + end-to-end pipeline, the DB mock-fallback test, the dataset
validator, eval metrics, edge budget + quantization, the **API contract shape check**,
the frontend `next build`, and a **git-secret grep** (fails if a service-role key is
committed). `ci.yml` just installs deps and runs this script on every push/PR to `main`.
**One gate, everywhere** — you can't merge red.

## 11.4 Security posture
- **No committed secrets** — the service-role key lives only in backend env, never in
  `NEXT_PUBLIC_*`, never in the bundle; CI greps for it.
- **RLS**: public read, backend-write via service-role.
- **CORS** is currently `*` (fine for a public read API; tighten to the frontend origin
  for production).

## 11.5 The real bugs we hit (this is the gold — tell these stories)

Deployment taught the lesson that **"it builds" ≠ "it works."** Four real bugs, each a
good story:

1. **`rootDirectory` in `vercel.json` → schema error.** An earlier "fix" put
   `{"rootDirectory":"frontend"}` in `vercel.json`. Vercel rejects it — `rootDirectory`
   is a *project setting*, not a valid `vercel.json` key. **Lesson:** verify config
   against real docs, and *actually deploy* to catch it.
2. **`output:"standalone"` broke the Vercel build.** It was added for the Docker image
   ("no effect on Vercel" — wrong). Standalone relocates a build-trace file Vercel's
   pipeline expects → `ENOENT ... next-server.js.nft.json`. **Fix:** gate it behind
   `NEXT_OUTPUT=standalone` (only the Dockerfile sets it), so Docker keeps standalone and
   Vercel doesn't. **Lesson:** a setting that helps one target can break another.
3. **The `services` schema was correct all along.** The project's *framework* is
   `services`, so the original `services` `vercel.json` was right; the two-project rewrite
   was a misdiagnosis (couldn't reach the docs, guessed). Restored it. **Lesson:** the
   platform's *configured framework* dictates the config; check it before "fixing."
4. **The prod backend 404'd on every call** (`{"detail":"Not Found"}` = FastAPI running
   but no route). Vercel's `services` rewrite forwards the *full* `/api/backend/*` path;
   FastAPI routes are unprefixed; local Next.js *strips* the prefix, hiding it. **Fix:**
   a `StripPrefix` ASGI middleware → proxy-agnostic backend (see `08`). **Lesson:**
   local-dev and prod had different rewriting behaviour; only a real prod `curl` found it.

Then: **Deployment Protection** (Vercel Authentication / SSO) was on, so the public URL
returned 302 (auth wall). Disabled via the Vercel API → the site is now public, and all
five backend endpoints were re-verified live against the frozen contract.

## 11.6 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| **One gate script** run locally + in CI | Identical checks everywhere; no "works on my machine" | A monolithic script (vs many small CI steps) |
| **Lean backend image** (no CV deps) | Fast cold start, small, cheap; API only *serves* | Real CV can't run in the deployed function |
| Vercel **`services`** (one project) | Same-origin `/api/backend`, no CORS/URL wiring for the frontend | Tied to a specific (niche) Vercel feature; finicky routing |
| **Guarded manual** CD (`deploy.yml`) | Never fires an unwanted deploy; no-ops without a token | Not fully automatic (you trigger prod) |
| `StripPrefix` middleware | Backend works behind any proxy, no contract change | A little ASGI plumbing |

## 11.7 Alternatives
- **Two separate Vercel projects** (frontend + Python backend) — the more common
  monorepo pattern; simpler routing semantics, but two projects + an explicit
  `NEXT_PUBLIC_API_URL`.
- **Kubernetes / a VM** — full control, needed at real scale; heavy for a hackathon.
- **A dedicated FastAPI host (Fly.io/Render) + static frontend** — clean separation;
  more moving parts.

## 11.8 Q&A
**Q: How do you stop broken code merging?** The `validate-terrasight.sh` gate runs in
GitHub Actions on every PR — syntax, safety regression, contract shapes, frontend build,
secret grep. Red = no merge.

**Q: Why is the deployed backend so small?** It installs `requirements.txt` only — the
API just *serves* results; the heavy CV (numpy/opencv) is offline/rover tooling, never in
the serverless function. Verified: no CV deps in the image.

**Q: Tell me about a deployment bug you fixed.** (Pick one from 11.5 — the `StripPrefix`
or the `output:standalone` one are the best.) The meta-lesson: *it builds ≠ it works*; we
only caught the prod 404 by curling the live API, not by a green build.

**Q: Are there secrets in the repo?** No — CI greps for a committed service-role key, it
lives only in backend env, and it never reaches the frontend.
