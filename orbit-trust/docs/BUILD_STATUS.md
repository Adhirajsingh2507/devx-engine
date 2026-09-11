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
| Python | 3.10.12 | 3.12 (D23) | Install 3.12 before wheel/abi3 + provider spikes |
| Node | 25.8.2 | 22 LTS (D23) | Confirm 22 in CI; local dev works |
| pnpm | 9.15.0 | 10 (D23) | Bump to 10 for web workspace |
| Rust/cargo/maturin | MISSING | stable (D24) | Install toolchain to build native wheel |
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
| M0 deployment path | PARTIAL | Skeleton + reference oracle + FastAPI health/capabilities run. Rust wheel + Supabase + Groq spikes BLOCKED (toolchain/creds). |
| M1 contracts/storage | PARTIAL | Strict Pydantic contract; domain validation + import classification; report ledger dedup/conflict/pair (T16-T18); canonical digest. supabase/migrations/0001_core.sql written (UNAPPLIED - no creds). RPCs/seed + live auth/isolation BLOCKED. |
| M2 scientific core | PARTIAL | Python oracle passes T01-T06/T10; covariance validity + unsupported/precision states (T07-T09); deadline P0-P3 policy + ack floor (T12/T14). Rust production port + T11/T13/T15 pending. |
| M3 fleet/comms | PARTIAL | Fleet comparison engine (T25-T26 hero reversal) + communication timing/state machine (T28), both wired as compute-only API endpoints. Bounded chunks / DB leases / resumable batches / benchmark modes BLOCKED (no DB). |
| M4 consequence/reentry | PARTIAL | Decimal expected-loss economics (T29-T30) + reentry exposure with holes/boundary + conditional damage (T31-T33), wired as compute-only endpoints. Reentry cannot alter orbital policy (separate module). |
| M5 agent | NOT_STARTED | |
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
| T32 (alt footprint) | PASS | alternative footprint exposes pop-outside/asset-D, INR 100,000 |
| T33 (missing vulnerability) | PASS | exposure available, damage unavailable_missing_vulnerability |
| positive import | PASS | all 10 fixture inputs accepted through Record union |
| all others | NOT_RUN | later milestones |

## Next executable ticket
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
