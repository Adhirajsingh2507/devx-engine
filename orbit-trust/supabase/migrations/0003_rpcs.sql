-- ORBIT-TRUST server-only transactional RPCs (handoff doc 19). NOT YET APPLIED.
--
-- Model: FastAPI verifies the JWT, does schema/domain/ledger validation, then
-- calls these narrow SECURITY DEFINER functions via the service role, passing
-- the already-verified actor as p_actor. Each function still enforces the
-- actor's membership/role. No generic arbitrary-SQL RPC is ever exposed. All
-- execute grants are revoked from public/anon/authenticated; only the service
-- role calls them. A function body is one transaction (all-or-nothing).

set search_path = public;

-- membership/role guard used by every write RPC
create or replace function _require_member(p_workspace uuid, p_actor uuid, p_min_role text)
returns void language plpgsql security definer set search_path = public as $$
declare r text;
begin
  select role into r from workspace_members where workspace_id = p_workspace and user_id = p_actor;
  if r is null then raise exception 'not_a_member' using errcode = '42501'; end if;
  -- role rank: owner > analyst > viewer
  if p_min_role = 'analyst' and r = 'viewer' then raise exception 'insufficient_role' using errcode = '42501'; end if;
  if p_min_role = 'owner'  and r <> 'owner'  then raise exception 'insufficient_role' using errcode = '42501'; end if;
end $$;

-- 1. create/seed an isolated demo workspace (idempotent on p_idempotency_key)
create or replace function create_demo_workspace(p_actor uuid, p_seed_id text, p_idempotency_key text)
returns uuid language plpgsql security definer set search_path = public as $$
declare ws uuid; existing uuid;
begin
  select result_ref::uuid into existing from idempotency_records
    where actor_id = p_actor and route = 'create_demo_workspace' and key = p_idempotency_key
      and expires_at > now();
  if existing is not null then return existing; end if;

  insert into workspaces(owner_id, mode) values (p_actor, 'public_synthetic') returning id into ws;
  insert into workspace_members(workspace_id, user_id, role) values (ws, p_actor, 'owner');
  -- copy seed inputs to fresh ids from public_seed_templates (0004) here.
  insert into audit_events(workspace_id, sequence, actor_id, entity, event_type, summary)
    values (ws, 1, p_actor, 'workspace', 'created', jsonb_build_object('seed', p_seed_id));
  update workspaces set next_audit_sequence = 2 where id = ws;
  insert into idempotency_records(workspace_id, actor_id, route, key, payload_digest, status, result_ref, expires_at)
    values (ws, p_actor, 'create_demo_workspace', p_idempotency_key, p_seed_id, 'done', ws::text, now() + interval '24 hours');
  return ws;
end $$;

-- 2. commit an already-validated import batch atomically (validation ran in the
--    API; this inserts accepted records, bumps revisions, writes one audit event)
create or replace function import_commit(
  p_workspace uuid, p_actor uuid, p_expected_revision bigint,
  p_reports jsonb,   -- array of report rows to insert
  p_summary jsonb)   -- accepted/deduplicated/conflicted/rejected counts
returns bigint language plpgsql security definer set search_path = public as $$
declare rec jsonb; seq bigint; new_rev bigint;
begin
  perform _require_member(p_workspace, p_actor, 'analyst');
  perform 1 from workspaces where id = p_workspace and data_revision = p_expected_revision for update;
  if not found then raise exception 'revision_conflict' using errcode = '40001'; end if;

  for rec in select * from jsonb_array_elements(p_reports) loop
    insert into reports(workspace_id, case_id, source_name, source_revision, raw_digest,
                        normalized_digest, source_created_at, raw_json, normalized_json)
    values (p_workspace, (rec->>'case_id')::uuid, rec->>'source_name', rec->>'source_revision',
            rec->>'raw_digest', rec->>'normalized_digest', (rec->>'source_created_at')::timestamptz,
            rec->'raw_json', rec->'normalized_json')
    on conflict (workspace_id, case_id, source_name, source_revision, raw_digest) do nothing;
  end loop;

  update workspaces set data_revision = data_revision + 1, queue_revision = queue_revision + 1,
                        next_audit_sequence = next_audit_sequence + 1
    where id = p_workspace
    returning data_revision, next_audit_sequence - 1 into new_rev, seq;
  insert into audit_events(workspace_id, sequence, actor_id, entity, event_type, summary)
    values (p_workspace, seq, p_actor, 'import', 'committed', p_summary);
  return new_rev;
end $$;

-- 3. record a review disposition; a stale acknowledgement cannot clear the floor
create or replace function save_review_action(
  p_workspace uuid, p_actor uuid, p_case uuid, p_expected_revision bigint,
  p_action text, p_rationale text, p_ack_assessment uuid)
returns bigint language plpgsql security definer set search_path = public as $$
declare cur_rev bigint; latest uuid; seq bigint;
begin
  perform _require_member(p_workspace, p_actor, 'analyst');
  select current_revision, latest_assessment_id into cur_rev, latest
    from cases where workspace_id = p_workspace and id = p_case for update;
  if cur_rev is null then raise exception 'not_found' using errcode = 'P0002'; end if;
  if cur_rev <> p_expected_revision then raise exception 'revision_conflict' using errcode = '40001'; end if;
  if p_ack_assessment is not null and p_ack_assessment <> latest then
    raise exception 'stale_acknowledgement' using errcode = '40001';  -- must ack the latest assessment
  end if;

  insert into review_actions(workspace_id, case_id, actor_id, acknowledged_assessment_id,
                             expected_revision, action, rationale)
    values (p_workspace, p_case, p_actor, p_ack_assessment, p_expected_revision, p_action, p_rationale);
  update cases set current_revision = current_revision + 1,
                   urgent_floor = case when p_ack_assessment = latest then null else urgent_floor end
    where workspace_id = p_workspace and id = p_case;
  update workspaces set next_audit_sequence = next_audit_sequence + 1
    where id = p_workspace returning next_audit_sequence - 1 into seq;
  insert into audit_events(workspace_id, sequence, actor_id, entity, event_type, summary)
    values (p_workspace, seq, p_actor, 'case', p_action, jsonb_build_object('case', p_case));
  return cur_rev + 1;
end $$;

-- 4. advance the demo clock (versioned settings op; recompute happens in the API)
create or replace function advance_demo_clock(p_workspace uuid, p_actor uuid, p_new_clock timestamptz)
returns void language plpgsql security definer set search_path = public as $$
begin
  perform _require_member(p_workspace, p_actor, 'owner');
  update workspaces set demo_clock = p_new_clock, queue_revision = queue_revision + 1 where id = p_workspace;
end $$;

-- ---------------------------------------------------------------------------
-- Operation-lease RPCs: signatures + invariant contracts. Bodies are completed
-- and verified against a live database in N2 (they depend on runtime lease
-- timing, so they are not fabricated here untested).
--
--   claim_operation(p_workspace, p_actor, p_kind, p_input_digest, p_lease_token, p_ttl)
--     -> acquire ONE workspace lease + any global slot via row locks; issue an
--        unpredictable token + expiry from db wall time; reject if another
--        operation holds the lease. Never hold a txn open during compute.
--   commit_chunk(p_workspace, p_operation, p_lease_token, p_input_digest, p_items, p_cursor)
--     -> verify token + unexpired lease + unchanged input digest; upsert
--        uniquely-keyed items; persist cursor/progress; publish nothing until
--        every required item has a supported disposition; stale work -> 'stale'.
--   finalize_result(p_workspace, p_operation, p_lease_token, p_result)
--     -> verify dependency versions still current; write immutable result; set
--        current pointer only if current; append audit; complete idempotency.
--   reset_workspace(p_workspace, p_actor, p_expected_revision)
--     -> owner-only; new seed generation; cancel/stale prior operations;
--        bounded deletion with relational integrity; never touches another ws.
-- ---------------------------------------------------------------------------

-- lock down execution: service role only
revoke all on function _require_member(uuid, uuid, text) from public;
revoke all on function create_demo_workspace(uuid, text, text) from public;
revoke all on function import_commit(uuid, uuid, bigint, jsonb, jsonb) from public;
revoke all on function save_review_action(uuid, uuid, uuid, bigint, text, text, uuid) from public;
revoke all on function advance_demo_clock(uuid, uuid, timestamptz) from public;
