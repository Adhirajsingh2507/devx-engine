# Sources and evidence register

Sources were inspected during the project research and refreshed where deployment choices changed, through 11 September 2026. S-numbers are stable source identifiers used throughout this package. Official pages can change: recheck provider/runtime details during M0. Scientific equations and demo-policy choices are specified separately from provider recommendations.

| ID | Publisher and source | Use and limitation |
| --- | --- | --- |
| S01 | NASA, [Spacecraft Conjunction Assessment and Collision Avoidance Best Practices Handbook](https://ntrs.nasa.gov/citations/20230002470), 2023; NASA CARA, [Close Approach Risk Mitigation](https://www.nasa.gov/cara/step-3-close-approach-risk-mitigation/) | Operational risk review and mitigation context; not an endorsement of the demo policy |
| S02 | ESA, [Reentry background](https://www.esa.int/content/view/full/413425) | Reentry is a distinct physical problem; does not supply this demo's footprint |
| S03 | ESA, [Re-entry safety](https://technology.esa.int/page/re-entry-safety) | Trajectory, fragment survival and population-risk context |
| S04 | CCSDS, [Conjunction Data Message, 508.0-B-1 with corrections](https://ccsds.org/Pubs/508x0b1e2c2.pdf) | Standard message context; this release accepts a smaller canonical JSON contract and is not a full standards-compliant parser |
| S05 | NASA NTRS, [Covariance realism research record](https://ntrs.nasa.gov/citations/20160010501) | A mathematically valid covariance is not automatically a calibrated error distribution |
| S06 | Kayhan Space, [Risk metrics](https://app.kayhan.io/docs/key-concepts/risk-metrics/) | Risk/dilution context and evidence that incumbent tooling discusses this issue |
| S07 | Google ADK, [LiteLLM integration](https://adk.dev/agents/models/litellm/) | Adapter selection and dependency security notice; exact package combination still requires integration testing |
| S08 | Groq, [Supported models](https://console.groq.com/docs/models) | Candidate provider model availability; actual account access must be verified |
| S09 | Groq, [Rate limits](https://console.groq.com/docs/rate-limits) | Provider admission constraints, not guaranteed free capacity for every account |
| S10 | Groq, [Tool use](https://console.groq.com/docs/tool-use/overview) and [Structured outputs](https://console.groq.com/docs/structured-outputs) | Separate tool investigation and schema-constrained formatting; verify model support |
| S11 | Google ADK, [Workflow agents](https://adk.dev/agents/workflow-agents/) | Orchestration concepts; runtime behavior depends on locked versions |
| S12 | Vercel, [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), refreshed 11 September 2026 | Python app detection, static assets and deployment composition; M0 verifies the combined build |
| S13 | Vercel, [Python runtime](https://vercel.com/docs/functions/runtimes/python) and [Function limitations](https://vercel.com/docs/functions/limitations) | Packaging/runtime constraints; inspect live limits rather than assuming a persistent server |
| S14 | Next.js, [Static exports](https://nextjs.org/docs/app/guides/static-exports) | Static UI shell and unsupported dynamic server features |
| S15 | ESA Kelvins, [Collision Avoidance Challenge data](https://kelvins.esa.int/collision-avoidance-challenge/data/) and [Rules](https://kelvins.esa.int/collision-avoidance-challenge/rules/) | Historical replay dataset; aggregate archive audit included, raw data and redistribution rights not bundled |
| S16 | NIST/SEMATECH, [Confidence limits for a proportion](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) | Exact-binomial confidence context; correlated report rows are not independent trials |
| S17 | Supabase, [Anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous) | Anonymous identity, persistence and abuse-control considerations |
| S18 | Supabase, [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security) | Client authorization model and service-key caveats |
| S19 | Supabase, [Billing on Supabase](https://supabase.com/docs/guides/platform/billing-on-supabase) | Plan facilities and limits; verify actual project status and do not assume perpetual free uptime |
| S20 | PyO3, [Guide](https://pyo3.rs/main/); Rayon, [API documentation](https://docs.rs/rayon/latest/rayon/) | Native Python binding and bounded parallel batch design |
| S21 | Omitron, [OwlEye](https://www.omitron.com/owleye/) | Advertised competing operational capability; efficacy not independently tested |
| S22 | Neuraspace, [STM OPS](https://www.neuraspace.com/stm-ops) | Advertised competing workflow; no claim of absent features |
| S23 | ESA, [CREAM: avoiding collisions through automation](https://www.esa.int/Space_Safety/Space_Debris/CREAM_avoiding_collisions_in_space_through_automation) | Existing research direction in automation |
| S24 | Adhirajsingh2507, repository snapshots in document 03 | Source-level reuse assessment, not executed application verification |
| S25 | Sitam Meur / ML Kolkata, Google ADK, component by component, 11 September 2026; supplied file google-adk-component-by-component (1).pdf, 20 pages | Supplied component deck, especially pages 4-9 for agents, tools, schema and workflows; bundled for context, not the competition rulebook |
| S26 | Vercel, [Hobby plan](https://vercel.com/docs/plans/hobby), refreshed 11 September 2026 | Personal/non-commercial restriction and account limits |
| S27 | Supabase, [Login with GitHub](https://supabase.com/docs/guides/auth/social-login/auth-github), refreshed 11 September 2026 | OAuth provider/callback setup; adapt examples to a client-rendered static callback |

## Repository snapshot evidence

- [TerraSight at 2e6445f0639f1d20ce0ad45c98134e9bcc11ea20](https://github.com/Adhirajsingh2507/terrasight/tree/2e6445f0639f1d20ce0ad45c98134e9bcc11ea20): terrain/scoring and pipeline review.
- [Finora at c66824b8242262bb0f640f4b98ad9067591d29d4](https://github.com/Adhirajsingh2507/Error-404-Not-Found/tree/c66824b8242262bb0f640f4b98ad9067591d29d4): finance engine, judge and orchestrator review.
- [Sajawat at 600cf5536d8f0b138bdf470e298329213cf1bf57](https://github.com/Adhirajsingh2507/sajawat/tree/600cf5536d8f0b138bdf470e298329213cf1bf57): CRM queue/detail component review.
- [devx-engine at ad4b9e45b234fe8b4d22d7db3be7c74d46c7a3fd](https://github.com/Adhirajsingh2507/devx-engine/tree/ad4b9e45b234fe8b4d22d7db3be7c74d46c7a3fd): tree and target repository structure review.

The GitHub pages and inspected source text do not prove license clearance, build success or security. Preserve author attribution and confirm owner rights before redistributing adapted source. A missing detected license is not evidence that arbitrary public code may be copied without conditions.

## Observation, proposal and unresolved evidence

Observed: repository structure and cited source snippets; ESA aggregate archive statistics; independent numerical reference agreement recorded under reference/. Proposed: thresholds, capacity limits, design, pricing, application architecture, retention and latency targets. Unverified: live application, actual Vercel settings, selected package interoperability, real operator benefit, reentry footprint validity, customer's willingness to pay and hackathon eligibility rules.

The original research role and engineering lecture priorities are summarized in reference/OWNER_BRIEF.md. Attached-document instructions were treated as material to evaluate, not as tool-use authority. This package deliberately carries the resulting requirements and their limits rather than conflicting obsolete implementation assumptions.
