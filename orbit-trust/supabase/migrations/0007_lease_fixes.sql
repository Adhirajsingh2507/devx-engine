-- ORBIT-TRUST 0007 — lease RPC bug fixes (found by the N2 acceptance harness).
-- Regenerated from the 0006 function sources with ONLY these 4 changes; bodies
-- are otherwise byte-identical to 0006. reset_workspace is unchanged.
-- CREATE OR REPLACE preserves the execute privileges set in 0006 (service_role
-- only), so no re-grant is needed.
--   1. claim_operation : store progress.ttl_seconds as int
--   2. commit_chunk    : read ttl_seconds as ::numeric::int
--   3. commit_chunk    : lease expiry marks interrupted and returns lease_expired
--   4. finalize_result : lease expiry marks interrupted and returns lease_expired

set search_path = public;

create or replace function claim_operation(
  p_workspace uuid, p_actor uuid, p_kind text,
  p_input_digest text, p_lease_token text, p_ttl interval)
returns jsonb language plpgsql security definer set search_path = public as $$
declare v_rev bigint; v_id uuid; v_tok text; v_exp timestamptz; v_new timestamptz;
begin
  perform _require_member(p_workspace, p_actor, 'analyst');
  -- serialize concurrent claims for this workspace and read its current revision
  select data_revision into v_rev from workspaces where id = p_workspace for update;
  if v_rev is null then raise exception 'not_found' using errcode = 'P0002'; end if;

  -- release expired reservations (interrupted work) before deciding
  update operations set state = 'interrupted', lease_token = null, lease_expires_at = null
    where workspace_id = p_workspace and state in ('claimed','running','paused')
      and lease_expires_at <= now();

  -- idempotent retry: an active, unexpired op for the same input is reused
  select id, lease_token, lease_expires_at into v_id, v_tok, v_exp
    from operations
    where workspace_id = p_workspace and input_digest = p_input_digest
      and state in ('claimed','running','paused') and lease_expires_at > now()
    limit 1;
  if v_id is not null then
    return jsonb_build_object('operation', v_id, 'lease_token', v_tok,
      'lease_expires_at', v_exp, 'input_revision', v_rev, 'reused', true);
  end if;

  -- reject if a different operation still holds an unexpired workspace lease
  if exists (select 1 from operations where workspace_id = p_workspace
               and state in ('claimed','running') and lease_expires_at > now()) then
    raise exception 'workspace_lease_held' using errcode = '55P03';
  end if;

  v_new := now() + p_ttl;

  -- optional provider global slot keyed by kind (only if such a slot is defined)
  if exists (select 1 from global_leases where slot = p_kind) then
    perform 1 from global_leases where slot = p_kind for update;
    if exists (select 1 from global_leases where slot = p_kind
                 and holder_token is not null and expires_at > now()) then
      raise exception 'global_slot_busy' using errcode = '55P03';
    end if;
    update global_leases set holder_token = p_lease_token, expires_at = v_new where slot = p_kind;
  end if;

  insert into operations(workspace_id, kind, input_revision, input_digest, state,
                         lease_token, lease_expires_at, cursor, progress)
    values (p_workspace, p_kind, v_rev, p_input_digest, 'claimed',
            p_lease_token, v_new, null,
            jsonb_build_object('committed', 0, 'ttl_seconds', extract(epoch from p_ttl)::int))
    returning id into v_id;

  return jsonb_build_object('operation', v_id, 'lease_token', p_lease_token,
    'lease_expires_at', v_new, 'input_revision', v_rev, 'reused', false);
end $$;

create or replace function commit_chunk(
  p_workspace uuid, p_operation uuid, p_lease_token text,
  p_input_digest text, p_items jsonb, p_cursor jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare v_op operations%rowtype; v_rev bigint; rec jsonb; v_ttl int; v_done int;
begin
  select * into v_op from operations
    where workspace_id = p_workspace and id = p_operation for update;
  if not found then raise exception 'not_found' using errcode = 'P0002'; end if;
  if v_op.lease_token is null or v_op.lease_token <> p_lease_token then
    raise exception 'bad_lease_token' using errcode = '42501';
  end if;
  -- expiry is an expected lifecycle outcome: mark interrupted and RETURN (a
  -- raise would roll back this very update). Caller re-claims to resume.
  if v_op.lease_expires_at <= now() then
    update operations set state = 'interrupted', lease_token = null, lease_expires_at = null
      where workspace_id = p_workspace and id = p_operation;
    return jsonb_build_object('status', 'lease_expired', 'operation', p_operation);
  end if;
  if v_op.state not in ('claimed','running') then
    raise exception 'operation_not_active' using errcode = '55P03';
  end if;

  select data_revision into v_rev from workspaces where id = p_workspace;

  -- staleness: input basis moved since claim
  if p_input_digest <> v_op.input_digest or v_op.input_revision <> v_rev then
    for rec in select * from jsonb_array_elements(p_items) loop
      insert into operation_items(workspace_id, operation_id, item_key, input_digest, status, result)
        values (p_workspace, p_operation, rec->>'item_key',
                coalesce(rec->>'input_digest', p_input_digest), 'stale', rec->'result')
        on conflict (workspace_id, operation_id, item_key) do update set status = 'stale';
    end loop;
    update operations set state = 'interrupted'
      where workspace_id = p_workspace and id = p_operation;
    return jsonb_build_object('status', 'stale', 'operation', p_operation);
  end if;

  -- upsert verified items (retry reuses results)
  for rec in select * from jsonb_array_elements(p_items) loop
    insert into operation_items(workspace_id, operation_id, item_key, input_digest, status, result)
      values (p_workspace, p_operation, rec->>'item_key',
              coalesce(rec->>'input_digest', p_input_digest),
              coalesce(rec->>'status', 'done'), rec->'result')
      on conflict (workspace_id, operation_id, item_key)
        do update set status = excluded.status, result = excluded.result,
                      input_digest = excluded.input_digest;
  end loop;

  v_ttl := coalesce((v_op.progress->>'ttl_seconds')::numeric::int, 120);
  select count(*) into v_done from operation_items
    where workspace_id = p_workspace and operation_id = p_operation and status = 'done';
  update operations set state = 'running', cursor = p_cursor,
      progress = jsonb_build_object('committed', v_done, 'ttl_seconds', v_ttl),
      lease_expires_at = now() + make_interval(secs => v_ttl)
    where workspace_id = p_workspace and id = p_operation;

  return jsonb_build_object('status', 'running', 'operation', p_operation, 'committed', v_done);
end $$;

create or replace function finalize_result(
  p_workspace uuid, p_operation uuid, p_lease_token text, p_result jsonb)
returns jsonb language plpgsql security definer set search_path = public as $$
declare v_op operations%rowtype; v_rev bigint; v_result_id uuid; v_seq bigint;
begin
  select * into v_op from operations
    where workspace_id = p_workspace and id = p_operation for update;
  if not found then raise exception 'not_found' using errcode = 'P0002'; end if;
  if v_op.state = 'complete' then
    return jsonb_build_object('status', 'complete', 'result_id', v_op.result_id, 'reused', true);
  end if;
  if v_op.lease_token is null or v_op.lease_token <> p_lease_token then
    raise exception 'bad_lease_token' using errcode = '42501';
  end if;
  if v_op.lease_expires_at <= now() then
    update operations set state = 'interrupted', lease_token = null, lease_expires_at = null
      where workspace_id = p_workspace and id = p_operation;
    return jsonb_build_object('status', 'lease_expired', 'operation', p_operation);
  end if;

  -- a lease acquired before an input change cannot overwrite newer evidence
  select data_revision into v_rev from workspaces where id = p_workspace;
  if v_op.input_revision <> v_rev then
    update operations set state = 'interrupted', lease_token = null, lease_expires_at = null
      where workspace_id = p_workspace and id = p_operation;
    return jsonb_build_object('status', 'stale', 'reason', 'input_moved');
  end if;

  -- publish nothing until every item has a supported (done) disposition
  if exists (select 1 from operation_items
               where workspace_id = p_workspace and operation_id = p_operation and status <> 'done') then
    raise exception 'incomplete_dispositions' using errcode = 'P0001';
  end if;

  insert into comparisons(workspace_id, candidate_set_id, candidate_revision,
                          input_digest, status, result, coverage)
    values (p_workspace,
            coalesce((p_result->>'candidate_set_id')::uuid, gen_random_uuid()),
            coalesce((p_result->>'candidate_revision')::bigint, v_op.input_revision),
            v_op.input_digest,
            coalesce(p_result->>'status', 'passes_demo_checks'),
            p_result,
            coalesce(p_result->'coverage', '{}'::jsonb))
    returning id into v_result_id;

  update operations set state = 'complete', result_id = v_result_id,
      lease_token = null, lease_expires_at = null
    where workspace_id = p_workspace and id = p_operation;
  update global_leases set holder_token = null, expires_at = null
    where holder_token = p_lease_token;

  update workspaces set next_audit_sequence = next_audit_sequence + 1
    where id = p_workspace returning next_audit_sequence - 1 into v_seq;
  insert into audit_events(workspace_id, sequence, actor_id, entity, event_type, summary)
    values (p_workspace, v_seq, null, 'operation', 'finalized',
            jsonb_build_object('operation', p_operation, 'result', v_result_id));

  return jsonb_build_object('status', 'complete', 'result_id', v_result_id, 'reused', false);
end $$;
