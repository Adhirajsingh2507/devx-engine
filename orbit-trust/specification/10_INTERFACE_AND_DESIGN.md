# Mission console interaction specification

## Visual system

Use the owner-selected clean mission console: dark navigation, light work panels and restrained status colors. Sidebar background #111827, work canvas #F4F6F8, panels white, primary text #111827, secondary text #475569, borders #D5DCE5, primary action #1D4ED8. P0/P1 use red text/icons with pale backgrounds, P2 amber and P3 blue/neutral. Green is reserved for a completed software check, never general spacecraft safety. Verify actual contrast in rendered controls.

Use a local/system sans-serif font, 16 px body, 14 px dense table text, 24-28 px page title and 12 px metadata only where legible. Default line height 1.45. Use 8 px spacing increments, 8 px panel radii and minimal shadow. No animated starfield, background music or full-screen 3D globe. The central visual is an evidence timeline or pair comparison that explains a decision.

At desktop widths use a 224 px sidebar and a content width that fills the remainder with 24 px padding. Below 900 px use a collapsible navigation drawer. At 390 px the primary action, case reason and urgency remain readable; wide scientific tables scroll inside their region, not the entire document. Reduced-motion preference disables nonessential animation.

## Navigation and screens

Home offers a short project statement, Start demo, Sign in and a clear synthetic-data notice. A signed-in user returns to their saved workspace. Persistent identity uses GitHub OAuth; Try demo uses Supabase anonymous sign-in with a private workspace. The static shell fetches session data only on the client.

Queue is the default work screen. Top row shows P0/P1 count, evidence issues, pending review and last update. The table columns are urgency, case/object pair, review deadline/slack, reported Pc, evidence state, main reason, assigned analyst and stage. Unknown values use an em dash with “not supplied” accessible text. Full queue counts remain visible beyond pagination. A persistent strip highlights any unacknowledged urgent cases and capacity overflow.

Case detail shows “Why this needs attention” first, followed by deadline, current evidence and recommended review step. Tabs: Evidence, Reports, Response comparison, Economics, Activity. The source timeline distinguishes creation time from reception time and provider streams. A side panel holds assignment, notes, acknowledgement and review disposition. Disable stale-version actions until refreshed; explain the conflict.

Evidence view shows passed/failed/unsupported checks with expandable source fields. An encounter-plane plot shows mean and uncertainty geometry only when inputs support it. Axes have units, source revision and “schematic” label where applicable. Do not render an Earth map from missing absolute coordinates.

Fleet view lists exactly which objects and time interval were assessed. Rows are pairs; columns are baseline and supplied alternatives. Selecting a cell opens its evidence. A candidate that helps A-B while creating an A-C concern displays both changes side by side. Candidate recommendation text says “Preferred among supplied options under demo policy.”

Satellite registry supports name, operator label, maneuver capability, contact-window metadata and economic assumptions. Orbital source records are read-only imports; correcting a scientific input creates a new revision with reason. Do not let a simple edit form silently rewrite a provider report. Archive a satellite only when retaining references; historical case records are never cascade-deleted by a metadata action.

Reentry Sandbox is a separate navigation item with a permanent banner: “Supplied footprint scenario. No reentry trajectory prediction.” Show footprint alternatives, exposure points, legend, coverage and included/excluded counts. Base maps are optional local outlines; no paid map key or runtime map-tile dependency is required. Map selection never sends an orbital maneuver.

Activity shows recorded tool execution, calculation completion, report import, assignment and review changes. It omits raw hidden reasoning. Settings contains display currency, account identity, data export/import and demo reset. Policy edits require a new version with visible history; a public anonymous visitor can change only their isolated sandbox.

## States and accessibility

Every screen has loading, empty, error, stale and partial-data states. A slow model does not replace already available numerical content with a spinner. Provider failure has a small explanation beside the template packet. Infrastructure failure prevents writes and offers retry; it cannot show a false successful save.

Use semantic tables with headers, labeled inputs, visible focus, keyboard-accessible dialogs and action buttons, and an accessible text alternative to every plot/map. Do not communicate urgency by color alone. Avoid automatic focus jumps when queue order changes; announce update counts and let the user refresh. Auto-advancing demo time is off by default.

Destructive sandbox reset requires one in-app confirmation naming that workspace. Editing costs, adding satellites and notes are ordinary reversible actions. A review disposition asks for a rationale because traceability is the product requirement, not because the AI is requesting permission to answer.

## Reuse constraints

Adapt Sajawat's admin component patterns and permission-aware detail interactions, replacing commerce terminology and its 100-record client board assumption. Adapt TerraSight's spatial presentation, not its safety score. Finora's execution trace can inspire the activity view, but do not reuse unvalidated confidence badges or theatrical timing as measured latency.
