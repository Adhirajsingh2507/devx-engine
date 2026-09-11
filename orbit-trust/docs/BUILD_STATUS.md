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

## Milestone status
| Milestone | Status | Notes |
| --- | --- | --- |
| M0 deployment path | PARTIAL | Skeleton + reference oracle + FastAPI health/capabilities run. Rust wheel + Supabase + Groq spikes BLOCKED (toolchain/creds). |
| M1 contracts/storage | NOT_STARTED | Schema + fixtures copied into repo. |
| M2 scientific core | PARTIAL | Independent Python oracle passes T01-T03/T02/T10; Rust production path + full policy pending. |
| M3 fleet/comms | NOT_STARTED | |
| M4 consequence/reentry | NOT_STARTED | |
| M5 agent | NOT_STARTED | |
| M6 console | NOT_STARTED | |
| M7 release | NOT_STARTED | |

## Acceptance tests run this session
| ID | Status | Evidence |
| --- | --- | --- |
| T01 (isotropic reference Pc) | PASS | tests/reference/test_numerics.py vs encounter_reference sigma-20/50/200/1000 |
| T02 (zero-miss analytic) | PASS | matches 1-exp(-R^2/2sigma^2) = 0.019801326693244702 |
| T03 (anisotropic geometry+Pc) | PASS | projected mean [35,-12], cov [[900,180],[180,400]], Pc 0.027295519415793158 |
| T10 (radius monotonic) | PASS | pc non-decreasing in R |
| all others | NOT_RUN | later milestones |

## Next executable ticket
M2 continuation (no creds needed): port projection + polar-quadrature to the Rust
core once the toolchain is installed, add covariance-validity/frame checks
(T04-T09) and the deadline P0-P3 policy (T11-T15). In parallel, M1 needs
jsonschema + Pydantic models generated from `contracts/core.schema.json`.

## Credential gates blocking progress
1. Rust toolchain (rustup + maturin) — local install, no owner needed.
2. Python 3.12 — local install.
3. Supabase project URL + keys — owner.
4. Groq API key — owner.
5. Dedicated ORBIT-TRUST Vercel project (Root Directory orbit-trust/) — owner.
