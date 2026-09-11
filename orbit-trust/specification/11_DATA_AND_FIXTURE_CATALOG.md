# Data sources and reproducible fixture catalogue

## Three distinct data modes

Public demonstration mode accepts synthetic canonical JSON and seeded examples only. Local research mode can import the ESA historical training archive for reported-risk replay. A future operator mode needs separate data agreements and complete validated source adapters. A provenance label is visible at workspace, case and export levels.

The ESA archive was downloaded and inspected during prior research. It contains 162,634 rows, 103 columns, 13,154 events and 19 mission IDs; SHA-256 is `68362fe5629cc80f17291f2d73f733bf4e922675e37b91a8ee79afadb46f3edc`. Download link: https://kelvins.esa.int/media/public/competitions/collision-avoidance-challenge/train_data.zip. The derived audit is included under reference/; the 87.7 MB archive is not bundled. [^11-S15]

## Historical adapter

Preserve all columns in a raw research record. Normalize documented risk as log10 Pc; retain the raw value. The 67,240 rows at -30 have unresolved floor/sentinel semantics and cannot establish meaningful precision at exactly 1e-30. All max_risk_estimate values are negative; exclude that field from risk/policy math until its encoding is verified. Observation-offset sign conventions are unresolved; do not label them absolute orbit age.

Exclude 391 negative time_to_tca rows before prospective replay selection. Then select events with at least one input at time_to_tca >= 2 days and a latest pre-TCA record with 0 <= time_to_tca < 1 day: the inspected archive gives 8,287 eligible events. An earlier audit key reported 7,962 because it excluded whole events containing any negative row; that key is superseded and is not the intended cohort.

Sort each event by decreasing time_to_tca for replay. Split by whole event, never by individual report, and do not use the last recorded risk as an actual collision label. With no absolute dates, do not claim a calendar-time train/test split. Freeze deterministic event-based calibration/holdout partitions and report mission composition. This pack does not require ML training.

Some position and velocity covariance/observation fields are missing. Suitability is calculation-specific, but the archive lacks the full geometry/frame/mission information required for our canonical complete-encounter path. Its last-observation metadata, max-risk fields and velocity gaps must not be silently guessed into a validated orbital assessment.

The data page and challenge rules do not establish unrestricted redistribution or commercial reuse for this project. Do not publish the raw archive, private operator data or a derived extract in the public demo without resolving applicable terms. This pack includes only source links, aggregate audit facts and original fictional fixtures. [^11-S15]

## Bundled fixtures

| File | Purpose |
| --- | --- |
| encounter_reference.json | Complete synthetic encounter with the four checked sigma alternatives |
| fleet_candidates.json | Three-object short-segment comparison with supplied A alternatives |
| triage_cases.json | Clock/deadline/materiality cases and expected tiers |
| economics.json | Exact decimal arithmetic reference and missing/invalid scenarios |
| reentry.json | Regional polygons and fictional population/asset points |
| communications.json | Contact timing, acknowledgement and packet-state simulation |
| report_update_cases.json | Duplicate, out-of-order, source conflict and stale-assessment expectations |
| adversarial_cases.json | Forbidden tool calls, prompt injection and citation/selection failures |

Expected values are test oracles for the specified model and fixtures, not stored production answers to display instead of computing. The next implementer must implement the calculation and compare against them. The packet-generating host can use templates, but fake numerical outputs or hardcoded candidate outcomes do not satisfy the numerical milestone.

Fixtures containing malformed values are negative tests, not examples of accepted input. Their expected_rejection field distinguishes schema errors from domain unsupported outcomes. No seed contains a real person's contact data, actual spacecraft command or secretly copied financial record.

## Default demo seed recipe

Create three synthetic satellite metadata records A/B/C and an audit case from the sigma-200 Report input. Give that report source_revision=r1 and a matching reported_pc from its reference value. Insert a later r2 at 12:10 UTC with sigma-1000 covariance, its matching lower reported Pc, and secondary_last_observation_at=null. Preserve r1 in history. At the fixed 12:20 clock, the current case requires review for missing evidence and retains the prior unacknowledged urgent floor. The model can inspect history and request observation/state context. Do not automatically call the old covariance a currently applicable scenario unless the scenario set explicitly declares it.

Load fleet_candidates.json as a separate candidate-set scenario and show all nine candidate/pair cells. Load economics.json as the explicitly separate financial reference and reentry.json as the separate ground-exposure reference. The sigma alternatives are independent calculation fixtures; do not bulk import all four unchanged source revisions as if they were sequential reports. The report-update fixture describes deliberate duplicate/conflict cases separately.

For the hero recording, retain one additional deliberately conflicting source-revision example if demonstrating SOURCE_REVISION_CONFLICT. Missing data, an older warning and an actual same-revision conflict are different findings; the narration must match the displayed case. Seed reset restores the same fictional clock and source history using fresh runtime IDs.

## Generation and scaling

For >100-case pagination tests, generate 205 explicit unique synthetic case IDs from the reference family with recorded seed=20260911, varied supplied deadlines and 7 known P0/P1 cases beyond insertion index 100. These are UI/load fixtures and not 205 independent scientific encounters. For numerical load testing, disclose the number of repeated versus distinct geometries and disable cache in the uncached pass.

Public maximums: 20 satellites, 500 cases, 2,000 report revisions, 3 response alternatives plus baseline, 5 reentry scenarios and 1,000 exposure points per workspace. Reject larger public bundles with a limit message and recommend local research mode. These limits bound costs and validation effort; they are not platform capacity claims.

Keep archive downloads explicit and outside server request paths. Imported filenames are metadata, not filesystem destinations. Public JSON uploads are at most 2 MiB, contain no embedded archives and do not trigger arbitrary URL downloads. Export includes schema/provenance, input hashes, assumptions and method version so another installation can reproduce it.

## Source notes

[^11-S15]: ESA Kelvins, [Collision Avoidance Challenge data](https://kelvins.esa.int/collision-avoidance-challenge/data/) and [Rules](https://kelvins.esa.int/collision-avoidance-challenge/rules/).
