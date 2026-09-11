# Deployment and operations runbook

## Deployment target and configuration gate

The existing repository is https://github.com/Adhirajsingh2507/devx-engine. It contains toolkit resources and the important 3d-game/ app reserved for future implementation. Preserve the game's files, assets, configuration and any existing deployment. Use orbit-trust/ as the intended Root Directory for the ORBIT-TRUST deployment only. The existing project's actual ID, linked branch, preset, Root Directory, deployment protection and environment variables have not been inspected through the owner's account. Record and verify them before changing a live project. If that project serves the game, keep it intact and resolve a distinct ORBIT-TRUST deployment target with the owner before changing settings.

Keep one Vercel project for the ORBIT-TRUST frontend/backend composition; this does not authorize consolidating or replacing a game deployment. Next.js exports the fixed page list to static files; root app.py exposes FastAPI; exported assets are copied into public/ for CDN delivery. Vercel documents FastAPI detection and a single Python function, with public/ used for static assets. The build must demonstrate correct precedence for /api/v1/* and the fixed web routes. A blanket HTML fallback for API failures is forbidden. [^14-S12]

Use a reproducible build script with a frozen pnpm lockfile. It builds apps/web, copies the export into the app root's public directory and verifies every expected route. Do not set the Vercel preset to Next.js merely because the UI uses Next.js: the selected project entry is the FastAPI/static composition. Verify the current framework preset, build command and output handling in M0 instead of inventing a known-working vercel.json. Keep the successful configuration in deploy/ with the tested Vercel CLI version.

## Native Rust packaging

Build the PyO3 extension with a pinned maturin toolchain in Linux CI for the exact Python/runtime architecture selected in M0. Prefer a compatible manylinux wheel with no unbundled external libraries. Name the artifact by package version; record wheel SHA-256, source-tree digest, Rust version, target, Python ABI and dependency lock hashes in vendor/wheels/build-manifest.json.

The deployable commit must already contain the tested wheel and manifest before Vercel's automatic deployment runs. A race in which CI builds the wheel after the same commit has auto-deployed is not acceptable. Prepare the wheel on the implementation branch, commit it with the matching source, verify it in CI, and only then promote that commit. A subsequent source change requires a new matching artifact. Keep a strict small-artifact limit and use a versioned authenticated artifact store later if native bundles become large.

Install the wheel during Python dependency installation. Do not rely on compiling Rust in an unspecified build stage after Vercel has already installed Python requirements. Verify extension import and an independent reference case on Linux and the actual preview runtime. Local Windows development uses a Windows-compatible build, never the Linux wheel. Pin releases and verify hashes; do not download arbitrary binaries from a user-supplied URL. [^14-S13][^14-S20]

## Environment variables

| Name | Scope | Meaning |
| --- | --- | --- |
| NEXT_PUBLIC_SUPABASE_URL | Browser/build | Supabase project URL |
| NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY | Browser/build | Public client key; grants/RLS still enforce access |
| SUPABASE_URL | Server | Same project endpoint |
| SUPABASE_SERVICE_ROLE_KEY | Server secret | Restricted use for validated transactional RPC writes; never bundle |
| GROQ_API_KEY | Server secret | Owner's free-tier key |
| GROQ_MODEL | Server | Raw provider model ID; default openai/gpt-oss-20b if available |
| ADK_LITELLM_MODEL | Server | Adapter ID groq/openai/gpt-oss-20b |
| APP_PUBLIC_ORIGIN | Server | Exact approved public origin |
| APP_MODE | Server | public_synthetic for submission |
| POLICY_VERSION | Server | demo-2.0 |
| APP_REQUEST_BUDGET_SECONDS | Server | 45; persistence reserve is 5 |
| ORBIT_CORE_THREADS | Server | 1 initially; change only with measurement |
| GROQ_ENABLED | Server | Explicit integration switch, false yields labeled fallback |

Store only placeholders in .env.example. Use separate local, preview and production values. Do not print credentials in logs, health checks, traces or generated reports. Supabase may expose newer server secret key names; the variable above is an application convention, not a requirement to use a legacy key type. Map a supported server credential deliberately and keep its use on the backend.

## Supabase setup and login

Create/select the owner's free project, apply migrations, verify grants/RLS and seed only original synthetic templates. Enable anonymous sign-ins for immediate isolated trial access. Enable GitHub OAuth for persistent accounts; configure a GitHub OAuth application's callback to the exact Supabase Auth callback URL shown in its dashboard. Keep that OAuth client secret in the provider configuration, not frontend code. Add the final public app callback and explicit local/preview callbacks to Supabase's allowed redirect list. [^14-S17][^14-S27]

The statically exported /auth/callback/ page uses the browser Supabase client with a tested PKCE flow and exchanges the returned code. It is a client page, not a Next.js server route handler. Test refresh, errors, sign-out, another browser and the anonymous-to-persistent transition. Prevent arbitrary external return URLs; allow only known local paths.

Anonymous identity is still a Supabase authenticated user. A lost browser session cannot be treated as a recoverable persistent account. Offer explicit export before sign-out. In version 2.0, signing into an existing GitHub account opens that account's workspace; it does not silently merge the anonymous one. Offer validated export/import to move synthetic case inputs, with fresh runtime IDs and preserved source lineage. This avoids ambiguous account linking while satisfying persistent accounts. [^14-S17]

Authentication, JWT expiry, quotas, leases and retention use actual UTC wall time. The fictional demo clock only affects scenario calculations and review deadlines.

## Runtime and quota controls

Set a verified Vercel function duration above the 45-second application budget; 60 seconds is the initial configuration target if supported by the resolved entrypoint/plan. Stop expensive work before the persistence reserve. Check current Python bundle and response limits at build time, and keep archives/training dependencies outside the deployment. No paid service is provisioned automatically. [^14-S13]

Use the database for one active operation per workspace, one global live Groq run, admission counts and expiry. Distinguish application runs from provider requests: allow at most three investigate runs per minute per user, ten per UTC day for anonymous users and fifty for persistent users; each run has the tighter provider-call/token limits in document 09. These are additional caps, not a guarantee of provider capacity. Enforce a shared daily provider token reservation below the actual account allowance; release unused reservation after accounting. Retry at most once within the remaining run budget, respect Retry-After and otherwise show fallback. [^14-S09]

Add signup abuse controls supported by the chosen Supabase plan, such as CAPTCHA, and cap workspace creation to one active demo workspace per identity. Anonymous churn means user limits alone cannot protect the key; global provider admission and fail-closed quotas are required. Never use recurring artificial traffic to evade free-project pause behavior. Show a useful unavailable message and restoration runbook instead. [^14-S19]

Vercel Hobby restricts use to personal, non-commercial use. Verify that the actual hackathon deployment qualifies; a later paid commercial pilot needs an eligible hosting plan and operating budget. This does not establish that a commercial product can operate indefinitely at zero cost. [^14-S26]

## Release and recovery

1. Create a preview from the deployable commit. Apply backward-compatible migrations to the appropriate database environment; never reset production to run tests.
2. Verify extension import, authentication, two-user isolation, metadata persistence, default encounter, fleet reversal, finance, reentry, real Groq trace and API/static routing.
3. Record cold/warm results and quotas. Confirm the public judge URL does not require Vercel team login. Restrict preview secrets and avoid making private test cases public.
4. Promote the verified commit through the existing deployment workflow; record the production URL and release ID. Smoke test from a fresh browser.
5. If release fails, roll back application deployment to a known compatible commit. Do not undo additive migrations by dropping data. Restore from a tested export/backup only with an explicit recovery procedure.

Export a synthetic demo backup before judging. Free-plan backup features vary; confirm actual facilities, and keep a manual versioned JSON export sufficient for the demo. Redact tokens and personal data from incident records. Retain anonymous inactive workspaces for 7 days and agent trace metadata for 30 days as proposed app policy; implement deletion through a documented owner-run maintenance action initially, not a hidden continuously running worker. Persistent accounts retain case data until owner deletion, with the stated public per-workspace limits. Implement delete-workspace/account UI only with explicit confirmation of that concrete destructive action.

## Deployment failures to diagnose

Wheel import error: inspect ABI/architecture/library dependencies and manifest; do not return fake values. Static route 404: inspect export tree and route precedence. OAuth loop: compare exact origins/callbacks and PKCE storage. Database 403: inspect grants, membership and JWT, not a blanket RLS disable. Groq 429: inspect account limits and admission counters. Function timeout: inspect bounded chunk size and response checkpoint, not a background thread. Existing game replaced unintentionally: restore the prior Vercel Root Directory and select the intended project with the owner.

## Source notes

[^14-S09]: Groq, [Rate limits](https://console.groq.com/docs/rate-limits).

[^14-S12]: Vercel, [FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi), refreshed 11 September 2026.

[^14-S13]: Vercel, [Python runtime](https://vercel.com/docs/functions/runtimes/python) and [Function limitations](https://vercel.com/docs/functions/limitations).

[^14-S17]: Supabase, [Anonymous sign-ins](https://supabase.com/docs/guides/auth/auth-anonymous).

[^14-S19]: Supabase, [Billing on Supabase](https://supabase.com/docs/guides/platform/billing-on-supabase).

[^14-S20]: PyO3, [Guide](https://pyo3.rs/main/); Rayon, [API documentation](https://docs.rs/rayon/latest/rayon/).

[^14-S26]: Vercel, [Hobby plan](https://vercel.com/docs/plans/hobby), refreshed 11 September 2026.

[^14-S27]: Supabase, [Login with GitHub](https://supabase.com/docs/guides/auth/social-login/auth-github), refreshed 11 September 2026.
