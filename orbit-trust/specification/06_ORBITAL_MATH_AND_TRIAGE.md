# Orbital mathematics and deterministic triage

This is a deliberately bounded scientific specification. The implementer must not extend its validity from fixture agreement to arbitrary orbital events. NASA distinguishes screening, assessment and mitigation; ORBIT-TRUST is primarily assessment evidence and review support. [^06-S01]

## Supported encounter model

The input supplies two positions, velocities and position covariances at a common encounter epoch in a common Cartesian inertial frame, plus hard-body radii. initial release accepts GCRF and explicitly synthetic inertial coordinates. Mixed frames, unequal epochs without supplied conversion, unknown covariance basis and undeclared cross-object dependence are unsupported. Do not treat each object's RTN axes as the same frame.

The short encounter assumes straight relative motion, approximately constant projected covariance, independent Gaussian position errors (unless a complete cross-covariance is supplied), and a combined circular hard-body region. Velocity uncertainty is neglected by this particular method and must be declared. Slow, repeating/co-orbital and long nonlinear encounters require another validated method and are not silently forced into this one.

The canonical JSON is the complete-input path. Historical ESA CSV provides reported-risk replay and audit only where field conventions are established. initial release does not claim a complete CCSDS CDM parser or full standard conformance. A future KVN/XML adapter must be a separately tested addition. [^06-S04]

## Geometry and probability

Let r = r_secondary - r_primary and v = v_secondary - v_primary. For a supplied linear segment, the unconstrained time of closest approach relative to the epoch is tau = -(r dot v)/(v dot v). Require it to lie inside the declared supported interval; a clipped endpoint is not a completed encounter for this 2D calculation. At a supplied TCA, check orthogonality with |r dot v| <= 1e-8 max(1, |r||v|); otherwise recompute within the supported synthetic segment or mark the direct-TCA input inconsistent.

For independent errors, C_rel = C_primary + C_secondary in the common frame. With supplied cross covariance C_ps, use C_primary + C_secondary - C_ps - transpose(C_ps). The complete joint covariance must pass validity checks; a random cross term must not be accepted because the projected result happens to look positive.

Construct the encounter-plane basis deterministically. Set n = v/|v|. Select the Cartesian unit axis least aligned with n (ties x, then y, then z); set e1 = normalize(axis cross n), e2 = n cross e1. Project the closest-approach vector and relative covariance onto rows e1, e2 to obtain mean m and 2 by 2 covariance S. Combined radius R is the sum of the two supplied radii, never a diameter or radar cross section substituted without evidence.

Pc is the integral of the 2D normal density with mean m and covariance S over x*x + y*y <= R*R. Implement deterministic Gaussian quadrature over polar coordinates, including the radial Jacobian. Compare a 64 radial by 128 angular grid with 128 by 256. Accept numerical convergence only if the absolute difference is <= max(1e-12, 1e-7 times the refined Pc). Use the refined value. If it fails, try 256 by 512 once; otherwise return numerical_nonconvergence. Precompute quadrature nodes and weights from a tested algorithm/library, not hand-entered approximate constants.

Use a Cholesky solve and log normalization to avoid explicit matrix inversion when evaluating the density. If floating-point underflow yields zero without an error bound, report below_computable_precision with null authoritative Pc; do not claim impossible collision. Positive tiny values can be displayed using scientific notation. Never round a probability before evaluating policy.

These tolerances are numerical engineering defaults, not physical uncertainty estimates. Relative speed below 1 m/s, nonpositive projected covariance, projected condition number above 1e6, invalid radius, unknown units or missing applicability declarations are unsupported in initial release. Raising these limits requires new reference cases and an explicit method version.

## Covariance checks

Require symmetric input within 1e-10 max(1, infinity norm of C) in the declared units. Material asymmetry is invalid. Do not silently repair covariance. The initial method accepts positive-definite matrices; singular positive-semidefinite matrices may be physically meaningful but are unsupported by this solver. Check finite entries, nonnegative variances and correlations in [-1,1]. A correlation of 1 can lead to singularity and must not be passed to inversion.

When standard deviations and correlations are explicitly defined, reconstruct C_ij = rho_ij sigma_i sigma_j. Covariance scale a multiplies variance, so standard deviation scales by sqrt(a). Store the original input and the declared scenario transform. Algebraic validity does not demonstrate covariance realism; that requires empirical orbit-error or residual evidence. [^06-S05]

## Checked reference fixture

For m=(100,0) m, R=10 m and S=sigma squared times identity, the following values were independently checked by Cartesian and polar integration during preparation of the preceding playbook. They are reference facts for a synthetic encounter, not an operational engine benchmark.

| Combined sigma in m | Pc |
| --- | --- |
| 20 | 8.71274018586874e-7 |
| 50 | 0.002733592576274527 |
| 200 | 0.0011025180765032241 |
| 1000 | 4.9749386433385265e-5 |

Use an independent SciPy noncentral-chi-square reference for isotropic cases and a separate Cartesian integration for general cases. Test the exact zero-miss isotropic result Pc = 1 - exp(-R squared/(2 sigma squared)). Full test tolerances are in document 12. Probability dilution is an established phenomenon, not a novelty claim. [^06-S06]

## Triage policy version demo-2.0

Review threshold theta = 1e-4, immediate-review slack = 3600 seconds. These are illustrative mission policy choices, not universal operational instructions. Material concern is true when an applicable provider or supported recomputation crosses theta, a declared applicable scenario crosses theta, or a mission-specific supplied override requires review. Missing information needed to classify concern also requires review, but does not assert high collision probability.

| Tier | Condition | Display |
| --- | --- | --- |
| P0 | Required unresolved review and current time is later than its known review deadline | Overdue review; persistent escalation |
| P1 | Required review and deadline unknown, or slack <= 3600 seconds | Review now; exact reason and remaining time |
| P2 | Required review and known slack > 3600 seconds | Scheduled review; owner and checkpoint |
| P3 | No material concern, usable applicable evidence and stable outcome across the declared supported scenarios | Monitor; next checkpoint and reopening conditions |

An optional cosmetic field is not material. Unusable covariance needed for a recomputation cannot become Pc=0. Valid reported risk may still support a review requirement while recomputation is unsupported. A provider-neutral label does not imply independent observations.

The review deadline is a supplied latest feasible command opportunity minus the supplied review/coordination allowance. Do not invent it from TCA alone. Fixture: command opportunity 14:30 UTC, review allowance 90 minutes, review deadline 13:00 UTC; at 12:20 UTC, slack is 40 minutes and a required case is P1. At exactly the deadline it is P1; after it, P0.

TCA passing does not prove no collision. The separate event_phase becomes post_encounter_pending_verification, and unresolved required review is retained until a human records an appropriate disposition. This is not an extra workflow stage or an automatic case closure. Historical post-TCA rows are excluded from predictive evaluation, separately from this workflow rule.

## Evidence audit rules

The canonical evidence_metadata distinguishes orbit-solution epoch and last-observation time from the propagated encounter epoch. Age at the review clock is now minus the corresponding supplied solution/observation time. Never calculate orbit age from the future TCA state epoch, or infer it from ESA observation offsets with unresolved sign conventions.

Demo defaults require solution and last-observation metadata no older than 21,600 seconds; values over that limit produce material stale-evidence findings. This six-hour rule is a fictional configurable review policy, not a universal orbit-quality threshold. Missing required metadata, unknown maneuver information, or an unverified covariance-realism basis produce material missing-evidence findings. Future observation/solution timestamps more than five seconds beyond the scenario clock produce an inconsistency; the five-second tolerance is a declared demo input allowance. The synthetic_assumption covariance basis is usable only in synthetic mode, with a persistent notice that realism has not been established for real objects. Operator_declared means a supplied assertion requiring its source reference, not independent calibration.

Use stable finding codes: MISSING_FRAME_EPOCH, INVALID_COVARIANCE, UNSUPPORTED_ENCOUNTER, STALE_SOLUTION, STALE_OBSERVATION, MISSING_OBSERVATION_METADATA, FUTURE_EVIDENCE_TIME, COVARIANCE_REALISM_UNVERIFIED, MANEUVER_CONTEXT_UNKNOWN, SOURCE_REVISION_CONFLICT, RISK_THRESHOLD_EXCEEDED, SCENARIO_CLASSIFICATION_CONFLICT and DEADLINE_UNKNOWN. Each finding includes object/report IDs, source JSON pointer, observed value or missing marker, rule version, material flag and host-rendered text. A deadline gap affects timing classification, not the numerical integration.

Optional supported covariance sensitivity scenarios are declared inputs, not an exhaustive search or a new independent observation. For the four-sigma reference, explicitly identify the selected alternative(s) and compare their policy classifications. Changing sigma from 200 to 1000 lowers Pc below the demo threshold; that alone cannot clear an urgent floor or resolve a stated uncertainty conflict.

## Escalation and acknowledgement

Store proposed_urgency separately from unresolved_alert_floor. Automatic updates can raise urgency immediately. A lower recommendation does not silently clear an unacknowledged P0/P1 alert. An analyst action must reference the latest assessment and provide a rationale to clear that floor. Closing a case requires a disposition and latest-version acknowledgement. New material evidence reopens it as Reviewing; duplicates and cosmetic metadata do not.

Capacity limits never hide required reviews. Top-K evaluation is an analysis metric, not permission to delete overflow. Show overload counts and an escalation instruction when required reviews exceed configured capacity. Economic value cannot lower a required safety review.

## Source notes

[^06-S01]: NASA, [Spacecraft Conjunction Assessment and Collision Avoidance Best Practices Handbook](https://ntrs.nasa.gov/citations/20230002470), 2023; NASA CARA, [Close Approach Risk Mitigation](https://www.nasa.gov/cara/step-3-close-approach-risk-mitigation/).

[^06-S04]: CCSDS, [Conjunction Data Message, 508.0-B-1 with corrections](https://ccsds.org/Pubs/508x0b1e2c2.pdf).

[^06-S05]: NASA NTRS, [Covariance realism research record](https://ntrs.nasa.gov/citations/20160010501).

[^06-S06]: Kayhan Space, [Risk metrics](https://app.kayhan.io/docs/key-concepts/risk-metrics/).
