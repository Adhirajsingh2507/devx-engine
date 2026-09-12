# Fleet comparison and communication simulation

## Candidate input and coverage

Accept an immutable candidate set containing a baseline and at most three alternatives for one selected spacecraft, with up to 20 catalogue objects in the public demo. The bundle supplies common-epoch Cartesian state and position covariance for each object, the supported short encounter interval, and candidate planning metadata. All objects are synthetic in the public demo. Alternatives replace only the selected object's state within that interval.

The first demonstration uses three objects with locally linear short arcs. It does not simulate gravity over a complete orbit or derive the candidate from a burn. Candidate positions encode hypothetical supplied outcomes. Label the horizon prominently: “All 3 supplied objects assessed over this 10-second synthetic encounter segment.” Do not shorten this to “Fleet safe.”

Evaluate every unordered pair for each candidate in the small catalogue. A 20-object catalogue has 190 pairs. Reuse unchanged pairs, but include their actual results in coverage. Use the sorted pair key, source revisions, scenario/method versions and horizon in the cache key. Do not add an unvalidated pruning step merely to claim optimization.

## Comparison logic

For each pair, compute supported geometry/Pc and apply the same supplied policy. Return a matrix of candidate by pair containing distance, Pc if supported, material findings and evidence links. A candidate is blocked_by_demo_policy if any applicable pair violates the threshold or a supplied hard feasibility constraint fails. If a required pair/input is unsupported or coverage is incomplete, the result is review_required_incomplete, never a pass. Otherwise it is passes_demo_checks.

The selected object's maneuver capability, command opportunity, planning allowance and candidate feasibility flag must be supplied. A flag proves only that the input asserts feasibility. Expose this distinction as feasibility_basis=supplied_assumption. In initial release there is no onboard propulsion, thermal, attitude or fuel-system validation. Analyst approval records a review choice; it does not promote supplied assumptions into independently verified physics.

Among candidates that pass the declared checks, sort by supplied delta_v_m_s ascending, then supplied response cost, then candidate ID. Unknown cost or delta-v sorts last and remains missing. Do not call the selected candidate globally optimal: it is preferred among the finite supplied alternatives under this comparison rule. Compare safety feasibility before money.

## Synthetic demonstration

The fixture supplies A, B and C with plausible instantaneous orbital-scale positions/velocities, but explicitly models only a short linear segment. Baseline A-B has small miss distance and material concern. Candidate one changes A's supplied position to reduce the A-B concern but coincides with C at closest approach. Candidate two moves A away from both within the supplied segment. The fixture includes independent expected pair probabilities and decision labels.

This demonstrates fleet conflict checking, not automated maneuver synthesis. The UI should let judges switch supplied alternatives, see the affected pair and inspect assumptions. Arbitrary dragging on an orbit graphic must not generate a purportedly executable maneuver.

## Optimization boundaries

Use Rayon inside the Rust core for independent pair jobs, with a bounded worker count. Separate algorithm improvements from language/runtime improvements in the benchmark. Compare the same inputs, tolerance, work and cache state. Report cold-start, uncached compute and cached response separately. Ordered output and stable tie-breaking must not depend on thread completion order.

Do not combine pairwise probabilities into a single “probability of any fleet collision” using a sum or independence formula without a joint event model. Repeated warnings can describe the same encounter, and a single spacecraft loss can appear in several pairs. The initial release interface displays pairwise results and unique case counts. Full-catalog screening, collision cascades and Kessler syndrome simulation are future separate capabilities.

## Communication state machine

Communication runs entirely in a sandbox with scripted packets. States are draft, authorized_for_simulation, waiting_for_contact, sent, acknowledged, execution_reported, expired, failed and cancelled. Only supplied simulation events can move sent to acknowledged and then to execution_reported. The interface uses those exact distinctions. There is no real satellite, radio network or external message connector.

A packet records case/assessment/candidate IDs and revisions, creation/expiry time, channel label and idempotency ID. A new material assessment invalidates an unsent old packet. A stale packet cannot be authorized. The simulator rejects sends outside the supplied contact window and marks packets expired at their explicit expiration. Duplicates return the prior packet state; acknowledgement of one packet cannot acknowledge another.

Feasibility uses supplied end-to-end delays: wait until contact + uplink time + acknowledgement allowance + required action lead time must fit before the supplied action deadline. None of these is derived from Groq token speed or HTTP response time. When input is missing, display timing_unknown. The application cannot promise to protect a spacecraft simply because its calculations finish quickly.

Require the complete uplink interval to fit inside the contact window. If acknowledgement uses the same supplied link, its allowance must also fit that window. Packet expiration is inclusive: at now >= expires_at it is expired. A sent packet with no acknowledgement becomes failed at its acknowledgement timeout and cannot be labeled executed without a valid subsequent simulation event sequence. Cancelling an unsent draft/authorized/waiting packet sets cancelled. A terminal packet is immutable; reset creates a fresh packet ID. The fixture communications.json exercises these distinctions using its own stated clock, separate from the default queue clock.

## Failure cases

Show delayed or absent acknowledgement, lost packet, expired candidate, unavailable contact, impossible supplied planning deadline and conflicting concurrent candidate selections. An analyst can cancel a draft or reset the simulator; this changes only the current workspace. Record all transitions in the audit ledger. In real future integration, the protocol, authorization, command signing and flight-control validation need their own independently reviewed specification.
