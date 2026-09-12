-- ORBIT-TRUST 0008 — replace retryable SQLSTATE 40001 with PT409 (HTTP 409).
-- Regenerated from 0003 (import_commit, save_review_action) and 0006
-- (reset_workspace); ONLY the conflict errcode changed. Bodies otherwise
-- byte-identical.
--
-- WHY: app-level optimistic-concurrency conflicts were raised with SQLSTATE
-- 40001 (serialization_failure). PostgREST AUTO-RETRIES 40001/40P01, so a
-- deterministic revision/ack conflict was retried until the client timed out
-- (proven live: import_commit + reset_workspace hung ~12-25s). PT409 is not
-- retried and maps to HTTP 409 Conflict, the correct status for these.
-- CREATE OR REPLACE preserves the execute privileges from 0005/0006
-- (service_role only), so no re-grant is needed.

set search_path = public;

create or replace function import_commit(
  p_workspace uuid, p_actor uuid, p_expected_revision bigint,
  p_reports jsonb,   -- array of report rows to insert
  p_summary jsonb)   -- accepted/deduplicated/conflicted/rejected counts
returns bigint language plpgsql security definer set search_path = public as $$
declare rec jsonb; seq bigint; new_rev bigint;
begin
  perform _require_member(p_workspace, p_actor, 'analyst');
  perform 1 from workspaces where id = p_workspace and data_revision = p_expected_revision for update;
  if not found then raise exception 'revision_conflict' using errcode = 'PT409'; end if;

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
  if cur_rev <> p_expected_revision then raise exception 'revision_conflict' using errcode = 'PT409'; end if;
  if p_ack_assessment is not null and p_ack_assessment <> latest then
    raise exception 'stale_acknowledgement' using errcode = 'PT409';  -- must ack the latest assessment
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

create or replace function reset_workspace(
  p_workspace uuid, p_actor uuid, p_expected_revision bigint)
returns bigint language plpgsql security definer set search_path = public as $$
declare v_rev bigint; v_new bigint; v_seq bigint;
begin
  perform _require_member(p_workspace, p_actor, 'owner');
  select data_revision into v_rev from workspaces where id = p_workspace for update;
  if v_rev is null then raise exception 'not_found' using errcode = 'P0002'; end if;
  if v_rev <> p_expected_revision then raise exception 'revision_conflict' using errcode = 'PT409'; end if;

  update global_leases set holder_token = null, expires_at = null
    where holder_token in (select lease_token from operations
                           where workspace_id = p_workspace and lease_token is not null);
  update operations set state = 'interrupted', lease_token = null, lease_expires_at = null
    where workspace_id = p_workspace and state in ('claimed','running','paused');

  -- bounded deletion (all scoped to this workspace; children cascade)
  delete from communication_packets where workspace_id = p_workspace;
  delete from reentry_scenarios     where workspace_id = p_workspace;
  delete from economic_scenarios    where workspace_id = p_workspace;
  delete from comparisons           where workspace_id = p_workspace;
  delete from candidate_sets        where workspace_id = p_workspace;
  delete from operations            where workspace_id = p_workspace;  -- cascades operation_items
  delete from cases                 where workspace_id = p_workspace;  -- cascades reports/assessments/reviews/conflicts
  delete from satellites            where workspace_id = p_workspace;  -- cascades satellite_revisions

  update workspaces set data_revision = data_revision + 1, queue_revision = queue_revision + 1,
         next_audit_sequence = next_audit_sequence + 1, last_active_at = now()
    where id = p_workspace returning data_revision, next_audit_sequence - 1 into v_new, v_seq;
  insert into audit_events(workspace_id, sequence, actor_id, entity, event_type, summary)
    values (p_workspace, v_seq, p_actor, 'workspace', 'reset',
            jsonb_build_object('from_revision', p_expected_revision));
  return v_new;
end $$;
