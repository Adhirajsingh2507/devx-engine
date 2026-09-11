# 10 — Frontend: dashboard + 3D surface view

**Stack:** Next.js 16 (App Router) + React 19 + Tailwind + Three.js (via
`@react-three/fiber` + `drei`). **Files:** `frontend/src/`. **Live:**
https://terrasight-liard.vercel.app

---

## 10.1 From zero: the pieces

- **React** — a UI library: you write **components** (functions returning HTML-like
  JSX); React re-renders them when data changes. `useState` holds data, `useEffect` runs
  side-effects (like fetching) after render.
- **Next.js** — a React framework adding routing (a file `app/explore/page.tsx`
  becomes the `/explore` route), builds, and server rendering. `"use client"` at the top
  marks a component that runs in the browser (needed for interactivity/3D).
- **Three.js** — a 3D graphics library (WebGL). **`@react-three/fiber`** lets you write
  Three.js *as React components* (`<mesh>`, `<Canvas>`); **`drei`** adds helpers (stars,
  controls).

## 10.2 The two screens

**Dashboard (`/`, `app/page.tsx`)** — mission control:
- `StatsPanel` — computed KPIs: average safety %, safe zones (count of zone 0), hazards
  (count of zone 3), site count. These are *derived* from the tiles, so they always match
  the data.
- `TerrainGrid` — an **SVG** grid: one `<rect>` per tile coloured by zone
  (`0=white, 1=grey, 2=dark, 3=near-black`), the safety score drawn as text, boundary
  polylines as dashed paths, the rover path as a dotted line with waypoint dots, and site
  labels `S1..S6`. Hovering a cell shows a detail readout (class, slope, height). The
  cell colour reflects the **zone**, not the score — so you can literally *see* the
  decision layer (e.g., a high-scoring soil cell painted hazard because of crater
  keep-out).
- `SiteTable` — ranked construction sites; `RoverTimeline` — the waypoints.

**Surface view (`/explore`, `app/explore/page.tsx` → `components/game/`)** — a driveable
**voxel** (Minecraft-style) 3D world **generated from the same tiles** (`worldgen.ts`
turns tiles into terrain blocks by class/height). A player controller, HUD (position,
fps, the cell you're standing on), site beacons, sky/fog. Loaded with `dynamic(..., {
ssr:false })` because Three.js needs the browser (no server-side rendering).

## 10.3 Data flow & the fallback (the important part)

Both screens fetch the frozen contract and **degrade gracefully**:
```
try:   GET /api/backend/{map/tiles, rover/path, sites, boundaries}   # live backend
catch: GET /mock/{tiles,path,sites,boundaries}.json                  # bundled fallback
```
- On Vercel, `/api/backend/*` is a same-origin rewrite to the FastAPI backend; the client
  base is `process.env.NEXT_PUBLIC_API_URL ?? "/api/backend"`.
- If the backend is unreachable, it falls back to `public/mock/*.json` shipped in the
  build — **the dashboard never shows a blank screen.**
- `/health` tells the UI whether it's talking to `"supabase"` (badge: **Live**) or
  `"mock"` (**Simulation**).

Because the frontend was built against the **frozen contract** (`types.ts` mirrors the
exact shapes), it worked against the real backend on day one with no rework — the whole
point of freezing the contract.

## 10.4 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| Build against the **frozen contract** + a bundled mock | Frontend developed fully in parallel, before the backend existed | A second copy of mock JSON to keep in sync with the backend's |
| **Live→mock fallback** | Demo never breaks; resilient to a down backend | Can *mask* a broken backend (looks fine on mock) — verify prod separately |
| **SVG** for the 2D grid | Crisp, scalable, trivial to draw rects/paths/text, no lib | Not great for *huge* grids (thousands of cells) |
| **Three.js voxel** surface view | A memorable, tangible "drive the rover" demo moment | Bundle weight (three + fiber + drei) and GPU use |
| `ssr:false` dynamic import for the 3D | Three.js needs the browser DOM/WebGL | The 3D page can't be server-rendered (fine — it's interactive) |
| Colour cells by **zone** (not score) | You *see* the decision layer's output directly | Monochrome palette (accessibility weakness — see below) |

## 10.5 Known gaps (be honest if asked)
- **Dead code:** `src/lib/api.ts` exists but both pages re-implement their own fetch — it
  should be deleted or used.
- **Mock duplication:** `frontend/public/mock/*.json` is a hand-copy of `backend/mock/*`
  → drift risk; ideally generated from one source.
- **Accessibility:** the grid is hover-only (no keyboard/touch), zones are encoded by
  brightness only (hard for colourblind users — the numbers help), no ARIA. Fine for a
  demo, weak for a real product.

## 10.6 Alternatives
- **Canvas / WebGL 2D** instead of SVG — needed only if the grid gets huge.
- **deck.gl / Mapbox** for a geospatial map view — heavier, more "GIS" feel.
- **Server Components / SSR data fetch** — could pre-render the dashboard; we chose
  client fetch for the live/simulation toggle and simplicity.
- **A real DEM/point-cloud render** instead of voxels — prettier/more accurate, much
  heavier; voxels are the deliberate "fun + light" choice.

## 10.7 Q&A
**Q: How does the frontend get data?** It calls the frozen contract at `/api/backend/*`
(same-origin on Vercel), falling back to bundled `public/mock/*.json` if the backend is
down — so it never shows an empty screen. `/health` drives a Live/Simulation badge.

**Q: Why did the frontend work immediately with the backend?** Because both were built
against the *same frozen contract*; `types.ts` matches the endpoint shapes exactly, so
there was nothing to reconcile.

**Q: Is the 3D just eye-candy?** It's generated from the *same* perception tiles
(`worldgen.ts`), so driving the rover shows the actual classified terrain — a tangible
way to convey "the rover sees and reasons about this world." (It also happens to be a
great demo hook.)

**Q: Biggest frontend weakness?** Accessibility (hover-only, brightness-only zone
encoding) and a duplicated mock file. Both are quick fixes, flagged honestly.
