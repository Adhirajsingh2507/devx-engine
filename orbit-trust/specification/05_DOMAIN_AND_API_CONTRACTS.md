# Domain records and API contracts

The canonical input contracts are in `schemas/core.schema.json`. JSON Schema validates structure; domain validators enforce physical applicability, ownership and cross-field rules. The schema root accepts Report, CandidateSet, EconomicScenario, ReentryScenario or CommunicationScenario, discriminated by bundle_kind. ImportBatch, AgentSelection and Error are separate named definitions. Fixture files are test wrappers: import their input object, not the entire expected-output wrapper. The API is versioned under `/api/v1`. Generate and commit an OpenAPI snapshot from the implemented FastAPI models, then compare it in CI. This document specifies behavior rather than an already running endpoint.

## Shared conventions

Use UTF-8 JSON, snake_case API fields and UTC ISO 8601 timestamps ending in Z. Runtime IDs are UUIDs; fixture IDs are stable readable strings. IDs are opaque to the client. All numbers must be finite; no NaN, Infinity or string-to-number coercion. Probabilities are linear values in [0,1] unless the field explicitly says log10. Money uses a decimal string with a currency code, never a binary float in the persistence/API layer. Distances are metres, velocity metres/second, covariance square metres and durations seconds.

Every input bundle declares schema_version=2.0, provenance_kind (synthetic, historical or operator_supplied), source_name and source_revision. Imported timestamps are source facts; received_at is the application's reception time. Recomputed/derived fields retain their source paths and method IDs. Missing is null or a missing optional field as the schema specifies, never an invented zero.

## Records

| Record | Required content and relationships |
| --- | --- |
| Workspace | ID, owner/member identities, mode, creation time and data revision |
| Satellite | Workspace, ID, display name, operator label, maneuver capability, metadata revision and optional economic inputs |
| Case | Workspace, explicit event key, object pair, reported TCA, workflow state, assignment and latest assessment ID |
| Report | Case, provider/source, source revision, creation/reception times, TCA, reported Pc, raw input digest and optional complete encounter |
| Encounter | Common epoch and frame, two object states, covariance assumptions, radii and model-domain declaration |
| Finding | Stable ID, category, code, severity, material flag, source references and explanation template parameters |
| Assessment | Input/report IDs, digest, policy version, evidence state, urgency, facts, method status, deadline and creation time |
| CandidateSet | Immutable baseline and alternative trajectory snapshots, catalogue revision, horizon and supplied planning constraints |
| Comparison | Every assessed pair/candidate, coverage, rejected/unsupported checks and candidate disposition |
| EconomicScenario | Currency, probability references, conditional loss line items, response costs and uncertainty labels |
| ReentryScenario | Footprint/layer revisions, geographic conventions and optional vulnerability inputs |
| AgentRun | Assessment binding, provider/model, prompt version, bounded tool trace, usage, validation and outcome |
| ReviewAction | Actor, case revision, action type, rationale, assessment acknowledged and timestamp |
| AuditEvent | Workspace sequence, actor, event type, entity/revision and non-secret change summary |

Keep reported_pc and recomputed_pc separate. A recomputation never overwrites its provider value. An assessment's evidence state is usable, incomplete, inconsistent or unsupported. Store individual findings even when one summary state takes precedence: unsupported calculation applicability first, then material inconsistency, then missing required data, otherwise usable. This summary does not suppress unrelated evidence.

## Event grouping and revisions

Workflow states are new, reviewing, awaiting_information, decision_recorded, monitoring and closed. Begin review from new; request information from reviewing; return awaiting_information to reviewing on new material evidence; record a disposition from reviewing; then move decision_recorded to monitoring or closed with latest-version acknowledgement and a rationale. New material evidence reopens monitoring/closed as reviewing. Assignment and notes do not constitute acknowledgement. Invalid transitions return 409 with the allowed next actions.

Acknowledgement resolves a review task for that assessment, not its physical risk finding. A closed or monitored case retains its scientific classification and recorded risk; show “Review recorded” separately. Default active queue counts include unresolved required reviews across the workspace, regardless of page/filter. Closed cases remain accessible in history and may retain a P1 scientific classification; never relabel them P3 simply because a person reviewed them. An unacknowledged urgent task cannot be hidden by a stage change. The separate event_phase is pre_encounter, post_encounter_pending_verification or verified_outcome_recorded; only an explicit sourced outcome/disposition sets the last value.

Group by workspace + explicit event_key. The JSON import requires this key; the historical adapter namespaces its event_id with the dataset ID. Never merge two providers' events based only on a similar TCA or object names. Cross-provider association requires an explicit supplied association. Reject a report that reuses an event key with a different object pair.

Deduplicate by source_name + source_revision + raw digest. An identical report has no new scientific revision. The same source revision with different content is a source conflict, not an overwrite. Arrival order is not scientific recency: order each source stream by creation time and preserve out-of-order arrivals. An input must state which report set is currently applicable; unresolved competing source claims remain alternatives. Do not average their Pc values.

Change to any material source, policy, candidate, economic assumption or exposure layer creates a new assessment dependency version. A note or assignment change creates audit history without rerunning physics. Source records are immutable. Operator corrections are new revisions identifying what was corrected and why.

## Endpoint surface

| Method and path | Request | Response / behavior |
| --- | --- | --- |
| GET /health | None | Liveness and build ID; no secrets or external calls |
| GET /capabilities | None | Engine/model configuration and supported modes, no credentials |
| POST /workspaces/demo | Seed ID, idempotency key | Isolated synthetic workspace for authenticated or demo identity |
| GET /satellites | Cursor, limit, search | Workspace-scoped page and total |
| POST /satellites | Validated metadata | Created satellite revision |
| PATCH /satellites/{id} | expected_revision, editable metadata | New revision or 409 |
| POST /imports | Canonical JSON, maximum 2 MiB | Per-record acceptance/rejection report and affected case IDs |
| GET /cases | Filters, cursor, limit | Stable queue page, total, urgency counts and revision |
| GET /cases/{id} | None | Current assessment, evidence and case metadata |
| GET /cases/{id}/reports | Cursor | Source-specific immutable history |
| POST /cases/{id}/assess | expected_revision, policy_id | Bounded deterministic assessment |
| POST /cases/{id}/actions | expected_revision, action, rationale, assessment_id | Recorded disposition with updated case |
| POST /cases/{id}/investigate | assessment_id, optional question | Bounded ADK result or visible template fallback |
| POST /fleet/compare | Candidate bundle ID and revision | Bounded comparison result or resumable batch state |
| POST /operations/{id}/continue | continuation_cursor, expected_revision | Process the next bounded batch under a database lease |
| POST /economics/evaluate | EconomicScenario | Formula result, included/excluded items and source bindings |
| POST /reentry/evaluate | ReentryScenario | Exposure and conditional damage outputs |
| POST /communications/simulate | Scenario ID, packet action, expected_revision | Simulation state only |
| GET /operations/{id} | None | Persisted operation status and available result |
| GET /activity | after_sequence, limit | Workspace-scoped activity delta |
| GET /exports/{case_id} | format=json or markdown | Complete versioned evidence packet |
| POST /workspaces/{id}/reset | expected_revision | Reset only this visitor's sandbox to a seed |

All paths except liveness/capabilities require the workspace identity defined by the selected storage mode. A workspace ID in the request is not authorization. Export filenames are server-generated. Reports and scenario inputs are POST bodies, not URLs to fetch.

POST /imports uses ImportBatch: schema_version, expected_workspace_revision and a records array of 1 to 500 canonical input objects, still subject to the total 2 MiB/capacity bounds. Validate the outer envelope first; malformed envelope returns 422. Then validate each record and return an HTTP 200 import summary with accepted, deduplicated, conflicted and rejected counts plus indexed errors. A wholly rejected but well-formed batch has zero accepted records. Stored accepted records and their summary commit atomically; a storage failure rolls them all back. ImportBatch's full structural schema is useful for strict preflight validation, while the runtime parser retains per-record errors instead of letting automatic whole-body validation discard the entire summary.

## Queue behavior

Default page size 50, maximum 100. Sort by urgency ascending (P0 first), then known review deadline ascending with unknown deadline first within its tier, then material concern flag, then case ID. Never sort unknown probability as zero. An analyst can choose alternative display sorts, but the pinned urgent summary remains. Return both filtered result counts and a clearly labeled all-workspace unresolved urgent count.

Pagination cursors carry queue revision and the sort tuple. If time or evidence changes the queue between pages, return 409 QUEUE_CHANGED and ask the client to refresh. This prevents silent skips/duplicates in a moving ranked queue. Snapshot exports can use an immutable queue revision.

## Errors and idempotency

Error shape: code, message, request_id, retryable and field_errors. Use 400 for malformed JSON, 401/403 for identity/permissions, 404 for inaccessible or missing objects, 409 for revision conflicts, 413 for oversized input, 422 for schema/domain input errors, 429 for admission limits and 503 for required infrastructure unavailable. An applicable record with scientifically unsupported calculation is a successful domain response with status unsupported, not an invented number or a generic 500.

POST requests that create revisions or expensive operations accept Idempotency-Key. Persist key, request digest and result reference atomically for 24 hours. Same key/digest returns the original result; a different digest returns 409. Authorization is rechecked on replay. Do not use only process memory for this guarantee on Vercel.

## Persistence implementation rules

Database storage uses separate immutable input/assessment tables and mutable case pointers. Index workspace_id + urgency + deadline, workspace_id + event_key, report source/revision, dependency digest, and operation status/lease expiry. Use a uniqueness constraint for report identity and idempotency keys. Every table containing user data is workspace-scoped.

Writes use one transaction for revision insertion, current pointer change, invalidation and audit event. A transaction or function crash must not publish an assessment pointing to missing inputs. Store small raw synthetic JSON in the database; do not require an object-storage service for the hackathon. The database/auth provider-specific implementation is finalized in documents 14 and 19.

## Cross-field validation and import behavior

Require distinct report object IDs matching the encounter states; interval start < end; unique catalogue IDs; selected object present exactly once; alternatives replacing only that object; candidate IDs unique and different from reserved baseline. State vectors and position covariances use the common epoch/frame declared at the bundle root. The independent covariance model forbids an extra cross-covariance; the supplied-cross-covariance model requires it and a valid full joint matrix. The initial fleet bundle supports independent object errors only; a correlated fleet needs an expanded joint model and is unsupported.

Reentry windows must be ordered; longitude is within [-180,180], latitude within [-85,85], rings are closed and non-self-intersecting, holes are contained, and dateline crossings are unsupported. The combined population/asset point count is at most 1,000, even though each structural array has its own bound. Identical duplicate point IDs deduplicate; conflicting duplicate bodies are rejected. Domain geometry checks supplement the schema and do not guess a corrected polygon.

All monetary terms in a calculation require one currency unless displayed separately. Parse probability JSON numbers through their preserved decimal text for Decimal arithmetic; do not introduce a binary-float rounding step before multiplying money. Store a probability's numeric display and its canonical decimal representation/source reference together. Unknown probability or conditional loss produces an unavailable result rather than zero.

Structural JSON/schema errors reject that record with 422. A structurally accepted report whose complete encounter is scientifically unsupported remains in the ledger with an unsupported calculation finding. A missing encounter is allowed for reported-risk audit, with its missing-evidence findings. Do not discard useful source history merely because the solver cannot run. Report whether a validation error rejected an input or a retained record produced an unsupported result.
