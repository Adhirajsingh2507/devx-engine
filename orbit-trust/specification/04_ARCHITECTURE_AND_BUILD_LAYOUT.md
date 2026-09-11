# Architecture and application boundaries

## Confirmed deployment

Implement in orbit-trust/ within the existing Adhirajsingh2507/devx-engine repository. The owner reports an existing Vercel Git deployment connection. The existing 3d-game/ app is important for future implementation: preserve its source, assets, configuration and any deployment, alongside the toolkit content. Do not remove or repurpose it. The public ORBIT-TRUST application combines a static Next.js export served by Vercel's CDN and one FastAPI Python function on the same origin. Supabase stores persistent accounts, cases and calculation provenance. Groq supplies model inference.

Use fixed web routes /, /queue/, /case/, /fleet/, /satellites/, /satellite/, /reentry/, /activity/, /settings/, /auth/callback/ and /about/. IDs are query parameters. The static shell contains no user-specific rendered content: all private state is fetched after client authentication. Never cache personalized API responses on the CDN or build a static page with user metadata.

Build Next.js with static export, local fonts and SVG/Canvas illustrations. No server actions, runtime SSR or ungenerated dynamic pages. Copy the export to the FastAPI project's public/ tree during build. The M0 preview verifies route precedence, trailing slashes and API 404s. If current Vercel routing requires explicit mappings, generate them from the fixed page list, not an unconditional catch-all returning HTML for unknown API calls. [^04-S12][^04-S14]

## Logical flow

Import -> canonical validation -> immutable report ledger -> deterministic checks -> supported Rust calculations -> policy assessment -> immediate queue.

On request, ADK investigates a saved assessment snapshot. Tools read version-bound records or request bounded scenario calculations. A separate formatter selects evidence and template codes. A host validator assembles the packet. New report, policy or candidate revisions invalidate dependent results.

Fleet comparison, reentry exposure and economics are distinct bounded operations. They share provenance and presentation conventions, not one physics model. Financial tools never backfill missing physics.

## New application layout

| Directory within orbit-trust | Responsibility |
| --- | --- |
| apps/web | Next.js UI, API client and accessible components |
| orbit_trust | Python API, domain models, persistence, policy and ADK |
| crates/orbit_core | Math, pair batches and PyO3 bindings |
| vendor/wheels | Reproducible Linux-compatible Rust wheel and build manifest |
| contracts | Canonical schema and generated API snapshot |
| data/fixtures | Original synthetic bundles and expected outputs |
| supabase/migrations | Tables, grants, RLS and atomic domain operations |
| tests/reference and tests/e2e | Independent numerical, workflow and browser checks |
| docs and deploy | Specification, measured evidence and Vercel runbook |

Root app.py exports the FastAPI instance. pyproject.toml, dependency locks and vercel.json belong under orbit-trust, the designated Vercel project Root Directory. Use one Python package, one Rust crate and one web application. No distributed worker platform, vector database, A2A service mesh or general agent marketplace.

## Serverless execution

No in-memory queue, process-local session ledger, SQLite or persistent background thread is authoritative hosted state. Vercel invocations can terminate or run in separate instances. Complete operations inside a bounded request or use explicit resumable batches with Supabase checkpoints. Polling status does not run a hidden worker.

Use a 45-second application request budget below a verified configured Vercel duration. Reserve 5 seconds for persistence. Numerical work has a 10-second batch budget; Groq has the tighter budgets in document 09. Persist results before returning success. On interruption, a running operation's lease expires and a new request can mark it interrupted and retry idempotently.

For a maximum 20-object, four-candidate comparison, continuation requests process at most 25 pair/candidate jobs or stop earlier at budget. Return progress and a continuation cursor. Closing the browser pauses unstarted work; reopening offers Resume. The default three-object demo should fit one request, subject to measurement.

Enforce one operation per workspace and a small global Groq concurrency limit through atomic database leases, not Python globals. A lease lasts 60 seconds; final writes require its current token and the unchanged input revision. Duplicate requests cannot publish competing results. Rust defaults to one worker publicly; local benchmarks can use min(4, available cores). Release the GIL during numerical batches.

## Persistence and authorization

Supabase Postgres is authoritative locally and publicly; offline integration testing uses its local development stack. Reads use the verified user JWT and RLS. Domain mutation endpoints validate JWT signature, issuer, audience and expiry plus workspace membership, then call restricted server-only transactional RPCs. The service credential never enters the browser; RLS bypass never replaces membership checks.

Revision insertion, current-pointer updates, invalidation and audit events are atomic. Seeds are immutable public synthetic data; changes belong to a workspace. Use uniqueness constraints for source identity and idempotency keys. Document 19 defines tables, grants and RPC responsibilities.

## Identity and result binding

Results identify schema version, workspace/case, input reports, raw and normalized hashes, policy/scenario/method versions, time and findings. Cache keys include catalogue, candidate, economic and exposure revisions where relevant. Anonymous visitors never share mutable cases. Shared caches contain only public synthetic mathematical inputs, without names, notes or credentials.

Normalize digests over sorted-key compact UTF-8 JSON with finite numbers and canonical UTC timestamps. Keep original-file SHA-256 separately. Do not assume different serializers or equivalent numeric spellings hash identically without canonicalization tests.

## Frontend updates

Poll every 3 seconds while an operation runs, every 15 seconds for the active queue, and stop in hidden tabs. Return workspace revision and activity sequence; fetch deltas or a full snapshot after cursor expiry. SSE and WebSockets are not required. This replaces the earlier continuously running service design.

Publish the queue before model work. Host facts and decisions cannot be overwritten by generated prose. New evidence marks explanations stale. Revision-protected edits return 409 instead of overwriting newer data. Demo clock advances affect policy; authentication and leases always use wall time.

## Packaging and backup

Use Vercel's Python Functions runtime, not Edge. Build the Rust Linux wheel reproducibly and verify imports in a preview before dependent features. Keep training packages and large archives out of the production function bundle. Run the same API locally with a platform-compatible extension. Local replay is a backup, not proof of the required public release. [^04-S12][^04-S13]

## Source notes

[^04-S12]: Vercel, [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), refreshed 11 September 2026.

[^04-S13]: Vercel, [Python runtime](https://vercel.com/docs/functions/runtimes/python) and [Function limitations](https://vercel.com/docs/functions/limitations).

[^04-S14]: Next.js, [Static exports](https://nextjs.org/docs/app/guides/static-exports).
