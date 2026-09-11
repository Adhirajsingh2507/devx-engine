# 15 — Glossary + One-Page Cheat-Sheet

---

## Glossary (every term, from 0)

**Affine quantization** — mapping floats to small ints via `scale` + `zero_point`
(`q = round(x/scale)+zp`). Used for INT8.

**API** — a program's request menu; ours is HTTP/REST returning JSON.

**Baseline (`b`)** — distance between the two stereo cameras. Bigger baseline → better far
depth.

**Bearing capacity** — how much load ground can hold; our `CLASS_BEARING` weight per
material.

**Calibration** — measuring a camera's intrinsics (`f, cx, cy`, distortion) from known
patterns.

**Cell / tile** — one square of the world grid; our atomic unit of classify+score. A tile
= `{x,y,z,class,slope,safety_score,zone}`.

**CNN (Convolutional Neural Network)** — a net that slides learned filters over an image;
basis of segmentation nets.

**Confidence** — a [0,1] "how sure am I"; in TerraSight it forces the decision toward
caution when low.

**Contract (frozen)** — fixed request/response shapes agreed day 1, locked by a test.

**CORS** — browser rule for cross-origin requests; our API allows it.

**Determinism** — same input → same output; enables provable, testable decisions.

**Disparity (`d`)** — horizontal pixel shift of a point between left/right images; source
of stereo depth.

**Drift** — accumulating pose error in SLAM over time.

**Edge computing** — running AI on the device (rover), not the cloud.

**Frame (camera/world)** — a coordinate system. Camera frame moves with the rover; world
frame is fixed.

**FastAPI** — Python web framework for the API.

**Fusion** — merging many frames/observations into one consistent map.

**Gradient** — rate of change (of height); its `arctan` gives slope.

**IMU** — inertial sensor (accelerometer + gyro); fused with vision to fight drift.

**IoU (Intersection over Union)** — a segmentation accuracy metric (overlap/union). *Ours
is self-consistency, not accuracy.*

**Idempotent** — running twice = running once (our `persist`).

**Latency wall** — the 6–44 min Earth round-trip that forces onboard autonomy.

**LiDAR** — laser depth sensor (alternative to stereo).

**Loop closure** — recognizing a revisited place to correct SLAM drift.

**Middleware** — code wrapping requests (CORS, our `StripPrefix`).

**NaN** — "Not a Number" = invalid/unknown; we treat it as *bad* (score 0), never neutral.

**No-false-safe** — the invariant: never call hazardous ground safe/Zone 0.

**Pinhole model** — `u=f·X/Z+cx`; how a camera projects 3D→2D (and loses depth).

**Pipeline** — the ordered stages segmentation→…→scoring→API.

**Pixel** — one image sample; RGB = 3 numbers (0–255).

**Point cloud** — a set of 3D points from depth.

**Pose** — position + heading `(x,y,heading)`.

**Precedence** — zone priority: hazard > geological > navigation > safe.

**Quantization** — fewer bits per number (INT8) for smaller/faster models.

**Rad-hard CPU** — radiation-hardened, slow, low-power space processor.

**Regolith** — loose planetary surface material ("soil").

**RLS (Row-Level Security)** — Postgres per-row access rules; ours = public read /
backend write.

**Roughness** — local bumpiness = stddev of neighbourhood heights (metres).

**Safety Score** — `[0,1]` weighted construction-viability per cell.

**Segmentation (semantic)** — per-pixel class labels.

**Service-role key** — Supabase admin key that bypasses RLS; backend-only, never in
frontend.

**SGBM** — Semi-Global Block Matching; classical stereo matcher (OpenCV).

**SLAM** — Simultaneous Localization And Mapping.

**Slope** — ground tilt in degrees = `arctan(gradient)`.

**Standard deviation (σ)** — typical spread from the mean; our roughness.

**Stereo** — two cameras → depth via disparity.

**Supabase** — hosted Postgres + API; our persistence.

**Terrain class** — one of 9 material labels (compact_soil … unknown).

**Trust gate** — `guards.py` checks (stale/off-grid/missing depth) rejecting bad input.

**U-Net** — encoder-decoder CNN for segmentation.

**Vercel `services`** — one-project multi-app framework we deploy on.

**Voxel** — a 3D cube (Minecraft-style); our surface view.

**Zone (0–3)** — safe / navigation / geological / hazard.

---

## One-page cheat-sheet

### The flow
`cameras → segmentation(class,conf) + stereo depth(slope,rough) → SLAM fusion(world grid +
path) → terrain analysis(Cell + crater-dist + boundaries) → SCORING(safety_score, zone) →
FastAPI(frozen contract) → Next.js dashboard + Three.js 3D`

Measurement = stages 1–4. **Decision = scoring only.**

### The 4 zones
`0 safe-build · 1 drive-only · 2 protect-science · 3 hazard` — precedence
**hazard > geological > navigation > safe**. Default = Zone 1 ("prove safe").

### The 9 classes (`CLASS_BEARING`)
compact_soil 1.0 · soil 0.6 · loose_soil 0.3 · rock 0.2 · crater 0.0 · shadow 0.0 ·
waterbed 0.1 · mineral_edge 0.1 · unknown 0.4

### Scoring numbers (`scoring.py`)
- Score = `0.35·slope_f + 0.25·rough_f + 0.20·class_f + 0.20·crater_f`
- `class_f = 0.4 + (bearing − 0.4)·conf`  ← the no-false-safe line
- Thresholds: slope safe **<8°**, hazard **≥25°** · rough max **0.30 m** · crater keep-out
  **<3 m** · Zone-0 needs score **≥0.70** AND conf **≥0.5** AND rough **<0.30** AND class
  ∈ {compact_soil, soil}
- **NaN/inf → 0** always.

### Stereo/depth
`Z = f·b/d` · slope = `arctan(gradient)·180/π` · roughness = `stddev(3×3 heights)` ·
invalid → NaN.

### The API (frozen)
`/health {status,source}` · `/map/tiles [{x,y,z,class,slope,safety_score,zone}]` ·
`/rover/path [{t,x,y,heading,mode}]` · `/sites [{id,x,y,safety_score,rank}]` ·
`/boundaries [{type,polyline}]`

### File map (where things live)
| Thing | File |
|---|---|
| Segmentation | `backend/app/perception/segment.py` |
| Depth (slope/rough) | `backend/app/depth/pipeline.py` |
| Real stereo (SGBM) | `backend/app/depth/stereo.py` |
| SLAM pose | `backend/app/slam/pose.py` |
| Fusion + path | `backend/app/slam/fuse.py` |
| Terrain + crater-dist + boundaries | `backend/app/terrain/assemble.py` |
| **Scoring + zones (the decision)** | `backend/app/scoring.py` |
| Trust gates | `backend/app/guards.py` |
| API | `backend/app/main.py` |
| Data (mock/Supabase) | `backend/app/db.py` |
| Pipeline runner | `backend/app/pipeline.py` |
| Internal contracts | `backend/app/contracts.py` |
| Edge budget / quantize | `backend/app/edge/{budget,quantize}.py` |
| Eval metrics | `backend/app/eval/metrics.py` |
| Safety regression test | `backend/tests/test_safety_regression.py` |
| Frontend dashboard | `frontend/src/app/page.tsx` |
| 3D surface view | `frontend/src/app/explore/` + `components/game/` |
| Gate | `scripts/validate-terrasight.sh` |

### What's real vs simulated
Real: decision layer, safety guarantees, API, persistence, INT8 quant, frontend, deploy.
Simulated: segmentation (classical), depth-on-real-images (untested), SLAM (synthetic
frames), datasets (placeholders). **No trained NN yet.**

### Killer lines
- "Failure mode is over-caution, **by design**."
- "We can refuse good ground, but are **architecturally prevented from approving bad
  ground.**"
- "Measurement informs the decision; it never overrules it."
- "It builds ≠ it works."
- "No GPS on Mars — localization must be onboard."

### Live demo
**https://terrasight-liard.vercel.app** (dashboard + `/explore`).
