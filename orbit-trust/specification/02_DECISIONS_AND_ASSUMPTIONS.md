# Decision register and defaults

This is the authoritative record of product choices. U denotes an explicit owner decision; D denotes an implementation default selected to complete the handoff; V denotes a requirement needing external verification before release. Defaults are not customer or scientific evidence.

| ID | Kind | Decision |
| --- | --- | --- |
| D01 | U | Build a space-technology hackathon project with substantive mathematics and useful agents |
| D02 | U | Combine conjunction-warning reliability and evidence auditing |
| D03 | U | Lead the demonstration with fleet review and response |
| D04 | U | Include a separate TerraSight-inspired reentry sandbox |
| D05 | U | Groq is the hosted model provider; no paid API credit or GPU |
| D06 | U | Public interactive web demo required |
| D07 | U | Dark navigation, light work panels, restrained status colors |
| D08 | U | Reuse the three owner-supplied repositories selectively |
| D09 | U/D | Owner selected Adhirajsingh2507/devx-engine, already connected to Vercel; orbit-trust/ subdirectory is an implementation default |
| D10 | D | Next.js static export, TypeScript, Tailwind, FastAPI, ADK, PyO3 Rust library |
| D11 | U/D | Owner selected the existing Vercel project; same-origin CDN frontend and FastAPI function is an implementation default |
| D12 | U | Supabase free tier for persistent accounts and case data; no authoritative Vercel filesystem state |
| D13 | D | GitHub OAuth for persistent identity; isolated anonymous demo trial with export/import |
| D14 | D | No shared mutable global demo; no visitor access to another workspace |
| D15 | D | Groq model openai/gpt-oss-20b through LiteLLM; fallback is deterministic templates |
| D16 | D | Two LLM roles: investigation and formatting; domain specialists otherwise use deterministic tools |
| D17 | D | Supplied candidate trajectories only; no live commanding or autonomous burn optimizer |
| D18 | D | Initial numerical domain is short linear encounters with declared Gaussian position uncertainty |
| D19 | D | Historical ESA data is optional local research input, not bundled public demonstration data |
| D20 | D | Primary display currency INR; user-supplied USD scenarios supported without automatic FX conversion |
| D21 | D | All times stored as UTC; demo clock is explicit and separate from wall-clock sessions |
| D22 | D | Release uses a fictional fixed demo clock beginning 2026-09-11T12:20:00Z |
| D23 | D | Runtimes: Python 3.12, Node 22 LTS, pnpm 10; pin compatible patch versions in milestone M0 |
| D24 | D | Rust stable toolchain pinned in M0; no nightly, unsafe custom numerical code or fast-math requirement |
| D25 | D | Test-only NumPy/SciPy reference routines stay out of the production function bundle where possible |
| D26 | D | Public deployment includes only synthetic uploads; real operational/private datasets are local-only |
| D27 | V | Account-specific Groq access, exact quotas, host eligibility and event submission rules must be verified |
| D28 | U | The existing 3d-game/ app is important for future implementation. Preserve its files, assets, dependencies, configuration, history and any deployment; do not remove or repurpose it for ORBIT-TRUST |

## Why these choices differ from the earlier playbook

The earlier report recommended a local CPU model and local-first execution. The owner subsequently selected Groq and required a public web demo. Those selections supersede the earlier recommendation. The prior statements about no public deployment or no fleet comparison are also superseded by the new scope. Scientific cautions, provenance requirements and evidence/urgency separation remain.

Current Groq documentation lists the earlier Finora Llama model as enterprise access. Do not assume the owner's previous default is available on a new free account. The proposed GPT OSS 20B model appears in Groq's free-limit table and supports tool use and strict structured output in separate calls. Access still requires an account check. The model is served by Groq; no OpenAI API account is required. [^02-S08][^02-S09][^02-S10]

The owner explicitly selected Vercel after a preliminary hosting comparison. Render and Hugging Face are not deployment requirements. Vercel supports FastAPI functions and static assets; persistent data belongs in Supabase. Package the numerical extension before function deployment and bound all computation by request lifetime. [^02-S12][^02-S13]

## External inputs without hidden assumptions

The owner will supply Groq/Supabase configuration through secret settings, authenticate account setup and verify the hackathon submission link. The target repository is known; the existing Vercel project settings and Supabase project values require inspection or owner input at deployment. Never request secret values in plain chat. The component lecture does not establish formal judging weights or whether pre-existing code is permitted. Disclose reuse and resolve the organizer's rule before submission.

The reported 29/50 readiness score in earlier research was a subjective assessment, not a release score. Do not carry it into the app as performance evidence. No fabricated customer interviews, live telemetry, loss data or scientifically calibrated confidence intervals are permitted.

## Change control

If a default becomes infeasible, record the failed check and the smallest compatible replacement in a decision log. Do not silently switch to a paid service, remove the public demo, replace ADK with fake traces, merge the reentry sandbox into orbital risk, or declare an unsupported calculation valid. Account provisioning is a release dependency, not a reason to stop unrelated implementation.

Dependency patch versions are intentionally resolved at implementation time because the pack cannot certify a future lockfile. This is a bounded compatibility task: select current non-prerelease versions satisfying the chosen runtime, exclude known compromised releases, run the M0 contract spike, lock and record. It is not permission to redesign the architecture.

## Source notes

[^02-S08]: Groq, [Supported models](https://console.groq.com/docs/models).

[^02-S09]: Groq, [Rate limits](https://console.groq.com/docs/rate-limits).

[^02-S10]: Groq, [Tool use](https://console.groq.com/docs/tool-use/overview) and [Structured outputs](https://console.groq.com/docs/structured-outputs).

[^02-S12]: Vercel, [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), refreshed 11 September 2026.

[^02-S13]: Vercel, [Python runtime](https://vercel.com/docs/functions/runtimes/python) and [Function limitations](https://vercel.com/docs/functions/limitations).
