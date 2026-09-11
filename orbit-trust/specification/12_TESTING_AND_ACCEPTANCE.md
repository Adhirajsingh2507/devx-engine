# Test strategy and acceptance catalogue

These are tests to implement, not tests already passed by ORBIT-TRUST. The package itself has separate document/fixture QA. Record every application test result with commit, environment, dependency versions and actual output in BUILD_STATUS and the release report.

## Numerical and policy checks

| ID | Scenario | Acceptance |
| --- | --- | --- |
| T01 | Four isotropic reference encounters | abs error <= max(1e-12, 1e-7 times reference Pc) |
| T02 | Zero miss, isotropic covariance | Match analytic 1-exp(-R^2/(2 sigma^2)) within T01 tolerance |
| T03 | General positive-definite anisotropic fixtures | Match independent Cartesian reference; report convergence |
| T04 | Rotate all states/covariances by one orthogonal matrix | Pc invariant within T01 tolerance |
| T05 | Swap primary/secondary consistently | Same distance/Pc and equivalent policy |
| T06 | Common position/velocity translation | Relative encounter result unchanged |
| T07 | Invalid/singular/asymmetric covariance, missing frame, nonfinite fields | Reject or unsupported as specified; no zero-risk substitute |
| T08 | Very low relative speed, endpoint-only closest approach, unsupported nonlinear declaration | Unsupported method state |
| T09 | Nonconvergent/underflow numerical cases | Explicit failure or precision status, no definitive zero |
| T10 | Increase hard-body radius with same valid inputs | Pc nondecreasing within tolerance |
| T11 | Sigma 200 versus 1000 reference alternatives | Lower Pc under greater uncertainty does not erase conflict |
| T12 | Deadline +40 minutes, >60 minutes, unknown, exact and passed | P1/P2/P1/P1/P0 as specified |
| T13 | Missing optional cosmetic field versus missing material evidence | Only the material gap affects required review |
| T14 | Downgrade after urgent alert | Alert floor remains until latest-version acknowledgement |
| T15 | New material evidence on a closed case | Reopens and invalidates stale packet |

Use a separate implementation for numerical expected values. The reference Python code may use SciPy ncx2 for isotropic cases and adaptive Cartesian quadrature for general cases. Sharing input parsing is acceptable; using the Rust function to generate its own sole oracle is not. Record deterministic sum ordering and tolerance across thread counts; do not require unsupported cross-CPU bitwise floating-point identity.

## Workflow, security and integration

| ID | Scenario | Acceptance |
| --- | --- | --- |
| T16 | Duplicate and reordered reports | No false new scientific revision; source history preserved |
| T17 | Same source revision with different body | Conflict retained, no overwrite |
| T18 | Same event key with different object pair | Rejected association |
| T19 | 205 cases with urgent records after index 100 | All urgent cases accessible; counts accurate |
| T20 | Queue changes during pagination | 409 refresh; no silent skip |
| T21 | Two concurrent edits | One revision wins; stale writer gets 409 |
| T22 | Two visitor accounts and guessed record IDs | No cross-workspace reads, writes, exports or model runs |
| T23 | Direct Data API calls attempting to forge assessment/Pc | Denied by grants/RLS |
| T24 | Function termination midway and retry | No partial valid result, no duplicate financial benefit or action |
| T25 | A-B improvement creates A-C conflict | Candidate one blocked; all pair evidence visible |
| T26 | Catalogue/candidate incomplete or unsupported | No candidate pass |
| T27 | Repeated idempotency key | Same payload returns same result; changed payload gets 409 |
| T28 | No contact, lost acknowledgement, duplicate packet, stale candidate | Correct simulated state, no fake execution |
| T29 | Reference INR economics | 100000 before, 1000 after, 99000 reduction, 79000 net |
| T30 | Mixed currency, missing loss, unsupported Pc, negative net | No unqualified aggregate or fabricated positive savings |
| T31 | Footprint holes, disconnected pieces, boundary points, repeated asset | Correct inclusion and no double count |
| T32 | Invalid/dateline polygon and missing exposure coverage | Reject unsupported geometry or display explicit coverage gap |
| T33 | Missing vulnerability assumption | Exposure available; damage unavailable/partial |
| T34 | Prompt injection in imported text | No tool privilege expansion or policy mutation |
| T35 | Invented finding ID, omitted required finding, wrong template | Reject/fix host packet; no accepted false citation |
| T36 | Groq 429, timeout, absent key, refusal or malformed schema | Deterministic fallback clearly labeled |
| T37 | New assessment during model inference | Old response marked stale |
| T38 | Cold start, browser refresh and sign in on another device | Persistent account sees saved data; no local filesystem dependency |
| T39 | Fresh public browser and auth callback | Live app works; real model trace verified with owner's key |
| T40 | Keyboard and 390/768/1440 px screens | Core workflow accessible, no clipped actions or color-only meaning |

## Agent evaluation

Create 50 frozen prompts: 20 ordinary evidence investigations, 10 missing-data requests, 10 conflicts/changed versions and 10 adversarial/unsupported cases. Label expected permissible tools/templates before evaluation. Report correct selection count, source fidelity, fallback count, latency and token cost. A template-only run cannot pass the live Groq integration requirement. Schema adherence is not proof of useful tool choice.

## Performance protocol

On the actual public tier, measure ten cold-start samples when practical and at least thirty warm repetitions per workload. Warm API target: queue read p95 <=2 seconds for 500 cases, ordinary single encounter audit <=2 seconds, default three-object comparison <=5 seconds and complete normal agent packet <=30 seconds. These are proposed targets, not measured claims or rigid proof of physical timeliness.

Also measure 20-object/4-candidate completion, chunk duration, peak memory, payload sizes, cache hit rate and database calls. A chunk must return before the application budget. Missing targets require profiling and truthful reporting; never hide a timeout by substituting precomputed values. Benchmark sequential reference, sequential Rust, parallel Rust and cached Rust with identical scientific work.

## Expert and customer evaluation limits

Synthetic policy consistency is not professional analyst accuracy. For a later pilot, freeze independent expert required-review labels and compare against a baseline already including quality checks and applicable dilution handling. Track both missed required reviews and excess workload at a stated capacity. Counterbalance task order and avoid letting an analyst repeat the same case in both interfaces.

A 99% recall claim needs appropriate independent cases and confidence bounds. For 299 independent required-review cases with zero misses, a one-sided exact 95% lower bound is about 99.003%; thirty perfect cases only about 90.5%. Correlated report updates cannot count as independent trials. Mean net time saved feeds economics; median time describes typical UX. No such study has yet been completed. [^12-S16]

## Source notes

[^12-S16]: NIST/SEMATECH, [Confidence limits for a proportion](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).
