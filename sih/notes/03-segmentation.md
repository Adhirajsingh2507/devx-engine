# 03 — Segmentation: "What is this pixel?"

**File:** `backend/app/perception/segment.py` · **Owner concept:** turn RGB pixels
into terrain-class labels + confidence. **Outputs measurements only** (never a zone).

---

## 3.1 The concept, from zero

The rover sees colour pixels. Before we can reason about safety, we need to know
*what each pixel is made of*: is it firm compact soil (good to build on)? loose sand
(drivable, not buildable)? a crater (hazard)? a shadow (we can't see — don't guess)?

**Semantic segmentation** = assign every pixel a class label from a fixed list. The
output is a "class map": the same-shaped grid, but instead of colours it holds labels.

Our fixed list — the **9-class taxonomy** (must match everywhere in the system):

| Class | Meaning | Build-worthiness |
|-------|---------|------------------|
| `compact_soil` | Firm, compacted regolith | Best (bearing 1.0) |
| `soil` | Ordinary soil | Good (0.6) |
| `loose_soil` | Loose/sandy | Drivable only (0.3) |
| `rock` | Rocky | Poor (0.2) |
| `crater` | Crater floor/rim | Hazard (0.0) |
| `shadow` | Unlit — no info | Unknown-ish (0.0) |
| `waterbed` | Ancient water/ice bed | Protect (0.1, geological) |
| `mineral_edge` | Mineral boundary | Protect (0.1, geological) |
| `unknown` | Doesn't match anything | Neutral (0.4) |

Each pixel also gets a **confidence** ∈ [0,1] — how sure the classifier is.

## 3.2 How real systems do this (the theory you should know)

The state-of-the-art is a **neural network**, specifically a **U-Net** or a
**Fully Convolutional Network (FCN)**:

- A **Convolutional Neural Network (CNN)** slides small learned filters over the
  image, detecting edges → textures → shapes → materials, layer by layer.
- **U-Net** is a CNN shaped like a "U": an **encoder** downsamples the image
  (capturing *what* is present, losing *where*), then a **decoder** upsamples back
  to full resolution (recovering *where*), with **skip connections** copying fine
  detail across. Output: a per-pixel class map. It's the workhorse of biomedical and
  terrain segmentation because it needs relatively little data and gives crisp
  pixel-accurate masks.
- You **train** it on labelled images (humans paint the correct class per pixel),
  minimizing a **loss** (e.g., cross-entropy) that punishes wrong pixels, using
  **gradient descent**.

**Why we don't ship a U-Net (yet):** training needs a large labelled dataset of
real planetary imagery we don't have, and `torch` is a heavy dependency we
deliberately keep off the rover/deployment until a trained model earns its place.
So we built an honest classical stand-in behind the *same interface*.

## 3.3 How TerraSight actually does it (classical classifier)

Our classifier is a **nearest-colour-centroid classifier in a feature space**. Plain
English: we have a reference "fingerprint" for each class; for a pixel, we compute
its fingerprint and pick the closest class.

Step by step (`segment.py`):

1. **Feature extraction** (`_features`): a raw RGB pixel is turned into a 6-number
   **feature vector**: `(hue, saturation, value, luminance, R−G, G−B)`.
   - HSV (hue/saturation/value) separates *colour* from *brightness* — more robust to
     lighting than raw RGB.
   - Luminance = perceived brightness `0.299R + 0.587G + 0.114B`.
   - `R−G, G−B` are cheap **opponent-colour** channels (a Lab-space idea) that
     separate reddish crater soil from greenish mineral edges well.
2. **Class centroids** (`CENTROID_FEATURES`): each of the 8 real classes has a
   reference colour (`CLASS_COLORS`) run through the same `_features`. That's its
   fingerprint in the 6D space.
3. **Nearest centroid** (`classify`): compute the pixel's feature vector, measure
   **Euclidean distance** to each class fingerprint, pick the nearest.
4. **Special rules**:
   - `max(R,G,B) ≤ 30` → `shadow` immediately (pure-black = unlit, no colour info).
   - Nearest distance `> UNKNOWN_DIST (0.35)` → `unknown` (matches nothing well).
5. **Confidence from margin** — the clever, safety-relevant part. Confidence is based
   on how much *closer* the winning class is than the runner-up:
   ```
   margin = (d2 − d1) / d2          # d1 = nearest dist, d2 = 2nd-nearest
   conf   = min(CONF_CAP, CONF_FLOOR + CONF_CAP · margin)
   ```
   - `CONF_CAP = 0.6` — a **heuristic never claims more than 60% certainty** (it's not
     a trained net; honesty by design).
   - `CONF_FLOOR = 0.2` — even a made match isn't zero.
   - Big margin (one class clearly closest) → high conf. Two classes nearly tied
     (ambiguous pixel) → low conf. **Ambiguity honestly lowers confidence.**
6. **Texture gate** (`segment`): using numpy, we compute local brightness variance
   (3×3 "texture"). A cell that was *already* an uncertain colour match *and* sits in
   a noisy/mixed patch is demoted to `unknown`. Crucially, **texture can only *lower*
   confidence or demote — never boost** — so it can't manufacture false certainty.

## 3.4 The math intuition (why margin-based confidence is the right idea)

Imagine each class fingerprint as a landmark on a 2D map, and the pixel as a dot.
- If the dot sits right on top of one landmark and far from all others → obviously
  that class, high confidence.
- If the dot is halfway between two landmarks → it *could* be either → we should be
  *unsure*, so confidence should be low.

`margin = (d2 − d1)/d2` captures exactly this: it's ~0 when the two nearest landmarks
are equidistant (tied → unsure) and →1 when the nearest dominates (clear → sure).
This is the same intuition behind an SVM's margin or a softmax's peakedness — we just
compute it cheaply and deterministically.

## 3.5 Decisions & tradeoffs (say these in an interview)

| Decision | Why | What we gave up |
|---|---|---|
| Classical classifier, not a U-Net | No labelled dataset; keep `torch` off the deploy; ship an honest, testable stand-in behind a frozen interface | Real-world accuracy / generalization to unseen terrain |
| Confidence **capped at 0.6** | A heuristic must not pretend to be a trained oracle; feeds the no-false-safe guarantee | Some Zone-0 approvals a confident model would allow (we're conservative) |
| Feature space (HSV+opponent), not raw RGB | More robust to lighting; separates similar-looking classes | A little extra compute per pixel (negligible) |
| Texture can only *demote* | Prevents a noisy patch from ever *raising* confidence — one-directional safety | Might over-flag some textured-but-fine ground as `unknown` (safe error) |
| Output is measurement-only | Segmentation never decides a zone; scoring does | Nothing — this is pure upside for auditability |

**The meta-decision:** we optimized for **honesty + a clean seam** over raw accuracy.
The classifier can be swapped for a trained model *without touching anything
downstream*, because both produce the exact same `SegCell{terrain_class, conf}`.

## 3.6 Alternatives we considered / would use at scale

- **U-Net / DeepLabv3+** (trained CNN): the real answer once labelled data exists.
  Higher accuracy, generalizes; needs data + GPU training + `torch` on device.
- **MobileNetV3-small backbone + INT8 quantization**: the *rover-appropriate* trained
  option — small, fast on CPU, quantizable (see `09`). This is our documented target.
- **Classical ML (Random Forest / SVM on colour+texture features)**: middle ground —
  learns from a little data, no deep-learning stack. A reasonable next step.
- **Vision transformers (SegFormer)**: excellent accuracy, too heavy for edge today.

## 3.7 Confidence's job downstream (the safety link)

The `conf` we output isn't cosmetic. In scoring (`07`), class contribution is:
```
class_f = 0.4 + (class_bearing − 0.4) · conf
```
At `conf=1` you get the class's full bearing; at `conf=0` it collapses to the neutral
0.4. **Low confidence literally pulls the score toward "meh," so an unsure label can
never push a cell to Zone 0.** Segmentation's honesty about uncertainty is what makes
the safety guarantee possible.

---

## 3.8 Q&A (hackathon + interview)

**Q: Is this deep learning?** No — it's a classical colour-centroid classifier. We
built it behind a frozen interface so a trained U-Net/MobileNet drops in without
changing anything downstream. The *system* is model-ready; the model is the next step.

**Q: How is your confidence computed — is it a real probability?** It's a
margin-based heuristic (gap between the best and second-best class match), capped at
0.6 to stay honest. It's not a calibrated probability, but it correctly orders
certain vs uncertain pixels, which is all the safety layer needs (low conf → caution).

**Q: What if a pixel is pure shadow?** Special-cased to `shadow` (no colour info) — we
never *guess* a material for unlit pixels, and scoring treats shadow as non-buildable.

**Q: Why 9 classes?** They map directly to *decisions*: buildable materials
(compact/soil), drivable-only (loose/rock), science-protect (waterbed/mineral_edge),
hard hazard (crater), and honest ignorance (shadow/unknown). The taxonomy is the same
string set used by the scoring layer, enforced by a self-check.

**Q: Biggest weakness?** No trained model → won't generalize to real, varied planetary
imagery. Mitigation: the geometry path (slope/depth) still works even when the class is
uncertain, and low confidence degrades the decision toward caution — so a bad class
guess degrades gracefully instead of causing a false-safe.
