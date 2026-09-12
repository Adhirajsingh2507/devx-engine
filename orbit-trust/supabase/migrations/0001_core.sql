-- ORBIT-TRUST core schema (handoff doc 19). Migration order within this file:
-- base tables -> FKs/indexes -> RLS/grants + membership helper.
-- Domain RPCs, synthetic seed and the M3/M4/M5 tables live in later migrations.
--
-- NOT YET APPLIED: no Supabase project/credentials in this session. Apply with
-- `supabase db push` against the owner's project, then run the doc-19 security
-- acceptance tests (two identities, viewer role, forged actor, guessed UUID,
-- cross-workspace FK, expired JWT, direct insert, direct RPC, lease expiry).

create extension if not exists pgcrypto;

-- ---------------------------------------------------------------------------
-- base tables
-- ---------------------------------------------------------------------------
create table workspaces (
  id                 uuid primary key default gen_random_uuid(),
  owner_id           uuid not null,
  mode               text not null check (mode in ('public_synthetic','local_research')),
  data_revision      bigint not null default 0,
  queue_revision     bigint not null default 0,
  next_audit_sequence bigint not null default 1,
  demo_clock         timestamptz not null default '2026-09-11T12:20:00Z',
  created_at         timestamptz not null default now(),
  last_active_at     timestamptz not null default now()
);

create table workspace_members (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  user_id      uuid not null,
  role         text not null check (role in ('owner','analyst','viewer')),
  created_at   timestamptz not null default now(),
  primary key (workspace_id, user_id)
);

create table satellites (
  workspace_id     uuid not null references workspaces(id) on delete cascade,
  id               uuid not null default gen_random_uuid(),
  current_revision bigint not null default 1,
  archived         boolean not null default false,
  primary key (workspace_id, id)
);

create table satellite_revisions (
  workspace_id uuid not null,
  satellite_id uuid not null,
  revision     bigint not null,
  metadata     jsonb not null,
  author_id    uuid not null,
  created_at   timestamptz not null default now(),
  primary key (workspace_id, satellite_id, revision),
  foreign key (workspace_id, satellite_id) references satellites(workspace_id, id) on delete cascade
);

create table cases (
  workspace_id         uuid not null references workspaces(id) on delete cascade,
  id                   uuid not null default gen_random_uuid(),
  event_key            text not null,
  object_pair          text[] not null,          -- canonicalized ordered pair
  current_revision     bigint not null default 1,
  workflow_state       text not null default 'new'
                         check (workflow_state in ('new','reviewing','awaiting_information',
                                'decision_recorded','monitoring','closed')),
  event_phase          text not null default 'pre_encounter'
                         check (event_phase in ('pre_encounter','post_encounter_pending_verification',
                                'verified_outcome_recorded')),
  assigned_member      uuid,
  latest_assessment_id uuid,
  urgent_floor         text check (urgent_floor in ('P0','P1','P2','P3')),
  created_at           timestamptz not null default now(),
  primary key (workspace_id, id),
  unique (workspace_id, event_key)
);

create table reports (
  workspace_id     uuid not null,
  id               uuid not null default gen_random_uuid(),
  case_id          uuid not null,
  source_name      text not null,
  source_revision  text not null,
  raw_digest       text not null,     -- SHA-256 of original bytes
  normalized_digest text not null,    -- canonical JSON digest (doc 04)
  source_created_at timestamptz not null,
  received_at      timestamptz not null default now(),
  raw_json         jsonb not null,
  normalized_json  jsonb not null,
  primary key (workspace_id, id),
  foreign key (workspace_id, case_id) references cases(workspace_id, id) on delete cascade,
  -- report identity: same revision + different body is a retained conflict, so
  -- uniqueness includes the raw digest (doc 19).
  unique (workspace_id, case_id, source_name, source_revision, raw_digest)
);

create table source_conflicts (
  workspace_id uuid not null,
  id           uuid not null default gen_random_uuid(),
  case_id      uuid not null,
  report_a     uuid not null,
  report_b     uuid not null,
  state        text not null default 'open' check (state in ('open','resolved')),
  review_action_id uuid,
  primary key (workspace_id, id),
  foreign key (workspace_id, case_id) references cases(workspace_id, id) on delete cascade
);

create table assessments (
  workspace_id    uuid not null,
  id              uuid not null default gen_random_uuid(),
  case_id         uuid not null,
  input_revision  bigint not null,
  input_digest    text not null,
  method_version  text not null,
  policy_version  text not null,
  evidence_state  text not null check (evidence_state in ('usable','incomplete','inconsistent','unsupported')),
  proposed_urgency text not null check (proposed_urgency in ('P0','P1','P2','P3')),
  effective_urgency text not null check (effective_urgency in ('P0','P1','P2','P3')),
  deadline        timestamptz,
  method_status   text not null,
  facts           jsonb not null,
  findings        jsonb not null,
  created_at      timestamptz not null default now(),
  primary key (workspace_id, id),
  foreign key (workspace_id, case_id) references cases(workspace_id, id) on delete cascade
);

create table review_actions (
  workspace_id uuid not null,
  id           uuid not null default gen_random_uuid(),
  case_id      uuid not null,
  actor_id     uuid not null,
  acknowledged_assessment_id uuid,
  expected_revision bigint not null,
  action       text not null,
  rationale    text not null,
  created_at   timestamptz not null default now(),
  primary key (workspace_id, id),
  foreign key (workspace_id, case_id) references cases(workspace_id, id) on delete cascade
);

create table audit_events (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  sequence     bigint not null,
  actor_id     uuid,
  entity       text not null,
  entity_revision bigint,
  event_type   text not null,
  summary      jsonb not null,     -- redacted, non-secret
  created_at   timestamptz not null default now(),
  primary key (workspace_id, sequence)
);

create table idempotency_records (
  workspace_id uuid not null,
  actor_id     uuid not null,
  route        text not null,
  key          text not null,
  payload_digest text not null,
  status       text not null,
  result_ref   text,
  expires_at   timestamptz not null,
  primary key (workspace_id, actor_id, route, key)
);

-- server-only internals
create table quota_buckets (
  scope    text not null,
  subject  text not null,
  window_start timestamptz not null,
  reserved int not null default 0,
  consumed int not null default 0,
  expires_at timestamptz not null,
  primary key (scope, subject, window_start)
);

create table global_leases (
  slot        text primary key,
  holder_token text,
  expires_at  timestamptz
);

create table public_seed_templates (
  seed_id  text not null,
  version  text not null,
  payload  jsonb not null,
  digest   text not null,
  primary key (seed_id, version)
);

-- ---------------------------------------------------------------------------
-- indexes (doc 19)
-- ---------------------------------------------------------------------------
create index cases_queue_idx on cases (workspace_id, urgent_floor, id);
create index cases_event_idx on cases (workspace_id, event_key);
create index reports_source_idx on reports (workspace_id, case_id, source_name, source_created_at);
create index assessments_digest_idx on assessments (workspace_id, input_digest, method_version, policy_version);
create index operations_placeholder_idx on audit_events (workspace_id, sequence);

-- ---------------------------------------------------------------------------
-- RLS + grants (doc 19). Browser reads use the user JWT + RLS; all domain
-- writes go through server-only transactional RPCs (added in 0003).
-- ---------------------------------------------------------------------------
alter table workspaces          enable row level security;
alter table workspace_members   enable row level security;
alter table satellites          enable row level security;
alter table satellite_revisions enable row level security;
alter table cases               enable row level security;
alter table reports             enable row level security;
alter table source_conflicts    enable row level security;
alter table assessments         enable row level security;
alter table review_actions      enable row level security;
alter table audit_events        enable row level security;

-- server-only tables: no anon/authenticated grants at all
revoke all on quota_buckets, global_leases, idempotency_records from anon, authenticated;

-- membership helper: SECURITY DEFINER with a fixed safe search_path, no dynamic
-- SQL, to avoid RLS policy recursion (doc 19). Test with users having no membership.
create or replace function is_member(target_workspace uuid)
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from workspace_members m
    where m.workspace_id = target_workspace
      and m.user_id = auth.uid()
  );
$$;
revoke all on function is_member(uuid) from public;
grant execute on function is_member(uuid) to authenticated;

-- read policies: membership-scoped. Direct writes are denied (no write policy);
-- mutations must go through server RPCs (0003).
create policy ws_read   on workspaces        for select using (is_member(id));
create policy mem_read  on workspace_members for select using (is_member(workspace_id));
create policy sat_read  on satellites        for select using (is_member(workspace_id));
create policy satr_read on satellite_revisions for select using (is_member(workspace_id));
create policy case_read on cases             for select using (is_member(workspace_id));
create policy rep_read  on reports           for select using (is_member(workspace_id));
create policy conf_read on source_conflicts  for select using (is_member(workspace_id));
create policy asmt_read on assessments       for select using (is_member(workspace_id));
create policy ract_read on review_actions    for select using (is_member(workspace_id));
create policy aud_read  on audit_events      for select using (is_member(workspace_id));
