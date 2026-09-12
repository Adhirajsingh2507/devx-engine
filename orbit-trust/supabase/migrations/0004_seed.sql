-- ORBIT-TRUST default synthetic demo seed (handoff doc 11). NOT YET APPLIED.
-- Public, immutable, synthetic-only. create_demo_workspace (0003) copies this
-- into a fresh workspace with new runtime ids and preserved source lineage.
--
-- Recipe (doc 11): satellites A/B/C; an audit case for event-AB with source
-- revision r1 = sigma-200 report (matching reported_pc), then a later r2 at
-- 12:10 with sigma-1000 covariance and secondary_last_observation_at = null.
-- r1 is preserved in history. At the fixed 12:20 clock the current case requires
-- review for missing evidence and retains the prior unacknowledged urgent floor.
-- Full report bodies are hydrated by the API from data/fixtures/encounter_reference.json
-- at seed time (kept out of SQL to avoid duplicating the canonical fixtures).

insert into public_seed_templates(seed_id, version, digest, payload) values (
  'default-demo', '2.0',
  'recipe:default-demo@2.0',
  jsonb_build_object(
    'demo_clock', '2026-09-11T12:20:00Z',
    'satellites', jsonb_build_array(
      jsonb_build_object('display_name', 'SAT-A', 'operator_label', 'synthetic', 'maneuver_capable', true),
      jsonb_build_object('display_name', 'SAT-B', 'operator_label', 'synthetic', 'maneuver_capable', false),
      jsonb_build_object('display_name', 'SAT-C', 'operator_label', 'synthetic', 'maneuver_capable', false)
    ),
    'cases', jsonb_build_array(
      jsonb_build_object(
        'event_key', 'event-AB',
        'object_pair', jsonb_build_array('A', 'B'),
        'reports', jsonb_build_array(
          jsonb_build_object('source_revision', 'r1', 'fixture', 'encounter_reference.json#sigma-200',
                             'created_at', '2026-09-11T12:00:00Z'),
          jsonb_build_object('source_revision', 'r2', 'fixture', 'encounter_reference.json#sigma-1000',
                             'created_at', '2026-09-11T12:10:00Z',
                             'override', jsonb_build_object('secondary_last_observation_at', null))
        )
      )
    ),
    'separate_scenarios', jsonb_build_object(
      'fleet',     'fleet_candidates.json',
      'economics', 'economics.json',
      'reentry',   'reentry.json'
    )
  )
)
on conflict (seed_id, version) do nothing;
