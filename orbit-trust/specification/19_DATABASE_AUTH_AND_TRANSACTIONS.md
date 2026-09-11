# Supabase database, authorization and transaction specification

## Identity and permissions

Every private record belongs to a workspace. Membership roles are owner, analyst and viewer. Version 2.0 creates one owner membership and one active demo workspace per authenticated identity; team invitation is deferred. An analyst may import, edit metadata and record reviews; a viewer may read/export; only an owner may reset/delete the workspace or change settings. Anonymous demo owners have the same within-workspace operations but lower quotas and limited retention.

Validate Supabase JWT signatures against the project's supported signing configuration. Check issuer, audience, expiry and authenticated subject; cache JWKS with bounded refresh and fail closed on unknown/invalid keys. Use the configured server verification method for legacy signing configurations rather than decoding an unsigned token. Identity comes from the verified token, never an actor_id supplied in JSON.

Client reads use the user JWT with row-level security. All domain writes go through FastAPI, which verifies identity and membership, then invokes narrow server-only transactional functions. A service credential bypasses normal RLS; each function must independently enforce the verified actor's membership and permitted action. Revoke function execution from PUBLIC, anon and authenticated roles unless explicitly designated as a safe read helper. Never expose a generic arbitrary-SQL RPC. [^19-S18]

## Relational inventory

Use UUID primary keys, timestamptz for UTC times, bigint revision/sequence counters, explicit status CHECK constraints and jsonb for bounded validated snapshots. Use numeric or decimal-string fields for money, not float columns. Every child relationship uses a composite workspace_id + entity_id foreign key where practical to prevent cross-workspace references even inside a server bug.

| Table | Keys and important fields |
| --- | --- |
| workspaces | id, owner_id, mode, data_revision, queue_revision, next_audit_sequence, demo_clock, created_at, last_active_at |
| workspace_members | workspace_id + user_id unique, role |
| satellites | workspace_id + id, current_revision, archived flag |
| satellite_revisions | workspace_id + satellite_id + revision unique, immutable metadata, author, created_at |
| cases | workspace_id + id, event_key unique per workspace, ordered pair identity, current_revision, workflow_state, assigned_member, latest_assessment_id, urgent_floor |
| reports | workspace_id + id, case_id, source_name, source_revision, raw_digest, normalized_digest, source_created_at, received_at, raw_json, normalized_json |
| source_conflicts | workspace_id, case_id, competing report IDs, state and review action reference |
| assessments | workspace_id + id, case_id, input_revision, input_digest, method/policy versions, evidence_state, proposed_urgency, effective_urgency, deadline, immutable facts/findings, method_status |
| candidate_sets | workspace_id + id + revision, catalogue revision, interval, canonical snapshot and digest |
| comparisons | workspace_id + id, candidate_set/revision, input_digest, status, complete pair result snapshot and coverage |
| economic_scenarios | workspace_id + id + revision, probability references, decimal inputs, currency, immutable result/dependencies |
| reentry_scenarios | workspace_id + id + revision, footprint/layer snapshots, assumptions, immutable result/dependencies |
| operations | workspace_id + id, kind, input_revision/digest, state, lease_token, lease_expires_at, cursor, progress, result_id and error code |
| operation_items | workspace_id + operation_id + item_key unique, input_digest, status, result snapshot |
| agent_runs | workspace_id + id, assessment_id, input_digest, model/prompt versions, status, bounded trace, usage, validation and packet selection |
| review_actions | workspace_id + id, case_id, actor_id, acknowledged_assessment_id, expected_revision, action, rationale, created_at |
| communication_packets | workspace_id + id, candidate/comparison bindings, simulation state, contact assumptions and acknowledgement/execution event references |
| audit_events | workspace_id + sequence unique, actor_id, entity/revision, event type, redacted summary and created_at |
| idempotency_records | workspace_id + actor_id + route + key unique, payload digest, status, result reference, expires_at |
| quota_buckets | scope + subject + wall-time window unique, reserved/consumed counters and expiry; server-only |
| global_leases | named capacity slot unique, holder token, expiry; server-only |
| public_seed_templates | seed_id + version, immutable synthetic payload/digest; read-only public metadata |

Report uniqueness is workspace + case + source_name + source_revision + raw_digest. A different digest with the same source revision is permitted as a retained conflict; a uniqueness rule on source revision alone would incorrectly discard that evidence. Ordered pair identity is canonicalized for grouping while primary/secondary roles remain preserved in each report.

Index queue reads on workspace/effective urgency/deadline/case ID; reports on workspace/case/source/created time; operations on workspace/status/lease expiry; audit on workspace/sequence; assessments on workspace/input digest/method/policy. Query counts over the entire filtered dataset, not the returned page. Store immutable derived results and atomically update current pointers only when their dependencies remain current.

## RLS and grants matrix

| Object | Browser read | Browser direct write | Server transaction |
| --- | --- | --- | --- |
| Workspace/member rows | Own membership permits scoped read | Denied | Validated creation/settings only |
| User data and derived tables | Membership-scoped | Denied | Role plus dependency checks |
| Audit/review history | Membership-scoped | Denied | Append through domain operation |
| Quota/global lease/idempotency internals | Denied | Denied | Narrow server-only operations |
| Public synthetic template metadata | Read permitted | Denied | Deployment/maintenance only |

Enable RLS on exposed user tables and revoke unnecessary table grants. A protected membership helper may use SECURITY DEFINER to avoid policy recursion only with a fixed safe search_path, qualified identifiers, no dynamic SQL, least privileges and explicit execute grants. Test the helper with users having no membership. Do not use user-editable profile metadata to grant roles.

Unauthenticated requests cannot create private records. Anonymous sign-in obtains a real authenticated Supabase identity before POST /workspaces/demo. Application admin privileges never derive from is_anonymous=false alone. Return 404 for inaccessible record IDs to avoid existence disclosure; use 403 when a known workspace member lacks an operation permission.

## Required atomic operations

1. **Create/seed workspace:** verify identity, reserve allowed workspace slot, create membership, copy seed inputs to fresh IDs, write initial revision/audit, return result under an idempotency record. Concurrent duplicate creation must not create two active workspaces.
2. **Import batch:** lock workspace/cases in stable order, enforce caps and expected revision, validate every supplied object first, insert accepted reports/conflicts, invalidate dependencies and advance queue/audit revision. Structural bundle failure rejects the bundle; per-record domain rejection is reported without inserting that record. Accepted records and their import summary commit together.
3. **Save satellite/action/settings:** lock current record, compare expected_revision, enforce role and referenced assessment freshness, create revision/action, update pointers/floor/workflow and append audit atomically. A stale acknowledgement cannot clear the latest urgent floor.
4. **Claim operation:** verify membership, idempotency, quotas and input snapshot; acquire one workspace lease and any provider global slot, issue unpredictable lease token and expiry using database wall time. Do not hold a SQL transaction open during model or numerical work.
5. **Commit chunk:** reacquire row lock, verify lease token, unexpired lease and current input digest, insert uniquely keyed completed items, persist cursor/progress and release lease. A retry may reuse verified item results but cannot publish a comparison until every required item has a supported disposition. Stale work is marked stale and does not update the current comparison.
6. **Finalize assessment/agent packet:** verify dependency versions, result schema and host validation; write immutable result, set current pointer only if current, append audit and complete idempotency record in one transaction. A lease acquired before an input change cannot overwrite newer evidence.
7. **Expire/reclaim:** an authorized resume request may mark expired work interrupted, release expired reservations according to policy and start a fresh lease. GET status never starts computation. Failed accounting uses conservative reservation until expiry; it must not allow double spending.
8. **Reset workspace:** owner-only revision-protected reset creates a new seed generation and cancels/stales prior operations. Perform bounded deletion/archival with relational integrity; never reset another workspace or the whole database.

POST bodies do not carry executable SQL, object-storage destinations, unrestricted URLs or callback addresses. Runtime file access is limited to packaged assets and temporary bounded scratch data.

## Queue time and acknowledgement details

Policy depends on the demo clock. Advance the scenario clock through a versioned workspace settings operation; increment queue revision and recompute affected priorities before serving the next queue snapshot. In live-wall-clock mode, detect the next deadline boundary on a request and atomically refresh stale policy buckets. A cursor is invalid when the resulting queue revision differs. Do not mutate the clock on every GET or silently reuse yesterday's urgency.

An urgent floor belongs to a particular unacknowledged material assessment chain. A downgrade proposal remains visible alongside the floor. An explicit latest-version acknowledgement records the actor/rationale and may clear the floor only if deterministic current policy permits the lower urgency. Closing a case does not cancel future material re-evaluation.

## Migrations and security acceptance

Order migrations: enums/base tables; foreign keys/indexes; membership helpers/RLS/grants; domain RPCs; synthetic template seed; optional retention maintenance. Each migration is versioned and reviewed. Avoid destructive renaming/drops during a release; use additive fields and an explicit later migration if necessary.

Test through real Supabase Auth and Data API, not only mocked Python repositories: two identities, viewer role, forged actor, guessed UUID, cross-workspace foreign key, expired JWT, direct assessment insertion, direct RPC execution, simultaneous updates, lease expiry, interrupted response and idempotent retry. These are required because service-key or grant mistakes can make otherwise correct application checks ineffective.

## Source notes

[^19-S18]: Supabase, [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security).
