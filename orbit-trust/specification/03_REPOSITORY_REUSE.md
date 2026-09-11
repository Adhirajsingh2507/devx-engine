# Source repository inspection and reuse map

All three repositories were accessible through GitHub's public file API on 11 September 2026. Initial browser retrieval failures did not mean the repositories were absent. The observations are a targeted source inspection, not an execution audit or a claim that every file is correct.

| Project | Repository | Inspected revision |
| --- | --- | --- |
| TerraSight | https://github.com/Adhirajsingh2507/terrasight | 2e6445f0639f1d20ce0ad45c98134e9bcc11ea20 |
| Finora | https://github.com/Adhirajsingh2507/Error-404-Not-Found | c66824b8242262bb0f640f4b98ad9067591d29d4 |
| Sajawat | https://github.com/Adhirajsingh2507/sajawat | 600cf5536d8f0b138bdf470e298329213cf1bf57 |

Read the pinned revision first. Compare current default branches before reuse and record differences that affect the selected component. If a revision is unavailable, report it and inspect the current counterpart; never imply the original inspection applies unchanged. Keep source-reuse notices with the extracted components and record their original paths and commits.

## TerraSight

Its README describes stereo/RGB perception for autonomous planetary rovers, terrain classification and construction-site scoring. The inspected `backend/app/pipeline.py` operates on fixture scenes and produces tiles, sites, boundaries and path outputs. This is useful architecture and UI material, but it is not an Earth reentry model.

Reuse the measurement-versus-decision separation from `backend/app/terrain/assemble.py` and `backend/app/scoring.py`. Adapt `frontend/src/components/terrain-grid.tsx`, `site-table.tsx` and `stats-panel.tsx` only after checking their data and coordinate assumptions. Use the API/types files to understand component dependencies. These frontend files were identified in the tree but were not fully audited during this review.

Replace crater-distance, slope, roughness and bearing-score business logic with the reentry sandbox's footprint/exposure model. The existing four zones concern buildability, navigation, geological interest and hazards. “Construction-safe” has no valid interpretation as “safe for debris impact.”

The inspected `_walk_border` routine joins disconnected feature regions with a nearest-neighbor walk. Do not reuse that geometry as an impact polygon: it can bridge separate regions. Use valid GeoJSON Polygon/MultiPolygon boundaries and preserve holes. No-crater sentinel values and local Cartesian grid coordinates must not leak into Earth exposure units.

## Finora

Useful concepts are deterministic specialist calculations, calculation provenance, small tool sets, an intent fast path, bounded loops and a trace. Inspect `backend/formatting.py`, `agents.py`, `orchestrator.py`, `judge.py` and `finance_engine.py` to trace dependencies before reuse.

Its financial engine concerns affordability, EMI, tax, emergency funds, investments and fraud. Those formulas are not satellite-loss models. The inspected engine also uses a fixed date. Replace the domain model and date handling; keep the idea that numbers come from code and carry input/formula provenance.

The inspected judge's `response_ok` primarily checks whether findings are nonempty. Its numeric confidence grows with finding count. Neither establishes factual completeness or calibrated confidence. The `_decision` path generates prose after evaluating those findings; it has no full final-prose validation in that inspected path. Replace these behaviors with document 09's validator and template-bound output.

The inspected specialist tool calls execute in a Python loop. Reuse does not provide parallel numerical processing automatically. Move independent encounter work to the bounded Rust worker pool, while keeping workflow ownership deterministic.

Finora's README documents serverless, stateless conversation tokens and an ephemeral financial store. Do not adopt that store as durable mission data. Use the case ledger and workspace isolation here. Do not carry its Groq/NIM provider fallback or API keys into the new application.

## Sajawat

Inspect `apps/admin/src/app/(console)/crm/page.tsx`, `crm/[id]/page.tsx`, `features/crm/stages.ts`, `features/console/ui.tsx`, `Sidebar.tsx`, `Can.tsx`, the CRM service and corresponding types. The detail screen offers notes, assignment and stage updates, which map well to review cases.

The board requests only 100 leads and groups them in the browser. Replace this with server-authoritative sorting, filtering and pagination. Count all matching cases and all urgency tiers on the server. Do not let browser truncation hide P0/P1 events.

Replace sales stages with the six review stages. Keep urgency as a separate field and allow system-driven reopening. An arbitrary dropdown change must not dismiss a persistent urgent acknowledgement requirement.

The original detail route uses a dynamic path. Our static export uses fixed pages with query parameters, such as `/case/?id=...`; adapt route access accordingly. Extract a small UI subset and its dependencies instead of importing the commerce monorepo, MongoDB, payment system or deployment infrastructure.

## Rights and practical extraction

The implementation target is https://github.com/Adhirajsingh2507/devx-engine. At inspected revision `ad4b9e45b234fe8b4d22d7db3be7c74d46c7a3fd`, the root contains README.md, .gitignore and .mcp.json, with toolkit/reference folders and the `3d-game/` app. The owner identifies this game as an important asset for future implementation. Preserve its source, assets, dependencies, configuration, history and any existing deployment. Do not delete, overwrite, rename, move or repurpose it during the ORBIT-TRUST build. Add `orbit-trust/` alongside it. Future game development/integration needs a separate owner request. No ORBIT-TRUST implementation or root package manifest was identified at the inspected snapshot.

The public tree cannot reveal Vercel's selected Root Directory. Configure orbit-trust only for the intended ORBIT-TRUST deployment; do not repoint or replace an existing game deployment. If the connected project serves the game, resolve the ORBIT-TRUST deployment target with the owner before changing its settings. Shared configuration changes must be additive and preserve the game's build/deployment behavior.

The owner has explicitly requested reuse of these projects. GitHub metadata did not identify a repository license in the inspected snapshots; that is not a license grant for unrelated third-party assets. Preserve contributor notices, inventory copied dependencies and obtain any required contributor/asset permission before publishing copied third-party material. Prefer newly drawn UI and fictional fixtures over copied media.

Write `SOURCE_REUSE.md` in the implementation repository listing source URL, pinned commit, original path, reused behavior, changed behavior and validation. Repo instructions guide work in the relevant source scope; do not import their unrelated automation or multi-agent instructions into ORBIT-TRUST.
