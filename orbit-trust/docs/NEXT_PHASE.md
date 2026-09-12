# ORBIT-TRUST — next phase plan

The deterministic core (M0–M4 compute logic) is implemented and tested. What
remains is (a) one unblocked-but-toolchain-gated item and (b) the
credential-gated milestones. Each ticket below lists its unblock condition, the
work, and the acceptance evidence, so it can start the moment its gate lifts.

## Gate inventory
| Gate | Needed for | How to lift |
| --- | --- | --- |
| Rust toolchain + Python 3.12 (local) | M2 Rust port, M0 wheel spike | `rustup` + `pip install maturin`; install Python 3.12 |
| Supabase project + keys | M1 storage/auth, M0 DB spike | owner creates project; set env (doc 14) |
| Groq API key | M5 live agent, M0 provider spike | owner supplies `GROQ_API_KEY` |
| Dedicated ORBIT-TRUST Vercel project (Root Dir `orbit-trust/`) | M0/M7 deploy | owner creates project separate from `3d-game` |

---

## Phase N1 — Rust production core (gate: local toolchain)
Port `orbit_trust.numerics` into `crates/orbit_core` and validate against the
Python oracle (never self-oracle, doc 12).
- Tickets: encounter-plane projection; two-grid polar quadrature (64x128 vs
  128x256, tol max(1e-12,1e-7·Pc), 256x512 fallback, else `numerical_nonconvergence`);
  Cholesky + log-normalization; covariance validity; Rayon pair batch for fleet.
- Build a manylinux wheel (`maturin`, pinned), record sha256 + ABI + Rust version
  in `vendor/wheels/build-manifest.json`. Install it and flip
  `capabilities.rust_core_available` to true.
- Acceptance: T01–T10 pass through the Rust path with results matching the Python
  oracle within tolerance; benchmark sequential-ref / sequential-Rust /
  parallel-Rust / cached with identical work (doc 12).

## Phase N2 — Supabase storage + auth (gate: Supabase creds)
Turn the pure ledger/validation logic into the atomic transactional layer.
- Migrations: finish `0002_fleet_reentry.sql` (candidate_sets, comparisons,
  operations, operation_items, economic_scenarios, reentry_scenarios,
  communication_packets), `0003_rpcs.sql` (create/seed workspace, import batch,
  save action, claim/commit operation, finalize assessment/packet, reset — all
  SECURITY DEFINER, membership+role+dependency checks, no arbitrary-SQL RPC),
  `0004_seed.sql` (default demo seed, doc 11).
- Server: JWT verify (issuer/audience/expiry/JWKS, fail closed); FastAPI domain
  endpoints (doc 05) calling the RPCs; GitHub OAuth + anonymous demo identity;
  idempotency records; demo-clock advance operation.
- Wire the existing compute cores (fleet/economics/reentry/comms) behind
  workspace-scoped endpoints with expected_revision + leases.
- Acceptance: T16–T24, T27, T38 against real Supabase Auth/Data API — two-account
  isolation, forged actor, guessed UUID, expired JWT, direct-insert denied,
  idempotent retry, interrupted-operation resume.

## Phase N3 — Bounded ADK/Groq agent (gate: Groq key + N2)
- ADK deterministic `CaseReviewWorkflow`; Investigator (≤3 allowlisted
  version-bound tools, ID-only args, 4 KiB result cap) + tool-free
  PacketFormatter returning the typed `AgentSelection`.
- Host validator: every cited finding/fact exists in the snapshot, templates
  match facts, required findings included; render authoritative text from
  template codes only. Deterministic labeled fallback on 429/timeout/malformed/
  missing-key; stale-on-new-evidence.
- Budgets/quotas via DB reservations (doc 09): ≤3 provider calls +1 shared retry,
  30 s wall, token caps, run/day caps. Freeze the 50-item eval set before measuring.
- Acceptance: T34–T37, one real Groq run in the deployed app, eval counts +
  token/latency report. Adversarial_cases.json: injection ignored, invented/
  omitted finding fixed, forbidden tools denied.

## Phase N4 — Mission console (gate: N2; Groq optional)
- Next.js static export, fixed routes (`/queue/`, `/case/`, `/fleet/`,
  `/reentry/`, …), dark-nav/light-panel system (doc 10). Server-paginated queue
  with pinned urgent strip; case evidence/timeline; fleet matrix; comms status;
  economics; separate reentry tab with permanent synthetic banner; activity;
  settings/export. Every screen: loading/empty/error/stale/partial.
- Deterministic results render before any model response. Accessibility:
  semantic tables, keyboard dialogs, visible focus, no color-only meaning,
  plot/map text alternatives, reduced-motion.
- Acceptance: T19–T21, T38–T40 — screenshots at 1440/768/390 via Playwright,
  keyboard review, fresh-session persistence, zero inaccessible urgent cases.

## Phase N5 — Release (gate: all above + Vercel project)
- Run applicable suite against the release candidate; measure public cold/warm
  latency + bundle size. Verify `3d-game/` unchanged vs `docs/game-baseline.txt`
  and its deployment intact. Secrets/license/data-notice review.
- Promote via the ORBIT-TRUST Vercel project after preview verification;
  smoke-test from a fresh non-team browser. Fill doc-17 traceability
  (PASS/FAIL/BLOCKED/NOT_RUN), 3-min demo recording.
- Acceptance: stable public URL, release commit, test/benchmark evidence,
  reproducible local instructions, explicit limitations.

## Cut order if constrained (doc 13)
Keep: scientific audit, core queue, three-object candidate reversal, one genuine
bounded Groq run, persistence, public URL. Drop first: animation, custom map
tiles, dashboard personalization, large benchmark sizes, report styling. Never
substitute fixture constants for Rust or a fabricated trace for the agent.
