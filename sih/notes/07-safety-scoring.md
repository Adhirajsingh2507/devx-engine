# 07 — Safety Scoring & Zones: the heart of TerraSight ⭐

**Files:** `backend/app/scoring.py` (the decision), `backend/app/guards.py` (trust
gates). **This is the ONLY place in the entire system where a decision is made.**
Everything else is measurement. If you understand this file, you understand the
project's soul.

---

## 7.1 What this layer does, and why it's different

Every stage before this *guessed* facts about the world (and could be wrong). This
stage takes those facts and makes a **safety-critical decision**: is this ground safe
to build on? Because a wrong "yes" could sink a habitat and kill a mission, this layer
is built on the opposite philosophy from perception:

| Perception | Scoring |
|---|---|
| Learned / heuristic, can be wrong | **Deterministic** — plain if/else math |
| Black box | **Transparent** — a human reads and audits it |
| "What is this?" | "What is *allowed*?" |
| Fast guesser | Strict, boring safety inspector |

**No machine learning here. No randomness. Same input → same output, forever.** That
predictability is the *feature*: you can **prove** properties about it and **test** it
exhaustively.

## 7.2 The input: a `Cell`

```python
Cell(slope_deg, roughness, terrain_class, crater_dist_m, conf=1.0)
```
Five facts about one patch of ground: how steep, how rough, what material, how far from
a crater, and how *confident* perception was in the class. Scoring turns this into two
outputs: `safety_score ∈ [0,1]` and `zone ∈ {0,1,2,3}`.

## 7.3 The Safety Score — a weighted vote

`safety_score(cell)` is a **weighted sum of four factors**, each mapped to [0,1]:

```
score = W_SLOPE·slope_f + W_ROUGH·rough_f + W_CLASS·class_f + W_CRATER·crater_f
        (0.35)           (0.25)           (0.20)          (0.20)      → sums to 1.0
```

Each factor answers "how good is this dimension?" on a 0–1 scale:

- **slope_f** — `_lin(slope, 8, 25)`: full credit (1.0) at/below 8°, zero at/above 25°,
  linear between. Flatter = better.
- **rough_f** — `_lin(roughness, 0.05, 0.30)`: smooth = better.
- **crater_f** — 1.0 if `crater_dist ≥ 3 m`, else `crater_dist/3` (linear ramp into the
  keep-out zone). Closer to a crater = worse.
- **class_f** — the material's **bearing capacity** from `CLASS_BEARING`
  (compact_soil=1.0, soil=0.6, loose_soil=0.3, rock=0.2, crater=0.0, shadow=0.0,
  waterbed/mineral_edge=0.1, unknown=0.4), **then adjusted by confidence** (next
  section).

**The `_lin` helper** is a clamped linear ramp — and it holds a safety rule:
```python
def _lin(x, lo, hi):
    if not math.isfinite(x): return 0.0     # NaN/inf → 0, NEVER full credit
    ...linear from 1.0 at lo to 0.0 at hi, clamped...
```
That first line is a guardrail: **a missing/invalid measurement scores 0**, so it can
never masquerade as good ground.

Weights `0.35/0.25/0.20/0.20` say: **geometry (slope+roughness = 60%) dominates** the
score, because geometry is measured more reliably than material class; class and
crater-margin are 20% each.

## 7.4 Confidence degradation — the mathematical heart of "no false-safe"

Here is the single most important line in the codebase:

```python
class_f = 0.4 + (class_bearing − 0.4) · conf
```

Read it slowly:
- At `conf = 1.0` (certain): `class_f = class_bearing` — full effect of the material.
- At `conf = 0.0` (no idea): `class_f = 0.4` — collapses to a **neutral** value.
- In between: it *slides* from the material's true bearing toward neutral as confidence
  drops.

**Why 0.4 and not 0?** 0.4 is deliberately *mediocre* — not good enough to earn Zone 0,
not bad enough to falsely condemn. An uncertain cell becomes "meh," which is exactly
right: **uncertainty pulls the decision toward caution, never toward approval.** A
low-confidence "compact_soil" (bearing 1.0) can't ride its high bearing into a
buildable score, because confidence drags it back to 0.4.

This is the mechanism that makes the safety guarantee *structural* rather than
*hoped-for*. It's not "we tested that low confidence usually behaves" — it's "the math
makes it impossible for low confidence to help."

## 7.5 The Zone — precedence and hard gates

The score is continuous; the **zone** is the actual decision. `zone(cell)` checks in a
strict **precedence order** — hazard wins over everything:

```python
def zone(cell):
    # ZONE 3 — HAZARD (highest precedence, checked first)
    if (slope >= 25                                 # too steep
        or crater_dist < 3                          # inside crater keep-out
        or terrain_class == "crater"                # a crater is ALWAYS hazard
        or (terrain_class == "rock" and roughness >= 0.30)):  # a boulder
        return 3

    # ZONE 2 — GEOLOGICAL (protect it)
    if terrain_class in ("waterbed", "mineral_edge"):
        return 2

    # ZONE 0 — CONSTRUCTION-SAFE (four independent gates, ALL required)
    if (safety_score(cell) >= 0.70                  # high enough score
        and conf >= 0.5                             # confident enough
        and roughness < 0.30                        # not rough
        and terrain_class in ("compact_soil", "soil")):  # a buildable material
        return 0

    # ZONE 1 — NAVIGATION (the default: drivable but not buildable)
    return 1
```

Three things to internalize:

**(a) Precedence `hazard > geological > safe > nav`.** Hazard is checked *first*, so a
steep waterbed is Zone 3 (hazard beats geological), and a crater that happens to look
flat and smooth is *still* Zone 3 (class `crater` forces it). Good geometry can never
rescue a hazard.

**(b) Zone 0 requires FOUR independent gates — not just a high score.** Score ≥ 0.70
**and** confidence ≥ 0.5 **and** roughness < 0.30 **and** a buildable material. A cell
must pass *all four* to be approved. This is defense-in-depth: no single lucky number
gets you a habitat.

**(c) The default is Zone 1, not Zone 0.** If you don't clearly earn "safe," you get
"navigation-only." **You have to prove safe; unproven ≠ safe.** This is the opposite of
"innocent until proven guilty" — for construction we want "unsafe until proven safe."

## 7.6 "No false-safe" — the invariant, stated precisely

> **No configuration of terrain/geometry/sensor input may reach Zone 0 (or a high
> safety score used to approve building) when it must not.**

Being wrong by *refusing* good ground (false-negative, over-cautious) is acceptable —
you just survey elsewhere. Being wrong by *approving* bad ground (false-positive,
false-safe) is **catastrophic** and is what the whole design forbids. Every mechanism
above serves this one asymmetry:

- NaN/inf → 0 (missing data can't look good).
- Confidence collapses class toward neutral 0.4 (unsure can't approve).
- Hazard precedence checked first (good geometry can't rescue a hazard).
- Four independent Zone-0 gates (no single number approves).
- Default Zone 1 (unproven ≠ safe).

## 7.7 Worked examples (trace these yourself)

Using the real thresholds:

1. **Flat compact pad**, `Cell(3°, 0.02, compact_soil, 10 m, conf 0.9)`:
   slope_f≈1, rough_f≈1, class_f = 0.4+(1.0−0.4)·0.9 = 0.94, crater_f=1 →
   score ≈ 0.35+0.25+0.20·0.94+0.20 = **0.988**. Zone: not hazard, not geo, score≥0.70
   ✔ conf≥0.5 ✔ rough<0.30 ✔ compact_soil ✔ → **Zone 0.** ✅

2. **Same pad but perception unsure**, `conf 0.2`:
   class_f = 0.4+(1.0−0.4)·0.2 = 0.52 → score ≈ 0.35+0.25+0.104+0.20 = 0.904 (still
   high!), BUT the Zone-0 gate `conf ≥ 0.5` **fails** → **Zone 1.** *Low confidence
   blocked the approval even though the score was high — no false-safe.* ✅

3. **Smooth-looking crater floor**, `Cell(4°, 0.03, crater, 12 m, conf 0.9)`:
   great geometry, high score — but `terrain_class == "crater"` triggers Zone 3
   immediately. **Class overrides good geometry.** → **Zone 3.** ✅

4. **Soil next to a crater**, `Cell(3°, 0.02, soil, 2 m, ...)`: lovely soil, flat — but
   `crater_dist 2 < 3` → **Zone 3** (keep-out). *This is visible on the live dashboard:
   a high-scoring soil cell painted as hazard.* ✅

5. **Boulder**, `Cell(5°, 0.5, rock, 9 m, ...)`: gentle slope, but `rock` +
   `roughness 0.5 ≥ 0.30` → **Zone 3** (boulder). ✅

## 7.8 The trust gates — `guards.py`

Before a `Cell` is even built, `guards.py` rejects untrustworthy inputs at the
**trust boundary** (pure, deterministic):
- `is_stale(ts, now)` — frame too old / from the future / non-finite → reject.
- `valid_coord(x, y)` — outside the world grid → reject.
- `has_depth(z)` — missing/NaN depth → this cell can't be trusted.
- `degraded(sensor_quality)` — below an SNR/coverage floor → degraded mode.
Same philosophy as scoring: **when a signal can't be trusted, degrade toward caution.**

## 7.9 How we *prove* it (testing)

- **`scoring.py` self-check** (`_demo`) — asserts the worked-example zones.
- **`test_safety_regression.py`** — sweeps *ranges* (not single points): "for slope in
  {25,26,45,89}, crater at every distance, every low-conf value... assert it never
  reaches Zone 0." Sweeping ranges means a future threshold tweak that *re-opens* a
  false-safe **fails the test**.
- **`eval/metrics.py`** — a **false-safe rate** metric (fraction of GT-hazard cells the
  pipeline called Zone 0) with an integration check that real scoring never false-safes
  known hazards.
This is how "no false-safe" goes from a slogan to a *tested invariant*.

## 7.10 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| **Deterministic rules, no ML** for the decision | Auditable, testable, provable, predictable — mandatory for safety-critical | The adaptivity/accuracy a learned policy might have |
| Weighted-sum score | Simple, tunable, explainable per-factor | Can't capture nonlinear factor interactions a model could |
| Confidence collapses class → neutral 0.4 | Makes "no false-safe" structural, not hoped-for | Conservatism: refuses some ground a confident model would allow |
| **Four** independent Zone-0 gates | Defense-in-depth; no single number approves | Fewer Zone-0 cells (over-cautious) |
| Default **Zone 1** (prove-safe) | Unproven ≠ safe | — (this *is* the safety posture) |
| Thresholds are **tuning knobs**, not universal | Regolith mechanics vary per body/dataset | Requires per-dataset calibration to be *accurate* (vs merely *safe*) |
| **ML must not override the rules** | A model can inform (as a measurement) but never bypass the inspector | Can't let a great model "just decide" |

## 7.11 Alternatives
- **Learned safety policy (RL / classifier)** — could be more accurate, but a black-box
  safety decision is a non-starter for auditability; you'd never certify it.
- **Fuzzy logic / Bayesian risk model** — principled uncertainty propagation; heavier,
  harder to test exhaustively; a reasonable research direction *feeding* the rules.
- **Pure threshold table (no score)** — simpler, but the continuous score is useful for
  *ranking* candidate sites (see `sites`), which a hard table can't do.

---

## 7.12 Q&A

**Q: Why is the decision layer not ML?** Because it's safety-critical. A neural net is a
black box you can't fully verify or explain; a deterministic rule engine can be read,
tested exhaustively, and *proven* to never approve a hazard. Right tool for the job:
ML to *measure*, rules to *decide*.

**Q: How do you guarantee you never call bad ground safe?** Five stacked mechanisms:
NaN→0, confidence collapses class toward neutral, hazard precedence checked first, four
independent Zone-0 gates, and a default of Zone 1. And we *test* it with range sweeps
and a false-safe-rate metric — it's a tested invariant, not a hope.

**Q: What if perception is confidently wrong (says soil, it's a crater rim)?** Two
backstops still catch it: geometry (a rim has slope/roughness that trip Zone 3) and the
crater keep-out distance. The rules don't depend on the class label being right.

**Q: Isn't 60% weight on geometry arbitrary?** It reflects that geometry is measured
more reliably than material class, and it's a *tunable knob* — we're explicit that
thresholds/weights are per-dataset calibration, not universal physics.

**Q: Downside of your approach?** Over-caution — we refuse some genuinely-fine ground
(false negatives). For *this* problem that's the correct trade: re-surveying is cheap,
a collapsed habitat is not.
