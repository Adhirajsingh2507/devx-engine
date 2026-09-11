# 05 — SLAM & Fusion: "Where am I, and one map from many frames"

**Files:** `backend/app/slam/pose.py` (pose estimation), `backend/app/slam/fuse.py`
(fusion + rover path). **Outputs measurements only.**

---

## 5.1 The concept, from zero

Each camera frame is a snapshot from *wherever the rover was at that instant*. Two
problems:

1. **Localization — "where am I?"** As the rover drives, the camera frame keeps
   moving. To put observations onto one fixed map, we must know the rover's **pose**
   (position + heading) for every frame.
2. **Mapping — "build one consistent world."** We must **fuse** many overlapping
   frames into a single, non-contradictory map — without duplicating cells or letting
   one bad frame overwrite good data.

Doing both *at the same time* — estimating pose *and* building the map, each
depending on the other — is **SLAM: Simultaneous Localization And Mapping.** It's a
foundational robotics problem (self-driving cars, drones, AR headsets all use it).

## 5.2 The chicken-and-egg + drift (the hard part)

- To know where you are, you compare what you see now to the map. To build the map,
  you need to know where you are. Each needs the other → you bootstrap and refine.
- **Drift:** every frame-to-frame motion estimate has a tiny error. Errors
  **accumulate** — after 1000 frames the rover *thinks* it's somewhere it isn't, and
  the map warps. This is the central SLAM challenge. Real systems fight it with:
  - **Loop closure** — recognizing a previously-seen place and snapping the map back.
  - **Sensor fusion** — blending vision with an IMU (accelerometer/gyro) and wheel
    odometry, which drift differently, so together they're steadier.

## 5.3 How real systems do this

- **Visual SLAM (ORB-SLAM3)** — tracks distinctive image features (corners) across
  frames, estimates full 6-DoF pose, does loop closure and bundle adjustment. The
  gold standard; complex and compute-heavy.
- **Visual-inertial odometry (VIO)** — fuses camera + IMU; robust, used on drones.
- **Featureless terrain problem:** uniform regolith has *no corners to track* →
  visual SLAM struggles → this is exactly where you lean on IMU/wheel odometry and
  flag the region as low-trust.

## 5.4 How TerraSight does it

We use a deliberately simple, testable approach appropriate for a near-planar rover
traverse — **translation-only scan matching on the height grid.**

### Pose estimation — `pose.py`
- **Registration** (`register`): given the previous frame's height grid and the
  current one, search over integer cell shifts `(dx, dy)` for the shift that best
  **aligns the heights** (minimizes **SSD** — sum of squared differences — over the
  finite-valued overlap). The winning shift = how far the rover moved. Pure numpy, no
  `cv2` needed.
- **Confidence = sharpness × coverage:**
  - **sharpness** = how much *better* the best shift is than the average shift. On a
    **flat, featureless** patch, *every* shift scores about the same → sharpness ≈ 0 →
    low confidence, automatically. (No separate "is this flat?" check needed — the
    math discovers it.)
  - **coverage** = fraction of the frame that had valid (non-NaN) overlap.
  - Confidence is clamped to `[0.05, 0.95]` — never 0 (some trust), never 1 (never
    certain).
- **Odometry/IMU blend:** an optional external `pose_hint` (wheel odometry / IMU) is
  blended with the vision estimate via a tunable weight (`ODOM_WEIGHT_DEFAULT=0.35`).
  A hint *backstops* a poor visual match but never *fully overrides* vision — real
  sensors drift, so we fuse rather than trust blindly.
- **`track_poses`**: runs registration across a frame sequence, dead-reckoning the
  pose; the first frame anchors the world origin at `(0,0)` with full trust.

### Degradation ladder (the safety-relevant bit)
Pose confidence drives the rover's `mode` through a **reversible** ladder:
```
full  →  cautious  →  survey-only  →  safe-hold      (as confidence drops)
      ←            ←              ←                    (and back up as it recovers)
```
So when the rover *can't trust where it is*, it slows down, then stops driving but
keeps mapping, then halts and flags for Earth — instead of confidently driving into a
hazard. **Autonomy is only safe if it knows when to stop.**

### Fusion — `fuse.py`
- `fuse_single(seg, depth)` — the P1 single-frame case: combine the segmentation grid
  and depth grid into one flat list of `FusedCell{x, y, height, slope, roughness,
  terrain_class, conf}`, keyed by cell.
- `fuse_sequence(frames)` — register a sequence into one shared world grid and
  **upsert** overlapping cells:
  - **Confidence-weighted running average** for geometry (height/slope/roughness) — a
    cell seen twice is *refined*, not overwritten.
  - **Highest-trust observation wins** the class label.
  - A **NaN sample is skipped** for geometry (never overwrites good data with unknown).
  - Fuse weight is **capped** so a long traverse can't make a stale reading immovable.
- `rover_path_from_poses` — turns the pose track into the contract's `rover_path`
  rows `{t, x, y, heading, mode}` (with the degradation `mode`).
- **`FusedCell.conf` carries the low-trust signal** — it's `seg_conf × pose_conf`, so a
  drifted/uncertain region naturally reads low-confidence downstream *without a new
  field*. Elegant: the existing confidence channel doubles as the trust map.

## 5.5 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| **Translation-only** scan matching (no rotation) | Sufficient for a near-planar traverse; simple, testable, no `cv2` | Can't handle sharp turns/rotation or full 6-DoF motion |
| Height-**SSD** registration, not feature tracking | Works on *featureless* regolith where corner-based visual SLAM fails | Less precise than feature+bundle-adjustment when features *do* exist |
| Confidence = **sharpness×coverage** | Featureless patches self-report low confidence with no special case | Not a rigorous covariance estimate |
| **Blend** odom/IMU, never fully trust | Real sensors drift differently; fusion is steadier than any one | Requires an odom/IMU source to gain the benefit |
| Confidence-weighted **upsert** (refine, don't overwrite); NaN skipped; weight capped | No duplicates, no good-data-clobbered-by-unknown, no immovable stale cells | More bookkeeping than "last write wins" |
| **Degradation ladder** drives `mode` | Safe autonomy stops when it can't trust itself; reversible | Slower/halting behaviour in ambiguous terrain (the *correct* trade) |

**Honest caveat:** no **loop closure** or **bundle adjustment**, so on a long loopy
traverse drift would accumulate — mitigated by the low-trust flag + degradation ladder
(the rover *knows* it's unsure and acts cautiously) rather than eliminated. All of this
runs on **synthetic frame sequences** (`scene_seq_0`), not real imagery yet.

## 5.6 Alternatives

- **ORB-SLAM3 / VINS-Fusion** — full visual(-inertial) SLAM with loop closure; the
  real long-mission answer; heavy and needs trackable features.
- **Wheel odometry only** — simplest; drifts badly on slip (sand), no map correction.
- **GPS** — not available off-Earth (no satellite constellation) — a fun fact judges
  like: *"you can't use GPS on Mars, so localization must be onboard and visual."*
- **Fiducial markers / prior orbital maps** — anchor pose to known landmarks; used in
  real missions, but requires pre-placed markers or good orbital DEMs.

---

## 5.7 Q&A

**Q: What is SLAM in one line?** Building a map of an unknown place *while*
simultaneously figuring out where you are in it — each depends on the other.

**Q: Featureless terrain breaks visual SLAM — how do you handle it?** Our height-SSD
matcher naturally scores *low confidence* on flat, featureless patches (every shift
looks equally good), so we degrade the rover to cautious/survey mode and lean on
odometry — instead of confidently driving on a bad pose estimate.

**Q: What about drift?** We don't do loop closure yet, so drift would accumulate over a
long traverse. We mitigate by *detecting* low trust and degrading behaviour, and by
fusing odometry. Loop closure (ORB-SLAM-style) is the documented upgrade.

**Q: Can you use GPS?** No — there's no GPS off Earth. That's precisely why onboard
visual localization is mandatory, not optional.

**Q: How do you avoid one bad frame ruining the map?** Fusion is a confidence-weighted
*upsert*: cells are refined, NaN never overwrites good data, the highest-trust label
wins, and fuse weight is capped so stale readings can be corrected.
