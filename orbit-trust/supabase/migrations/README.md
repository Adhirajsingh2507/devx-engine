# Supabase migrations (doc 19)

**NOT YET APPLIED** — no Supabase project/credentials in this session. These are
reviewed artifacts to `supabase db push` once the owner's project exists, then
verified with the doc-19 security acceptance tests against the real Data API.

Order (doc 19): enums/base tables → FKs/indexes → membership helper/RLS/grants →
domain RPCs → synthetic template seed → optional retention maintenance. Avoid
destructive renames/drops during a release; use additive fields.

| File | Milestone | Contents | Status |
| --- | --- | --- | --- |
| 0001_core.sql | M1 | workspaces, members, satellites(+revisions), cases, reports, source_conflicts, assessments, review_actions, audit_events, idempotency, quota/lease/seed internals; indexes; RLS + `is_member` helper + read policies | written, unapplied |
| 0002_fleet_reentry.sql | M3/M4 | candidate_sets, comparisons, operations, operation_items, economic_scenarios, reentry_scenarios, communication_packets; RLS + read policies | written, unapplied |
| 0003_rpcs.sql | M1 | server-only RPCs: create_demo_workspace, import_commit, save_review_action, advance_demo_clock (full bodies); claim/commit/finalize/reset (signatures + invariant contracts, bodies finished live in N2) | written, unapplied |
| 0004_seed.sql | M1 | synthetic public_seed_templates default demo seed (doc 11 recipe) | written, unapplied |

All four are authored but UNVERIFIED — they need `supabase db push` against a
real project and the doc-19 security acceptance tests before use. The
operation-lease RPC bodies are intentionally left as contracts (not fabricated
untested) because they depend on runtime lease timing.

All domain writes go through the 0003 RPCs (SECURITY DEFINER, membership +
role + dependency checks); no generic arbitrary-SQL RPC. The service key never
reaches the browser.
