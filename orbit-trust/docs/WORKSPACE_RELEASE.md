# Utility-first workspace release

## Current interface

The public `/` route is now a two-screen introduction: centered ORBIT-TRUST branding over the ray-traced Earth, followed by a short description and an Enter app link. It does not contain the working tools. The initial brand reveal lasts 1.6 seconds; reduced motion skips it. The app never waits for a staged processing animation.

The persistent layout at `/app/` provides searchable sidebar navigation and workspace search (Ctrl/Cmd K). Every tool has a separate static route: `/app/overview/`, `/app/satellites/`, `/app/orbits/`, `/app/collision/`, `/app/agents/`, `/app/finance/`, `/app/terrain/`, `/app/activity/`, and `/app/methods/`. Old homepage section bookmarks navigate to the corresponding app route. Earlier console routes remain preserved for compatibility.

Page titles are compact. Interactive states include page filtering, case and satellite search, selected-object inspection, orbital Play/Pause and Zoom, analyst note saving, explicit calculation, scenario comparison, trace export and data-request export. The mobile navigation is collapsible and hidden from keyboard focus when closed.

`WorkspaceProvider` retains selected objects, case selection, notes, input assumptions and latest assessment results through client navigation. Refresh resets this in-memory demo. No cloud persistence or account login is claimed. Local findings run immediately on the Run assessment button, then appear in Activity. A selected scenario can change independently of the recorded result; the app asks users to run again when inputs differ.

## Finance

Financial analysis is a dedicated page and sidebar destination. Users edit replacement cost, daily service revenue, loss-scenario downtime, response cost and response-scenario downtime, then choose Calculate exposure. Compare response scenario expands a separate, explicitly conditional calculation. Results disclose stale assumptions and missing insurance/ground exposure. A negative comparison is allowed; the app never turns it into invented positive savings. Export includes assumptions and exclusions.

## Latest main integration

Pulled and merged `origin/main` at `b6d8acf`. Preserved the Python API, Rust crate, fixtures, Supabase migrations and bounded ADK/Groq investigator. Resolved documentation and ignore-file conflicts by retaining both backend and frontend records. Kept `orbit-trust/vercel.json` as the backend configuration so an existing backend deployment is not repurposed as a frontend. GARUDA and the shared engine remain intact.

The new frontend still uses local demonstration calculations. The newly merged backend is present but not connected to this UI. Database migrations were not applied during this frontend release. The UI does not claim authenticated production operations or live telemetry.

## Deployment layout

The frontend build root is `orbit-trust/apps/web`, with the existing `npm run build` command and Next.js static export (`out/`). Its source imports sibling engine code; Vercel must include files outside the root directory. Dependency installation must respect `orbit-trust/pnpm-lock.yaml` and the parent workspace, with no independent regenerated lockfile. Backend settings remain under `orbit-trust/`. Do not change the `physics-sandbox` / GARUDA project.

GitHub records show multiple projects under `techadhiraj07-1630s-projects`. Their names do not reliably identify their contents: the stable `devx-engine-web.vercel.app` domain was inspected after pushing and serves the game, not this frontend. Do not repurpose it. The generated deployment URL redirects unauthenticated users to Vercel login. The correct ORBIT-TRUST frontend project/root must be confirmed with the owner before changing project settings. A successful GitHub deployment status alone does not prove this interface is live.

## Validation performed

- Next production build/static export: passes, 23 generated pages including all nine tool routes.
- Seven deterministic tests: encounter bounds, invariance, nonfinite values, unsupported claims, finance assumptions, negative difference and overflow rejection.
- Playwright desktop: app entry, immediate assessment, 11 Activity events (6 local + 5 historical), finance results retained between routes, workspace search opening RELAY-09, and a 3,072-triangle ray-traced orbital viewport.
- Playwright mobile at 390 × 844: sidebar filter, route selection, edited $20 million replacement assumption giving $20,336,000 conditional loss, response comparison, case search and session note save. No document-level horizontal overflow.
- Screenshots inspected in workspace `artifacts/workspace-*.png`.

The historical `FRONTEND_EXPERIENCE_V2.md` records the superseded single-page design. This document takes precedence for current navigation and interaction behavior.
