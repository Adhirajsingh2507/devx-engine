# Supabase migrations (doc 19)

**0001–0006 APPLIED** to the live project; **0007–0008 written + verified on a
scratch Postgres, PENDING apply** (apply them in the SQL Editor, in order). Until
0007/0008 land, `commit_chunk` errors on the ttl cast and any conflict
(`revision_conflict`) hangs the request. Verified with the doc-19 security + lease
acceptance tests against the real Data API. Direct `psql`/`supabase db push` is
not reachable from the build machine (network blocks Postgres ports; direct host
is IPv6-only), so migrations are applied via the **Supabase SQL Editor** and
verified over HTTPS (PostgREST/Auth) and on a scratch Postgres.

Order (doc 19): enums/base tables → FKs/indexes → membership helper/RLS/grants →
domain RPCs → seed → lease RPCs → hardening. Applied migrations are immutable;
fixes land as a new additive migration (never edit an applied file).

| File | Milestone | Contents | Status |
| --- | --- | --- | --- |
| 0001_core.sql | M1 | workspaces, members, satellites(+revisions), cases, reports, source_conflicts, assessments, review_actions, audit_events, idempotency, quota/lease/seed internals; indexes; RLS + `is_member` helper + read policies | applied |
| 0002_fleet_reentry.sql | M3/M4 | candidate_sets, comparisons, operations, operation_items, economic_scenarios, reentry_scenarios, communication_packets; RLS + read policies | applied |
| 0003_rpcs.sql | M1 | server-only RPCs: create_demo_workspace, import_commit, save_review_action, advance_demo_clock (full bodies); lease RPC signatures/contracts | applied |
| 0004_seed.sql | M1 | synthetic public_seed_templates default demo seed (doc 11) | applied |
| 0005_lock_rpc_execute.sql | N2 | revoke EXECUTE on the 0003 write RPCs from anon+authenticated (Supabase default-grants them; REVOKE FROM public alone is insufficient). Fixes the SEC-9/10 direct-RPC finding. | applied |
| 0006_lease_rpcs.sql | N2 | operation-lease RPC bodies: claim_operation, commit_chunk, finalize_result, reset_workspace; execute revoked from anon+authenticated, granted to service_role | applied |
| 0007_lease_fixes.sql | N2 | lease fixes: ttl_seconds stored/read as int (was `120.000000`→int cast error); lease expiry marks interrupted and RETURNS `lease_expired` instead of raising (a raise rolled back the interrupted mark) | **pending apply** |
| 0008_conflict_status.sql | N2 | replace SQLSTATE 40001 with PT409 (HTTP 409) in import_commit, save_review_action, reset_workspace. 40001 (serialization_failure) is AUTO-RETRIED by PostgREST, so a deterministic conflict hung the request until timeout. | **pending apply** |

## Security model (verified live)
- Browser reads use the user JWT + RLS (`is_member`). All domain writes go through
  the SECURITY DEFINER RPCs, which re-check membership/role. No generic
  arbitrary-SQL RPC. Execute on every write RPC is service_role-only.
- N2 acceptance: 13/13 Data-API isolation tests pass **live** (cross-tenant read
  denial, direct-write denial, forged actor/owner, guessed UUID, server-only
  tables, forged-RPC denial, JWT fail-closed). Lease lifecycle (expiry,
  interrupted, idempotent retry, concurrent claims/commits, stale-digest,
  stale-on-finalize, reset guards + isolation) passes on scratch Postgres;
  live re-run is pending 0007/0008 apply.

## Error-code convention (doc 19 + PostgREST)
Application conflicts must NOT use 40001/40P01 — PostgREST auto-retries those and
a deterministic conflict will hang. Use `PT409` (→ HTTP 409). Lease/lock
contention uses 55P03; not-found P0002; auth 42501.
