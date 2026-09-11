# Business model, validation and hackathon presentation

## Positioning

ORBIT-TRUST is an evidence and response-review workspace for teams that already receive conjunction warnings. Its proposed advantage is the connection between changing evidence, review deadlines, supplied fleet response alternatives and a reproducible decision record. It is not a new tracking network or a promise to eliminate orbital collisions.

Start with a flight-dynamics team at a small LEO operator or an outsourced mission-operations provider. The daily user reviews conjunction cases; the operations lead approves workflow purchases; security and flight-dynamics specialists gate operational adoption. A university CubeSat team may be accessible for usability feedback but does not automatically represent a paying commercial buyer.

## Existing alternatives and differentiation test

| Alternative | Evidence available | Consequence for positioning |
| --- | --- | --- |
| Provider alerts plus spreadsheets and internal scripts | A plausible workflow baseline to verify in interviews | Compare against actual review practice, not a deliberately weak Pc-only table |
| Kayhan | Public documentation discusses risk metrics and dilution [^15-S06] | Uncertainty-aware metrics alone are not novel |
| Omitron OwlEye | Markets conjunction/risk assessment and operational support [^15-S21] | Do not claim the first decision-support product |
| Neuraspace STM OPS | Markets operational space-traffic tools [^15-S22] | Workflow automation and maneuver support already have competitors |
| ESA CREAM | Research into collision-avoidance automation [^15-S23] | Automation itself is not sufficient differentiation |

Public marketing establishes advertised capabilities, not completeness, efficacy or a verified feature absence. ORBIT-TRUST's gap hypothesis is easier reconciliation and auditability for an underserved workflow. It needs side-by-side analyst testing. An eventual advantage could be operator-approved adapters, expert-labeled evidence conflicts and integration history; the demo does not yet possess that advantage.

## Proposed commercial model

Sell a team workspace subscription with a defined reviewed-event allowance and support level. A later enterprise tier can add private deployment, provider integrations, access controls and audit retention. Charge for the workflow and support, not a percentage of a claimed satellite saved. Avoid transaction-linked financial promises that the evidence cannot establish.

Initial pricing is an interview hypothesis: a time-limited paid pilot at INR 25,000 per month, followed by a small-team plan around INR 50,000 per month if verified value supports it. These are original proposal numbers, not observed market prices or accepted willingness to pay. Quote taxes, data-provider costs and private-hosting costs separately if applicable. Do not publish a checkout before validating plan eligibility, terms and support costs.

For a labor-value example, 600 reviewed cases/month with a measured mean net reduction of 8 minutes/case produces 80 hours/month. At an explicitly assumed loaded analyst cost of INR 1,500/hour, the modeled labor capacity value is INR 120,000/month. A hypothetical INR 50,000 subscription leaves INR 70,000/month before integration, training and other costs. The case count, time saving and labor rate are assumptions; saved capacity is not automatically a cash payroll reduction.

Contribution per customer equals revenue minus compute/inference, database, licensed data, support and amortized onboarding costs. Keep customer acquisition and general R&D separate. Free hackathon quotas do not prove sustainable margins. No defensible TAM or market-share estimate is currently available; a later bottom-up model should count independently verified qualified operators, realistic annual contract values and reachable conversion rates instead of multiplying every satellite by a price.

## Unit-economics hypotheses

These scenarios are arithmetic illustrations for discovery, not supplier quotes, forecasts or measured business performance. Replace every cost with actual pilot data before investment or pricing decisions.

| Monthly per-customer input or derived metric | Base hypothesis | Stress hypothesis |
| --- | --- | --- |
| Subscription revenue / ARPU | INR 50,000 | INR 50,000 |
| Compute, inference and database allocation | INR 5,000 | INR 10,000 |
| Licensed-data allocation | INR 5,000 | INR 10,000 |
| Support and amortized onboarding | INR 15,000 | INR 20,000 |
| Total cost to serve | INR 25,000 | INR 40,000 |
| Gross contribution / margin | INR 25,000 / 50% | INR 10,000 / 20% |
| Acquisition cost per customer, assumed | INR 100,000 | INR 200,000 |
| Acquisition payback | 4 months | 20 months |
| Retained lifetime, assumed | 24 months | 12 months |
| Simplified contribution LTV | INR 600,000 | INR 120,000 |
| LTV / acquisition cost | 6.0 | 0.6 |

Payback equals acquisition cost divided by monthly gross contribution. Simplified LTV equals monthly gross contribution times assumed retained lifetime; it omits discounting, expansion and changing support burden. At a hypothetical INR 200,000/month fixed operating expense, the base contribution requires eight paying customers just to cover that expense, before acquisition spending. The stress case is unattractive: payback exceeds assumed lifetime. These examples make the support/data-cost risk visible instead of equating free inference with a high-margin business.

The first distribution step is a small set of founder-led operator/service-provider conversations, followed by one to three scoped pilots. Ten customers require repeatable onboarding and a verified budget owner. Reaching a hundred would likely require service-provider distribution and reusable data adapters. A thousand qualified buyers is not assumed in this narrow market. Reentry exposure has a different operational workflow; treat it as an experimental extension until a buyer validates its value, rather than charging the conjunction buyer for every demo feature.

## Customer discovery plan

Conduct 8–12 structured conversations spanning operators and service providers, with permission and without asking for sensitive conjunction data. Ask how they handled their most recent difficult alert; which evidence required clarification; who made the review decision; which system already handles that task; and what integration/security work a pilot would require. Show the three-object reversal only after learning their current process. Do not ask whether they simply like the idea.

For a pilot, agree on expert labels, representative cases, the existing-tool baseline and a stop condition before testing. Measure mean review time, missed required reviews, excess escalations and time to retrieve supporting evidence. Seek written interest in a specific evaluated workflow and a named operational sponsor. No interviews, letters of intent, revenue, contracts or partnerships are claimed in this handoff.

## Three-minute live demonstration

| Time | Action | Message |
| --- | --- | --- |
| 0:00–0:25 | Open queue with source updates and urgent count | A lower reported probability can coexist with unresolved evidence and a review deadline |
| 0:25–0:55 | Inspect case timeline and deterministic findings | The system preserves provenance and explains why this case needs attention |
| 0:55–1:20 | Run ADK investigation; show actual tool trace | The agent selects evidence and drafts a bounded request; policy remains deterministic |
| 1:20–1:55 | Compare baseline and two supplied response candidates | Candidate one helps A-B but creates A-C concern; fleet coverage changes the disposition |
| 1:55–2:15 | Show simulated communication and separate financial example | Acknowledgement is not execution; monetary benefit is conditional expected loss |
| 2:15–2:40 | Open separate reentry sandbox and change footprint | Exposure changes under a supplied footprint; this is not a predicted crash location |
| 2:40–3:00 | Export packet and show measured test results | Every accepted fact is tied to its inputs, assumptions and method |

Keep the INR 79,000 financial example explicitly labeled as a separate economic reference scenario unless the implementation binds it to matching Pc inputs. Do not accidentally associate those probabilities with the fleet fixture's different probabilities. Begin with a pre-seeded workspace; calculations execute on demand. If the provider fails during presentation, show the honest fallback and previously recorded real-run evidence with its date, rather than inventing live agent activity.

## Suggested pitch

“Satellite teams do not just need another warning. They need a defensible review before the deadline. ORBIT-TRUST audits the evidence, keeps urgent uncertainty visible and tests supplied response options against the loaded fleet. In our synthetic example, a response that improves one conjunction creates another. Deterministic calculations catch that change; bounded agents help assemble the evidence request. The separate reentry sandbox reports exposure under stated footprints. We are testing whether this workflow reduces analyst effort without missing required reviews.”

## Submission evidence and judging

The supplied Google ADK PDF explains components; it is not a verified competition rulebook or scoring rubric. Hackathon name, deadline, mandatory services, allowed pre-existing code and submission fields remain unconfirmed. Map the final submission to the actual rules when they are available. Do not invent numerical judging weights or claim Google ADK/Groq compatibility guarantees eligibility.

Prepare the public URL, repository URL and release commit, three-minute recording, architecture diagram, source/license notices, reference checks, measured latency table, real provider trace and clear reuse disclosure. Describe the existing projects as prior work and identify the new domain-specific implementation. Do not claim all components were built during the hackathon if they were adapted from existing repositories.

## Judge questions with defensible answers

Why agents? They choose among bounded evidence tools and organize an information request; deterministic services calculate and enforce policy. Why Rust? It provides a shared tested numerical batch core; performance benefit will be reported from measurements, not assumed from the language. Why not existing products? This is a workflow hypothesis requiring validation against incumbents. Can it prevent a collision? The demo supports review and supplied scenario comparison; it cannot certify or execute a real maneuver. Does the reentry map predict casualties? No: it evaluates exposure under a supplied footprint and optional stated damage assumptions.

Winning cannot be guaranteed. The strongest demonstration is a specific, reproducible decision failure that the application catches, a genuine bounded agent contribution, and clear evidence that the deployed implementation works.

## Source notes

[^15-S06]: Kayhan Space, [Risk metrics](https://app.kayhan.io/docs/key-concepts/risk-metrics/).

[^15-S21]: Omitron, [OwlEye](https://www.omitron.com/owleye/).

[^15-S22]: Neuraspace, [STM OPS](https://www.neuraspace.com/stm-ops).

[^15-S23]: ESA, [CREAM: avoiding collisions through automation](https://www.esa.int/Space_Safety/Space_Debris/CREAM_avoiding_collisions_in_space_through_automation).
