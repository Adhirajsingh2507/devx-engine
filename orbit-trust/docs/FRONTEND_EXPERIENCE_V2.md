# Earth and mission experience

Implemented September 12, 2026 in `orbit-trust/apps/web`. Run the existing `npm run dev` command there; this session serves `http://localhost:3000/`. No packages were installed or changed for this milestone.

## Experience

The homepage progresses through an arrival sequence, Earth close-up, scroll-controlled pullback to monochrome Earth and red satellite paths, then four mission chapters. The existing review queue and case workspace remain accessible.

| Destination | Behavior |
| --- | --- |
| `/` | NASA Earth ray tracing; hover, keyboard focus or click satellites for information |
| `/#mission` | Encounter instrument, supplied review priorities and selected-case evidence |
| `/#agent-architecture` | Root orchestrator, five inspectable branches, 19 specialist descriptions |
| `/#activity` | Expandable CSS 3D signal sculpture and filterable event ledger |
| `/#satellite-directory` | Eight fictional spacecraft, search, review filter, return to orbit and alert rehearsal |
| `/overview/`, `/activity/`, `/satellites/` | Static-export-compatible client navigation to the corresponding homepage chapter; ordinary link fallback |
| `/queue/`, `/case/` | Existing analyst workspace |

The welcome dialog is shown once per browser session, skipped for reduced motion, dismissible with its button or Escape, and automatically finishes after the model becomes ready (bounded by a timeout). No remote asset is required for the introduction. Site motion can be paused; this also pauses trace playback. Reduced motion retains navigation and information without camera interpolation or decorative loops.

## Real engine integration

- `3d-game/apps/client/src/earth/model.ts` reads the downloaded NASA GLB's indexed geometry, transforms, vertex normals, UVs and color/normal maps. The loaded mesh has 3,072 triangles.
- `3d-game/apps/server/src/bvh.ts` exports its acceleration tree to GPU textures. The browser uses this library code; it does not start the offline server renderer.
- `3d-game/apps/client/src/earth/shaders.ts` traces primary rays against the mesh through the packed BVH, shades with direct sunlight and normal mapping, and integrates an atmospheric shell. This is not the offline renderer's full global-illumination pipeline.
- `renderer.ts` uses the engine's existing GL helper and math types. `projectOrbit` uses ray/sphere occlusion to hide dots behind Earth.
- `EarthHero` smooths scroll progress through an exponential response, caches viewport dimensions and orbit samples, only recalculates orbit paths when the camera changes, and avoids tracing an unchanged frame. Rendering stops while the stage is outside the viewport or the document is hidden.
- Resolution adapts to observed frame time, with a pixel budget and an initial software-renderer adjustment. The interface runs on requestAnimationFrame independently from expensive ray tracing. Resolution can drop on slow devices; 60 FPS is not guaranteed on every device.
- GARUDA and the game remain independent and important. No game routes or models were removed.

### Measurement

Playwright's browser initially ran in the background, producing approximately 1 callback/second. That was an invalid foreground-performance baseline. After `page.bringToFront()`, the earlier drawing threshold produced around 30 ray-traced frames/second with 60 UI callbacks/second. The updated threshold and adaptive rendering produced a sampled 59 ray-traced frames/second and 60 UI callbacks/second at a 1440 × 1000 CSS viewport, quality scale 0.69, on Intel UHD Graphics via ANGLE/D3D11. These are local development measurements, not a cross-device benchmark. The canvas exposes `data-render-fps`, `data-frame-fps` and `data-render-scale` for inspection; they count submissions/callbacks, not GPU timestamp-query measurements.

## Orchestrator and data boundaries

The design adapts the router → specialists → judge → trace pattern described in [the owner's Finora repository](https://github.com/Adhirajsingh2507/Error-404-Not-Found). It does not import its personal-finance business logic into an orbital assessment.

`src/lib/mission-workflow.ts` contains the inspectable branch definitions, two explicit synthetic scenarios, deterministic computations and six trace events per run. `mission-experience.tsx` displays them and owns transient UI state.

| Branch | Specialist nodes | Current execution |
| --- | --- | --- |
| Evidence audit | Schema/units, covariance auditor, maneuver context | Supplied epoch age compared with a 12-hour demo policy; missing context disclosed |
| Collision | Encounter geometry, pair screening, uncertainty, response comparison | One constant-relative-velocity closest-approach fixture using the existing engine Vec3 |
| Terrain | Footprint gate, classifier, exposure estimator | Withheld: no footprint or geographic overlays provided |
| Finance | Asset valuation, service interruption, response budget, insurance, aggregation | Replacement cost + daily revenue × downtime; response-cost assumption shown separately |
| Judge | Numeric verifier, evidence guardrails, brief, human approval | Summarizes limitations and leaves the next step to the analyst |

The nested specialists describe the intended architecture; they are not individually deployed agents. Run/replay is a timed display of local branch results, not a live ADK/Groq invocation. The exported JSON is labeled `orbit-trust.demo-trace.v1` with input assumptions and the events reached so far. Its findings include all precomputed branch results, even before the playback reaches them. No account data is transmitted. State resets on refresh except for the session-only welcome preference.

Closest approach minimizes `|r + v t|` over `0 <= t <= 600 seconds`. The close fixture yields 120 m at 300 seconds; the wider fixture yields 2,400 m. A 500 m threshold triggers demonstration review, not a declaration of collision. No collision probability can be derived without covariance and other required inputs. A conjunction is not an immediate reentry prediction.

The financial fixture defaults to $18,000,000 replacement cost, $24,000/day service revenue and 14 downtime days: $18,336,000 conditional loss. It is not probability-weighted loss or money actually saved. Insurance recovery and ground losses are excluded. Adjusting the what-if slider changes its displayed value without rewriting the recorded trace.

The hero's decorative circular orbits are fictional, accelerated and visually expanded. They do not drive the encounter alert. The alert comes from the separate computed fixture and identifies itself as a demonstration. The mission priorities and historical activity are supplied snapshots from `demo-data.ts`; new local-run events are marked separately.

## Next integration seams

Replace scenario fixtures with validated, provenance-bearing contracts before connecting operational data. A future service should emit bounded branch progress events, source IDs, model version, frame/epoch/units, input completeness, computed findings and explicit withheld states. Feed that stream to the existing trace UI. Keep secrets and Groq calls on a backend; no client API keys. Terrain requires a separately supplied reentry footprint and exposure layers. Maneuver ranking requires operator-supplied candidates and a scientific orbital model. The rigid-body game engine is not an orbital propagator.

## Validation

- `npm run build` in `apps/web`: static export passes, including legacy entry routes.
- `npm run typecheck` in `3d-game/apps/client`: passes.
- `node --test --experimental-strip-types test/mission-workflow.test.ts` in `apps/web`: four tests pass. Covers future-horizon bounds, zero/diverging relative velocity, rotation invariance, non-finite input rejection, scenario classification and unsupported-claim withholding. Node emits an informational module-type warning; no package change was needed.
- Playwright at 1440 × 1000 and 390 × 844: no document-level horizontal overflow; verified welcome skip and automatic finish, reduced motion, orbit reveal, visible dots, filters/empty state, expanded finance, slider, run completion, pause/resume, close-approach alert, acknowledgement, wider scenario without false alert, JSON download and old-route navigation.
- Visual screenshots were inspected locally in the workspace `artifacts/orbit-v2-*.png`; they include welcome, hero, orbit view, mission, architecture, activity, finance, mobile pages and alert.

Higgsfield had zero image credits when checked; no new Higgsfield asset was generated. Figma's tools were not exposed in this session, so this milestone does not claim an updated Figma file. Playwright and the local animation, redesign and React review skills were used directly.
