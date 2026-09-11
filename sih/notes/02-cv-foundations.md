# 02 — Computer-Vision Foundations (from zero)

Before the perception stages make sense, you need ~12 concepts. This file builds
them from nothing. If you already know a section, skim it.

---

## 2.1 An image is just numbers

A digital image is a **grid of numbers**. Each little square is a **pixel**
("picture element"). A grayscale image is a 2D grid where each pixel is one number
(0 = black, 255 = white). A colour image has **3 numbers per pixel** — Red, Green,
Blue (RGB), each 0–255. So a colour image is really a 3D block of numbers:
`height × width × 3`.

```
one RGB pixel = (R, G, B) = (210, 200, 170)  → a light tan colour
```

This matters because **all of computer vision is math on these number grids.** When
we say "segment the image," we mean "for each pixel's numbers, output a label."

**Matrix / array:** a grid of numbers. In code we use `numpy` arrays. A 3×9 grid of
cells is a matrix with 3 rows and 9 columns.

## 2.2 A camera turns 3D into 2D (and loses depth)

A camera flattens the 3D world onto a 2D sensor. The standard model is the
**pinhole camera**: light from a 3D point passes through a tiny hole and lands on
the sensor. The key formula (you can quote this):

```
u = f · (X / Z) + cx        (horizontal pixel of a 3D point)
v = f · (Y / Z) + cy        (vertical pixel)
```

- `(X, Y, Z)` = the 3D point in the world (Z = distance from camera, "depth").
- `(u, v)` = where it lands in the image, in pixels.
- `f` = **focal length** (in pixels) — how "zoomed in" the camera is.
- `(cx, cy)` = **principal point** — the pixel at the centre of the sensor.

These numbers (`f, cx, cy`, lens distortion, etc.) are the camera's **intrinsics**,
found by **calibration** (photographing a known pattern like a checkerboard).

**The critical loss:** notice `Z` divides `X` and `Y`. A near small object and a far
big object can produce the *identical* pixel. **A single image cannot recover depth
`Z`.** That's why we need *stereo* (two cameras) — see 2.4.

## 2.3 Segmentation vs classification vs detection (naming)

Three related CV tasks, easy to confuse:

- **Classification:** one label for the *whole image* ("this is a cat").
- **Object detection:** boxes around objects ("cat here, dog there").
- **Semantic segmentation:** a label for *every pixel* ("these pixels are rock,
  those are soil"). ← **This is what stage 1 does.**

Segmentation gives you a "painted" version of the image where every pixel is
coloured by its class. It answers **"what is this?"** for the whole scene at once.

## 2.4 Stereo vision — how two eyes see depth

Hold a finger up and blink each eye alternately: the finger *jumps* left/right
against the background. Near things jump more than far things. Your brain uses that
jump to feel depth. That jump is **disparity**, and it's exactly how stereo depth
works.

Two cameras a known distance apart (the **baseline**, `b`) photograph the same
scene. A point in the world appears at a slightly different horizontal pixel in the
left vs right image. That horizontal shift is the **disparity** `d` (in pixels).
The depth formula (memorize the shape):

```
Z = (f · b) / d
```

- Big disparity `d` → object is **close** (small `Z`).
- Small disparity → object is **far**.
- Zero/invalid disparity → depth **unknown** (we mark it `NaN`, not "far").

So stereo depth is a two-step job: (1) for each pixel, find the *matching* pixel in
the other image (the hard part, called **stereo matching**), giving disparity;
(2) convert disparity → depth with the formula above. Stage 2 does this.

## 2.5 Depth map → heights → slope & roughness

Once you know the depth `Z` of every pixel, plus the camera geometry, you can
compute each point's real-world `(X, Y, Z)` — a **point cloud** (a cloud of 3D
dots). Bin those into a top-down **grid** and each cell gets a **height** (elevation).

From the height grid you derive the two numbers the safety layer actually cares about:

- **Slope** (degrees): how tilted the ground is. Computed from how fast height
  changes between neighbouring cells (the *gradient*). Steep = dangerous.
- **Roughness** (metres): how bumpy the ground is *locally*. Computed as the
  **standard deviation** of heights in a small neighbourhood (spread around the
  average). A boulder field is rough; a flat pad is smooth.

**Standard deviation, from 0:** take some numbers, find their average, then measure
the typical distance each number is from that average. Small = clustered (smooth);
large = spread out (rough). Formula: `σ = sqrt(mean((xᵢ − mean)²))`.

## 2.6 Gradient & slope (a little calculus, gently)

The **gradient** is just "rate of change." If height rises 0.5 m over 1 m of
horizontal distance, the ground rises at a ratio of 0.5. Convert a ratio to an
angle with `arctan`:

```
slope_degrees = arctan( rise / run ) · (180/π)
```

`arctan(0.5) ≈ 26.6°`. In 2D we combine the change in the x-direction and the
y-direction with the Pythagorean theorem: `gradient_magnitude = sqrt(dx² + dy²)`,
then `slope = arctan(that)`. Our depth stage does exactly this per cell.

## 2.7 Coordinate frames — "where" is ambiguous, so we pin it down

"The rock is at (3, 2)" — 3 and 2 *of what*? Pixels? Metres? From the camera or from
the map? CV is full of bugs from mixing these up, so systems define frames explicitly:

- **Image/pixel frame:** `(u, v)` in pixels, origin top-left.
- **Camera frame:** `(X, Y, Z)` in metres, relative to the camera right now.
- **World frame:** a *fixed* map origin that doesn't move as the rover drives.

The rover moves, so the camera frame keeps changing. To build **one** consistent map,
you must express everything in the **world frame** — which requires knowing where the
camera is in the world at each moment. Figuring that out is **localization** (part of
SLAM, stage 3). TerraSight's world frame is a grid of cells `(x, y)` with a metric
spacing `cell_size_m`; a cell also carries a `height` (its z).

## 2.8 Pose — position + orientation

A rover's **pose** = where it is *and* which way it faces: `(x, y, heading)` for a
ground rover (position + a compass angle). Tracking pose over time gives the **path**.
If you know each frame's pose, you can stitch frames into one map. Estimating pose
from images is the core of SLAM (stage 3). Real poses **drift** (small errors
accumulate) — a central challenge we'll address.

## 2.9 Confidence & probability — "how sure are you?"

A good perception system doesn't just say "rock" — it says "rock, **confidence
0.6**." **Confidence** is a number in [0,1]: 1 = certain, 0 = no idea. It's the
system admitting when it might be wrong.

This is the single most important CV concept for *our* project, because our safety
rule is: **low confidence must make the decision more cautious, never less.** A
label the system isn't sure about must not be allowed to approve construction. We
enforce this mathematically (see `07`).

## 2.10 NaN — the "I don't know" value (and why it's sacred here)

`NaN` = "Not a Number" — a special value meaning *invalid / missing / undefined*
(e.g., a pixel where stereo matching failed, so depth is unknown). The tempting bug
is to treat a missing value as 0 or as "far/flat/safe." **We never do that.** In
TerraSight, `NaN` anywhere in a cell's data forces its safety contribution to 0
(worst case), so **missing data can never look like good ground.** A missing
measurement is treated as a *bad* measurement, not a neutral one. Remember this —
it's a favourite interview trap ("what happens if a sensor drops out?").

## 2.11 The grid / "cell" / "tile" — our unit of decision

We chop the world into square cells (a top-down grid). Each **cell** (a.k.a. **tile**
in the API) is the atomic unit we classify and score. A tile carries exactly:
`{x, y, z(height), class, slope, safety_score, zone}`. The whole map is a list of
tiles. Deciding per-cell (instead of per-pixel) is a deliberate simplification:
cells are the natural granularity for "can I put a lander leg *here*?"

## 2.12 Determinism vs learning — two ways to make a decision

- A **learned/ML system** (neural net) finds patterns from data. Powerful, but a
  **black box**: same input → same output, but you can't easily *explain why*, and
  it can be confidently wrong on inputs unlike its training data.
- A **deterministic/rule system** follows explicit if/else math a human wrote. Less
  clever, but **fully transparent, testable, and predictable**: you can prove
  properties about it ("it can never output X when Y").

TerraSight uses **learning-style thinking for perception** (guessing what things
are) and **strict determinism for the decision** (what's allowed). Knowing *which
tool for which job* is the mark of good system design — and it's exactly the kind of
thing interviewers probe.

---

### The 12 concepts in one breath
image = numbers · camera flattens 3D→2D and loses depth · stereo recovers depth via
disparity `Z=fb/d` · depth→heights→slope(arctan of gradient)+roughness(stddev) ·
frames (pixel/camera/**world**) must be pinned · pose = position+heading, it drifts ·
**confidence** [0,1] must degrade toward caution · **NaN = unknown = treated as bad,
never neutral** · the **cell/tile** is our decision unit · **determinism for the
safety decision, learning for perception.**

Now you're ready for the stages. Start with `03-segmentation.md`.
