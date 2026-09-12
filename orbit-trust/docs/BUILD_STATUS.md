# ORBIT-TRUST BUILD_STATUS

Project: ORBIT-TRUST 2.0 · Target: devx-engine/orbit-trust · Hosting: Vercel ·
Persistence: Supabase · Provider: Groq.

Record PASS / FAIL / BLOCKED / NOT_RUN honestly. Never convert NOT_RUN to PASS.
"Written but not run" is not a passing test. Synthetic fixture results are not
measured customer outcomes.

## Current state
- Application implementation: IN PROGRESS (M0 scaffold).
- Branch: `orbit-trust` (off `main` @ ad4b9e4). Work scoped to `orbit-trust/`.
- Public URL: pending owner Vercel/Supabase/Groq configuration.

## Environment discovered this session
| Item | Found | Spec (doc) | Action |
| --- | --- | --- | --- |
| Python | 3.10.12 (system) + 3.12.14 (uv) | 3.12 (D23) | 3.12 installed via uv; build venv .venv312 |
| Node | 25.8.2 | 22 LTS (D23) | Confirm 22 in CI; local dev works |
| pnpm | 9.15.0 | 10 (D23) | Bump to 10 for web workspace |
| Rust/cargo | 1.98.1 (rustup) | stable (D24) | INSTALLED; maturin 1.15 in venv |
| fastapi/uvicorn/pydantic/numpy/scipy | present | — | Reference oracle + API run now |
| jsonschema | MISSING | needed M1 | Add for schema validation |
| Groq key | ABSENT | required for live (R10) | Spike C + M5 live run BLOCKED |
| Supabase creds | ABSENT | required (D12) | Spike B + M1 remote checks BLOCKED |

## Deployment gate (doc 14) — RESOLVED direction
- The game has its OWN Vercel project: `3d-game` (projectId prj_xEnl1Ee9iuz6VOCmgWSXTi24ESg2,
  org team_ZdcbiBW0YBdbYG0OoG7ubjTe), build `pnpm --filter client build`.
- Therefore ORBIT-TRUST needs a SEPARATE Vercel project, Root Directory `orbit-trust/`.
  Do NOT repoint or change the `3d-game` project. Owner action required to create/link
  the ORBIT-TRUST project (Phase 8 / M0 verify).

## Game preservation (release gate, doc 17)
- Baseline recorded: `docs/game-baseline.txt` (HEAD ad4b9e4, 51 tracked files).
- Pre-existing uncommitted `3d-game/.gitignore` mod is the owner's; left untouched.
- Verify at release: `git ls-tree -r HEAD 3d-game` unchanged.

## Handoff conformance audit (PDF vs implementation)
Confirmed ORBIT_TRUST_IMPLEMENTATION_HANDOFF.pdf is the verbatim render of docs
00-19 (spot-checked; PACKAGE_DOCUMENT_QA confirms full parity). Audited code vs
spec and corrected two deviations:
- doc 06: pc_general now surfaces `numerical_nonconvergence` on a large quadrature
  error instead of silently returning a Pc; evaluate_encounter maps that status.
- doc 05: import_summary now reports accepted / deduplicated / conflicted /
  rejected (+retained unsupported) by running report records through the ledger.
No larger deviations found; implementation tracks the handoff.

## Milestone status
| Milestone | Status | Notes |
| --- | --- | --- |
| M0 deployment path | PARTIAL | Skeleton + reference oracle + FastAPI health/capabilities run. Rust wheel spike DONE (abi3-py312 manylinux_2_34 wheel built, imported, validated). Supabase + Groq spikes BLOCKED (creds). Vercel import-in-function verification pending a project. |
| N1 Rust production core | DONE | orbit_core: projection + GL/periodic-trapezoid polar quadrature with two-grid convergence gate + Rayon batch. Matches Python oracle across T01-T10; wheel + build-manifest in vendor/wheels/. Benchmark (2000 problems): seq-Python 3400ms, seq-Rust 3310ms, parallel-Rust 483ms (6.8x), cached 83ms. |
| M1 contracts/storage | PARTIAL | Strict Pydantic contract; domain validation + import classification; report ledger dedup/conflict/pair (T16-T18); canonical digest. supabase/migrations 0001-0007 authored + APPLIED/seeded on the live project (reachable over the HTTPS Data API; direct Postgres is IPv6-only and unreachable from the build sandbox). In-memory service layer + doc-05 core-loop endpoints now built and tested (see below). Swapping the in-memory store for Supabase RPC calls + JWT auth is the remaining M1 work. |
| M2 scientific core | DONE (logic) | Rust core + Python oracle T01-T10; covariance/precision states (T07-T09); P0-P3 policy + ack floor (T12/T14); assessment engine (findings, evidence-state precedence, material-concern vs review, reopening) T11/T13/T15. Persisted assessment table lands with N2. |
| M3 fleet/comms | PARTIAL | Fleet comparison engine (T25-T26 hero reversal) + communication timing/state machine (T28), both wired as compute-only API endpoints. Bounded chunks / DB leases / resumable batches / benchmark modes BLOCKED (no DB). |
| M4 consequence/reentry | PARTIAL | Decimal expected-loss economics (T29-T30) + reentry exposure with holes/boundary + conditional damage (T31-T33), wired as compute-only endpoints. Reentry cannot alter orbital policy (separate module). |
| M5 agent | PARTIAL | Bounded investigate FALLBACK built: deterministic host-owned AgentSelection (template selection over the assessment's own findings) + host validator (`agent.validate_selection`) that a Groq/ADK proposal must pass. Live Groq/ADK provider call + budgets/quotas BLOCKED on wiring (creds present in .env; provider integration deferred by owner). |
| M6 console | NOT_STARTED | |
| M7 release | NOT_STARTED | |

## Acceptance tests run this session
| ID | Status | Evidence |
| --- | --- | --- |
| T01 (isotropic reference Pc) | PASS | tests/reference/test_numerics.py vs encounter_reference sigma-20/50/200/1000 |
| T02 (zero-miss analytic) | PASS | matches 1-exp(-R^2/2sigma^2) = 0.019801326693244702 |
| T03 (anisotropic geometry+Pc) | PASS | projected mean [35,-12], cov [[900,180],[180,400]], Pc 0.027295519415793158 |
| T04 (rotation invariance) | PASS | orthogonal rotation of all states -> Pc invariant |
| T05 (primary/secondary swap) | PASS | same Pc |
| T06 (translation invariance) | PASS | common shift -> relative result unchanged |
| T07 (invalid covariance / schema) | PASS | negative-variance -> domain_invalid_covariance; missing-frame / pc>1 -> schema_422; same-object -> domain_pair_mismatch |
| T10 (radius monotonic) | PASS | pc non-decreasing in R |
| T08 (unsupported states) | PASS | low relative speed / tca outside interval / invalid covariance -> unsupported, pc null |
| T09 (precision) | PASS | underflow -> below_computable_precision, no definitive zero |
| T12 (deadline tiers) | PASS | +40m/2h/unknown/exact/passed -> P1/P2/P1/P1/P0 |
| T14 (ack floor holds) | PASS | downgrade after urgent held until latest-version ack |
| T16 (dedup / out-of-order) | PASS | identical retry dedup; older revision preserves current |
| T17 (source conflict) | PASS | same revision + different body -> retained conflict |
| T18 (event-pair conflict) | PASS | reused event_key with different pair -> reject_association |
| T25 (A-B fix creates A-C) | PASS | candidate-one blocked; every pair's pc/evidence visible |
| T26 (candidate dispositions) | PASS | baseline+one blocked, two passes; preferred=candidate-two; pc matches fixture |
| T28 (comms simulation) | PASS | scripted authorize/send/ack/execute; reject_send / expired / failed / reject_auth / timing_unknown |
| T29 (reference economics) | PASS | 100000 before, 1000 after, 99000 reduction, 79000 net (Decimal) |
| T30 (economics guards) | PASS | mixed currency / unknown prob -> unavailable; negative net -21000 shown, not clipped |
| T31 (footprint holes/boundary) | PASS | pop 150, value INR 1,500,000, damage INR 150,000; hole excluded, boundary included |
| T32 (alt footprint + geometry rejects) | PASS | alt footprint exposes pop-outside/asset-D (INR 100,000); rejects unordered window / dateline / latitude>85 / unclosed ring / self-intersection / uncontained hole / >1000 points |
| T33 (missing vulnerability) | PASS | exposure available, damage unavailable_missing_vulnerability |
| positive import | PASS | all 10 fixture inputs accepted through Record union |
| Rust core vs oracle (T01-T10) | PASS | orbit_core.project_and_pc matches orbit_trust.numerics + fixtures within 1e-6 rel; batch==sequential; error paths raise (.venv312) |
| T11 (uncertainty vs conflict) | PASS | sigma-200 reviews (risk, usable evidence); sigma-1000 monitors; sigma-1000 + missing obs still reviews without asserting high Pc |
| T13 (cosmetic vs material) | PASS | DEADLINE_UNKNOWN (non-material) no review; MANEUVER_CONTEXT_UNKNOWN (material) reviews |
| T15 (reopen closed) | PASS | new material evidence -> reviewing + ack required; duplicate/cosmetic -> unchanged |
| all others | NOT_RUN | later milestones (credential-gated) |

## Backend service layer (this session)
Built the doc-05 workspace core loop as a self-contained layer, behind seams so
Supabase/Groq/Vercel wiring drops in without touching callers (owner deferred
those integrations). New modules: `store.py` (in-memory, workspace-scoped,
global lock — the only stateful component; the Supabase store replaces it),
`service.py` (domain ops), `agent.py` (investigate fallback + host validator).
Endpoints added: POST /workspaces/demo, POST /imports, GET /cases,
GET /cases/{id}, GET /cases/{id}/reports, POST /cases/{id}/assess,
POST /cases/{id}/actions, POST /cases/{id}/investigate,
POST /workspaces/{id}/reset, GET /activity. Doc-05 error shape + demo identity
(`X-Demo-User`/`X-Workspace-Id`, fail-closed) + Idempotency-Key.
- Acceptance: `tests/reference/test_service.py` PASS — create/import/dedup,
  workspace + case revision guards (409), queue sort + QUEUE_CHANGED cursor,
  workflow state machine + invalid-transition 409, latest-version ack floor,
  partial-batch import (bad record rejected, summary preserved), idempotent
  replay, cross-identity isolation, investigate fallback validated.
- Deferred (chosen scope, doc 13 cut order): satellites CRUD,
  operations/continue DB leases + resumable batches, exports (json/markdown),
  and the real Supabase RPC/JWT + live Groq + Vercel env wiring.

## Next executable ticket
Full forward plan with per-phase gates and acceptance: see `docs/NEXT_PHASE.md`.
Remaining no-creds work: M2 Rust port (needs local rustup+maturin) validated
against orbit_trust.numerics; M3 bounded-chunk/lease semantics as pure logic;
polygon geometry rejects (dateline/self-intersection, T32 negative side). Then
the credential-gated milestones: M1 Supabase RPCs/seed + live auth/isolation,
M5 bounded ADK/Groq agent + fallback, M6 Next.js console, M7 release. These stay
BLOCKED until owner supplies Supabase + Groq creds and a dedicated ORBIT-TRUST
Vercel project, and the Rust toolchain + Python 3.12 are installed locally.

## Credential gates blocking progress
1. Rust toolchain (rustup + maturin) — local install, no owner needed.
2. Python 3.12 — local install.
3. Supabase project URL + keys — owner.
4. Groq API key — owner.
5. Dedicated ORBIT-TRUST Vercel project (Root Directory orbit-trust/) — owner.
