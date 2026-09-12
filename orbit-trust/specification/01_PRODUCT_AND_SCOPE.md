# Product requirements and scientific boundaries

## Problem and buyer

Satellite operations analysts receive evolving conjunction reports. They must determine which event needs attention, whether the evidence supports the assessment, and what can still be done before the relevant review and command deadlines. A queue sorted only by reported collision probability can obscure important uncertainty and timing issues.

The primary user is a flight-dynamics or orbital-safety analyst. The first buyer hypothesis is the head of mission operations at a small commercial LEO operator that already receives conjunction data. Flight-dynamics service firms are an adjacent customer channel. Satellite count alone does not establish need: recurring review effort and an inadequate existing workflow do.

ORBIT-TRUST answers: which case needs review, why, which evidence is missing, how supplied response options affect the supplied fleet, and what the stated financial consequences are. It preserves human responsibility for operational choices.

## Required capabilities

| ID | Requirement | Visible proof |
| --- | --- | --- |
| R01 | Import canonical encounter JSON and historical ESA CSV in local research mode | Import report with accepted, rejected and unsupported records |
| R02 | Group explicit event IDs and preserve report revisions | One case with source-specific history |
| R03 | Audit evidence separately from urgency | Two independent status fields with reasons |
| R04 | Compute supported short-encounter probability in Rust | Reference-checked result and method record |
| R05 | Apply deadline-aware P0-P3 review policy | Urgent uncertain case remains visible |
| R06 | Compare supplied response alternatives across loaded objects | A-B improvement rejected when A-C worsens |
| R07 | Simulate communication feasibility and status | Sent, acknowledged and executed are separate |
| R08 | Compute conditional loss and expected-loss change | Inputs, formula, currency and limitations visible |
| R09 | Provide a separate reentry exposure sandbox | Supplied footprint changes exposure totals |
| R10 | Run bounded ADK investigations through Groq | Recorded tool calls and version-bound output |
| R11 | Validate both tool results and report output | Invalid citations or actions cannot enter accepted packet |
| R12 | Provide queue, case, satellite and activity workflows | Add/edit metadata, assign, note, review and export |
| R13 | Survive provider failure without losing calculations | Deterministic results remain available |
| R14 | Work at a public web URL | Fresh-browser live demonstration |
| R15 | Preserve reproducibility and traceability | Exported bundle reproduces the assessment |
| R16 | Meet accessibility and bounded resource requirements | Keyboard flow, responsive views and measured budgets |

## Scope boundaries

The core accepts assessments; it is not a global tracking or conjunction-screening service. It does not discover every orbital object. Fleet assessment covers exactly the supplied catalogue, trajectories and time interval. The initial physics engine supports the explicitly declared short linear Gaussian encounter model, not arbitrary orbital propagation.

Response candidates are supplied trajectories with planning assumptions. The software can compare their encounter consequences and check the supplied timing constraints. It does not infer a feasible burn from a slider or optimize a real maneuver. All maneuver-like actions in the demo are simulation records.

The reentry sandbox starts with an externally supplied or synthetic footprint. It does not compute atmospheric breakup, fragment survival, drag or reachable landing corridors. It does not route falling debris using rover navigation. ESA describes reentry analysis as including trajectory, surviving fragments and population risk; a terrain score does not replace those inputs. [^01-S02][^01-S03]

Financial outcomes are conditional models. The existence of a costly spacecraft does not mean a warning implies the entire spacecraft value has been saved. A collision-free outcome alone cannot establish the effect of a particular maneuver or software product.

## User journeys

An analyst opens the queue, selects an urgent case and sees the specific source conflict. They inspect report revisions, request a bounded investigation and receive an evidence-linked information-request draft. They compare two supplied response candidates and observe that one creates a new fleet concern. They record a review disposition, retaining the assumptions and assessment version. A new material report reopens review and invalidates stale explanations.

A judge opens a separate Reentry Sandbox tab. A persistent label identifies the scenario as synthetic. Two supplied footprints cover different fictional exposure points. The interface updates the exposed population and asset-value totals. Damage estimates appear only for explicitly supplied probability and vulnerability assumptions. This branch cannot change orbital queue priority.

## Success and claims

Implementation success means all required capabilities have passing acceptance evidence and the public interactive demo works. Scientific success is narrower: reference agreement within the supported calculation domain. Business success requires separate analyst and buyer evidence, which is not currently available.

Measure required-review recall, unnecessary review burden, time to a defensible disposition, output fidelity, cache behavior, latency and memory. Do not substitute a visually impressive map or agent animation for these results. The competitive claim is reduced review effort and clearer reconciliation; it remains a hypothesis until compared against a strong existing workflow.

## Language shown to users

Use “Review now,” “Evidence incomplete,” “Calculation unsupported,” “Candidate passes demo checks,” “Simulation acknowledgement,” and “Estimated change in expected loss.” Avoid “Safe satellite,” “Collision certain,” “Crash location,” “Optimal escape,” “Guaranteed savings,” or a numerical confidence percentage based on agent agreement.

## Source notes

[^01-S02]: ESA, [Reentry background](https://www.esa.int/content/view/full/413425).

[^01-S03]: ESA, [Re-entry safety](https://technology.esa.int/page/re-entry-safety).
