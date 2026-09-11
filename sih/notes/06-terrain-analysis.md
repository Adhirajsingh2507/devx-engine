# 06 — Terrain Analysis: describe each cell, trace the boundaries

**File:** `backend/app/terrain/assemble.py`. **The bridge between perception and the
decision.** Still measurement-only — it builds descriptors and boundary lines; it
does **not** decide zones.

---

## 6.1 The concept

After fusion we have a world grid of `FusedCell`s (class, slope, roughness, height,
confidence per cell). The scoring layer needs a clean per-cell **descriptor** plus one
value perception *doesn't* directly give: **distance to the nearest crater**. And the
frontend needs **boundary polylines** (the outline of crater rims and mineral edges)
to draw. Terrain analysis produces both.

Two jobs:
1. **`build_cells`** — turn each `FusedCell` into a `scoring.Cell` (the exact input the
   decision layer expects), computing `crater_dist_m` along the way.
2. **`extract_boundaries`** — trace the outline of each feature-class region into an
   ordered list of points (a **polyline**).

## 6.2 Crater-distance — a "keep-out" radius, from zero

Why compute distance-to-crater at all? Because **the ground *near* a crater rim is
dangerous even if the cell itself looks flat** — the edge can collapse, and you don't
put a habitat right beside a pit. So the safety layer enforces a **keep-out margin**
(`CRATER_MARGIN_M = 3 m`): any cell closer than 3 m to a crater is a hazard,
regardless of how nice its own geometry is.

To enforce that, each cell needs to know how far it is from the nearest crater:
- Collect all cells classified `crater`.
- For each cell, `crater_dist_m = (Euclidean distance in cells to the nearest crater
  cell) × cell_size_m`. A crater cell itself has distance 0.
- **If there are no crater cells:** distance = a **large finite** number
  (`NO_CRATER_DIST = 1e6`), **not `inf`**. Subtle but important: scoring treats `inf`
  as invalid (→ score 0), so using `inf` would wrongly penalize everything. Using a
  big *finite* number means "very far → full credit." (A classic edge-case detail
  interviewers love.)

## 6.3 Boundary tracing — from a blob to a line

Perception gives us *regions* (sets of cells all labelled `crater` or `mineral_edge`).
The dashboard wants the *outline* of each region as an ordered polyline. `extract_boundaries`:
1. **Find the rim cells** — a cell is on the border if at least one of its 4 neighbours
   is *outside* the region. (Interior cells are dropped; a fully-enclosed region falls
   back to all its cells.)
2. **Walk the border** — start at the topmost-then-leftmost rim cell and greedily hop to
   the nearest unvisited rim cell, tracing the perimeter. Disjoint blobs of the same
   class get stitched by distance. Output: `{type, polyline:[[x,y],...]}`.

**Complexity note (a `ponytail:` comment in the code):** the greedy walk is `O(n²)` per
class — fine for a per-scene grid; swap for a KD-tree or a proper Moore-neighbour
contour trace if grids grow to thousands of cells. Naming your own ceiling like this is
exactly what senior reviewers want to see.

## 6.4 The measurement↔decision boundary, enforced in code

This module is on the **measurement** side, so it must **never** call `zone()` or
`safety_score()` — it only *builds* `Cell`s and hands them off; the runner
(`pipeline.py`) does the scoring. This isn't just a convention: `assemble.py`'s
self-check **monkey-patches** `scoring.zone`/`safety_score` with call-counters and
asserts they're called **zero** times. A runnable proof of the architectural boundary,
not just a comment. (Great thing to show a judge who asks "how do you *know* the split
holds?")

## 6.5 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| Compute `crater_dist_m` here (not in scoring) | Keeps scoring pure-rules; distance is a *measurement* | An extra pass over the grid |
| No-crater distance = **large finite**, not `inf` | `inf` would read as invalid and zero-out good cells | A tiny magic constant (documented) |
| Greedy `O(n²)` border walk | Simple, correct for scene-sized grids | Efficiency at very large scale (ceiling documented) |
| **Assert** no scoring calls in the self-check | Turns the measurement↔decision rule into a *tested invariant* | Nothing — pure upside |
| Boundaries as polylines | Cheap to transmit + draw vs. sending a raster mask | Some shape fidelity for blobby regions |

## 6.6 Alternatives
- **Distance transform (scipy `distance_transform_edt`)** — compute crater-distance for
  the whole grid in one vectorized pass; faster at scale, adds a scipy dependency.
- **Marching Squares / OpenCV `findContours`** — proper contour extraction for
  boundaries; more robust on complex shapes, heavier dependency.
- **Compute crater-distance inside scoring** — rejected: it would put a *measurement*
  (geometry) into the *decision* layer, breaking the clean split.

## 6.7 Q&A
**Q: Why keep-out around craters?** Rim collapse and edge instability — the ground
*next to* a pit is unsafe even if flat. We enforce a 3 m margin via `crater_dist_m`.

**Q: Why is "no craters" distance a big finite number, not infinity?** Because scoring
treats non-finite values as invalid (→ score 0). A big finite number correctly means
"very far → safe," while `inf` would zero-out the whole map. Edge-case discipline.

**Q: How do you prove terrain analysis never makes a decision?** Its self-check
replaces `zone`/`safety_score` with counters and asserts they're never called — the
measurement↔decision boundary is a *tested* invariant.
