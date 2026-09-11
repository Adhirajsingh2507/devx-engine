-- ORBIT-TRUST fleet / consequence / operations tables (handoff doc 19).
-- Additive; depends on 0001_core.sql. NOT YET APPLIED (no Supabase project).

create table candidate_sets (
  workspace_id      uuid not null references workspaces(id) on delete cascade,
  id                uuid not null default gen_random_uuid(),
  revision          bigint not null,
  catalogue_revision text not null,
  interval_start_offset_s double precision not null,
  interval_end_offset_s   double precision not null,
  snapshot          jsonb not null,   -- immutable canonical candidate set
  input_digest      text not null,
  created_at        timestamptz not null default now(),
  primary key (workspace_id, id, revision)
);

create table comparisons (
  workspace_id      uuid not null references workspaces(id) on delete cascade,
  id                uuid not null default gen_random_uuid(),
  candidate_set_id  uuid not null,
  candidate_revision bigint not null,
  input_digest      text not null,
  status            text not null check (status in ('passes_demo_checks','blocked_by_demo_policy','review_required_incomplete','in_progress')),
  result            jsonb,            -- complete pair result snapshot
  coverage          jsonb not null,
  created_at        timestamptz not null default now(),
  primary key (workspace_id, id)
);

create table operations (
  workspace_id     uuid not null references workspaces(id) on delete cascade,
  id               uuid not null default gen_random_uuid(),
  kind             text not null,
  input_revision   bigint not null,
  input_digest     text not null,
  state            text not null check (state in ('claimed','running','paused','interrupted','complete','failed')),
  lease_token      text,
  lease_expires_at timestamptz,
  cursor           jsonb,
  progress         jsonb,
  result_id        uuid,
  error_code       text,
  created_at       timestamptz not null default now(),
  primary key (workspace_id, id)
);
create index operations_lease_idx on operations (workspace_id, state, lease_expires_at);

create table operation_items (
  workspace_id uuid not null,
  operation_id uuid not null,
  item_key     text not null,
  input_digest text not null,
  status       text not null check (status in ('done','stale','failed')),
  result       jsonb,
  primary key (workspace_id, operation_id, item_key),
  foreign key (workspace_id, operation_id) references operations(workspace_id, id) on delete cascade
);

create table economic_scenarios (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  id           uuid not null default gen_random_uuid(),
  revision     bigint not null,
  probability_refs jsonb not null,
  inputs       jsonb not null,        -- decimal-string monetary inputs
  currency     text not null,
  result       jsonb,                 -- immutable result + dependencies
  created_at   timestamptz not null default now(),
  primary key (workspace_id, id, revision)
);

create table reentry_scenarios (
  workspace_id uuid not null references workspaces(id) on delete cascade,
  id           uuid not null default gen_random_uuid(),
  revision     bigint not null,
  footprint    jsonb not null,
  layers       jsonb not null,
  assumptions  jsonb,
  result       jsonb,
  created_at   timestamptz not null default now(),
  primary key (workspace_id, id, revision)
);

create table communication_packets (
  workspace_id   uuid not null references workspaces(id) on delete cascade,
  id             uuid not null default gen_random_uuid(),
  case_id        uuid,
  comparison_id  uuid,
  candidate_id   text,
  state          text not null check (state in ('draft','authorized_for_simulation','waiting_for_contact','sent','acknowledged','execution_reported','expired','failed','cancelled')),
  contact        jsonb not null,      -- supplied contact/timing assumptions
  events         jsonb not null default '[]',
  expires_at     timestamptz not null,
  created_at     timestamptz not null default now(),
  primary key (workspace_id, id)
);

-- RLS: membership-scoped reads; writes via server RPCs only (0003).
alter table candidate_sets        enable row level security;
alter table comparisons           enable row level security;
alter table operations            enable row level security;
alter table operation_items       enable row level security;
alter table economic_scenarios    enable row level security;
alter table reentry_scenarios     enable row level security;
alter table communication_packets enable row level security;

create policy cset_read on candidate_sets        for select using (is_member(workspace_id));
create policy comp_read on comparisons           for select using (is_member(workspace_id));
create policy op_read   on operations            for select using (is_member(workspace_id));
create policy opi_read  on operation_items       for select using (is_member(workspace_id));
create policy econ_read on economic_scenarios    for select using (is_member(workspace_id));
create policy rent_read on reentry_scenarios     for select using (is_member(workspace_id));
create policy pkt_read  on communication_packets for select using (is_member(workspace_id));
