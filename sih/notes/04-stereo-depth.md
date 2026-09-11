# 04 — Stereo Depth: "How far? How steep? How rough?"

**Files:** `backend/app/depth/pipeline.py` (slope/roughness from a height grid),
`backend/app/depth/stereo.py` (real stereo → depth), `backend/app/depth/calibration.py`
(camera parameters). **Outputs measurements only.**

---

## 4.1 The concept, from zero

Segmentation told us *what* each pixel is. But "what" isn't enough: **flat-looking
compact soil on a 25° slope is still a hazard.** We need the *geometry* — how far
away things are, and from that, how **steep** and how **rough** the ground is.

A single camera can't measure distance (recall 2.2: depth is lost in projection). So
the rover has **two** cameras side by side (**stereo**), like two eyes. By comparing
the two images we recover depth, exactly like your brain does.

## 4.2 The math, gently

Three sub-steps:

**(a) Disparity — find the shift.** For a point in the world, find *where it lands in
the left image* and *where the same point lands in the right image*. Because the
cameras are offset by the **baseline** `b`, the point shifts horizontally by `d`
pixels (the **disparity**). Finding, for every pixel, its matching pixel in the other
image is the hard part — **stereo matching**.

**(b) Disparity → depth.** Simple triangulation:
```
Z = (f · b) / d
```
Close objects shift a lot (big `d` → small `Z`); far objects barely shift. If we can't
find a confident match (occlusion, textureless sand), `d` is invalid → **depth = NaN**
(unknown), never a fabricated number. This NaN discipline is a safety feature.

**(c) Depth → height grid → slope & roughness.** Depth per pixel becomes a 3D point
cloud; binned top-down it becomes a **height** per grid cell. Then:

- **Slope** (degrees): how fast height changes between neighbours.
  ```
  dz/dx = (h[x+1] − h[x−1]) / (2 · cell_size)     # central difference
  dz/dy = (h[y+1] − h[y−1]) / (2 · cell_size)
  slope = arctan( sqrt(dz/dx² + dz/dy²) ) · 180/π
  ```
  A 45° ramp (`dz == dx`) gives exactly 45°. Edge cells use one-sided differences.
- **Roughness** (metres): the **standard deviation** of heights in the 3×3
  neighbourhood — bumpiness. Boulder field → high; flat pad → ~0.

## 4.3 How TerraSight does it

### The always-on path — `derive_geometry(heights, cell_size_m)` (`depth/pipeline.py`)
Pure stdlib (`math`, `statistics`). Takes a height grid, returns per cell a
`DepthCell{height, slope_deg, roughness}`:
- **Central differences** for the gradient (one-sided at the grid edge).
- `slope = degrees(atan(hypot(dzdx, dzdy)))`.
- `roughness = pstdev(finite heights in the 3×3 window)`.
- **NaN propagation:** any non-finite height → the cell's slope/roughness are `NaN`.
  We *never* invent a value for missing depth.

It's verified with known-answer self-checks: a flat plane → ~0° slope, ~0 roughness;
a constant 45° ramp → 45.0° within tolerance; a hole (NaN) stays NaN.

### The real-stereo path — `stereo.py` (needs OpenCV)
- `disparity(left, right, calib)` — runs **`cv2.StereoSGBM`** (Semi-Global Block
  Matching), the standard classical stereo matcher, tuned by calibration params.
- `disparity_to_depth(disp, calib)` — applies `Z = baseline·focal / disparity`, with
  **invalid/occluded disparity → NaN**.
- `stereo_geometry(left, right, calib, cell_size_m)` — builds the height grid then
  **reuses `derive_geometry`** for slope/roughness (one source of truth for geometry).
- `cv2` is **lazy-imported** — the module (and whole pipeline) loads on a machine
  without OpenCV; you only need OpenCV to actually run SGBM. Its self-check runs the
  pure-numpy NaN guard always, and the full synthetic-plane round-trip only when
  `cv2` is present.

### Calibration — `calibration.py`
A `Calibration` dataclass holds `baseline_m, focal_px, cx, cy` and the SGBM matcher
knobs (disparity range, block size, uniqueness ratio, speckle filter). **These are
data, not magic constants** — they differ per camera rig and per dataset (a lunar rig
≠ a Mars-analog rig), so they live in JSON (`backend/data/calibration/lunar.json`,
`mars.json`), ready to be loaded per dataset.

## 4.4 Why SGBM (Semi-Global Block Matching)?

Stereo matching is hard because a single pixel is ambiguous (many pixels look alike).
- **Block matching** compares small *patches* (more distinctive than 1 pixel).
- **Semi-global** enforces *smoothness*: neighbouring pixels should have similar
  disparity (the world is mostly continuous), aggregated along multiple 1D paths — a
  clever approximation of a full 2D optimization. It's the classic accuracy/speed
  sweet spot, and it's in OpenCV, so no training and no ML dependency.

## 4.5 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| Classical **SGBM**, not a learned stereo net | No training, in OpenCV, deterministic, edge-friendly | Some accuracy on textureless/low-light regions a learned net handles better |
| `cv2` **lazy-imported / gated** | Deployed API stays lean (no numpy/opencv on Vercel); pipeline loads without it | Real stereo only runs where OpenCV is installed (offline/rover), not in the serverless API |
| **Reuse `derive_geometry`** for slope/roughness | One tested source of truth for geometry math | Nothing — pure win |
| Invalid disparity → **NaN**, never a number | Missing depth must read as *bad*, not flat/safe | Coverage: some cells have no depth (correctly) rather than a guessed value |
| Calibration as **JSON data** | Per-dataset tuning without code changes; honest about "these are knobs" | A small config-loading step |
| Slope/roughness at **cell** granularity | The unit the safety layer needs; cheap | Sub-cell detail |

**Honest caveat to state:** the real SGBM path is *implemented and unit-checked on
synthetic pairs*, but has **not been run on real stereo imagery** (no OpenCV/images
wired in this environment). The always-on `derive_geometry` (height→slope/roughness)
is fully tested. So "we compute slope/roughness correctly" is proven; "we extract
depth from real Mars photos" is coded but unproven.

## 4.6 Alternatives

- **Learned stereo (RAFT-Stereo, PSMNet)** — higher accuracy, handles hard regions;
  needs GPU + training data; heavy for a rover.
- **Active depth (LiDAR / structured light / ToF)** — direct, accurate depth without
  matching; extra hardware, power, and mass (precious on a rover). Many real rovers
  *do* carry LiDAR; stereo is the cheap passive option.
- **Monocular depth (single-camera neural net)** — one camera, but gives *relative*
  not metric depth and hallucinates on novel scenes — dangerous for safety.
- **Photoclinometry / shape-from-shading** — infer slope from brightness; classic in
  planetary science, brittle under harsh space lighting.

## 4.7 The two numbers that matter downstream

Scoring only consumes `slope_deg` and `roughness` from this stage (plus `height` for
display). The thresholds that make them meaningful live in `scoring.py`:
- `SLOPE_SAFE_DEG = 8` (full credit below), `SLOPE_MAX_DEG = 25` (hazard at/above).
- `ROUGH_MAX = 0.30 m` (rough cutoff; also blocks Zone 0).
These are **tuning knobs calibrated per dataset**, not universal physics — an
important honesty point (real regolith mechanics vary by body).

---

## 4.8 Q&A

**Q: How do two cameras give depth?** Disparity — the horizontal pixel shift of the
same point between left and right images. `Z = f·b/d`: big shift = close, small = far.

**Q: What if stereo matching fails (shadow, smooth sand)?** Disparity is invalid →
depth is `NaN` → that cell contributes 0 to safety. Missing depth is treated as bad,
never as flat/safe.

**Q: Why not LiDAR?** Stereo is passive, cheap, low-power, low-mass — good for a
budget rover. LiDAR is more accurate but adds hardware/power/mass; our design keeps
that as a pluggable upgrade (it would just feed the same height grid).

**Q: Is your depth real?** The slope/roughness math on a height grid is fully tested.
The real image→depth SGBM path is implemented and synthetic-checked but not yet run on
real stereo photos — that's the honest next step.

**Q: Units and thresholds?** Slope in degrees (safe <8°, hazard ≥25°), roughness in
metres (rough ≥0.30 m). These are per-dataset calibration knobs, deliberately not
hard-coded as universal truths.
