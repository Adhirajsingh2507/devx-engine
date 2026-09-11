# 09 — Edge AI: running on a rover (budgets + quantization)

**Files:** `backend/app/edge/budget.py` (latency/memory harness),
`backend/app/edge/quantize.py` (INT8 quantization), `docs/architecture/edge-ai.md`.

---

## 9.1 From zero: what "edge" means and why it's hard

**Edge computing** = running the AI *on the device* (the rover) instead of in a
datacenter. For a planetary rover this isn't a preference, it's the whole point (the
latency wall — see `01`). But a rover's computer is nothing like a cloud GPU:

- **Rad-hard CPUs are ancient and slow.** Space processors (e.g. RAD750) are radiation-
  hardened for reliability, which means they run at *hundreds of MHz*, not GHz — roughly
  1990s-desktop speed. No fat GPU.
- **Power is scarce.** Every watt comes from solar panels / RTG; compute competes with
  driving, heating, and comms. Perception gets a *low-single-digit-watt* budget.
- **Memory is small** (~hundreds of MB), and there's no swapping to a cloud.
- **Real-time.** Decisions must keep up with driving, at a 1–5 s frame cadence.

So the job of "edge AI" is: make perception **small and fast enough** to run in that
envelope, without losing the safety guarantees.

## 9.2 Latency & memory budgeting (`budget.py`)

You can't optimize what you don't measure. `budget.py` **times each pipeline stage** and
the full run on the `scene_0` fixture (median wall-clock over repeats) and measures
**peak memory** with `tracemalloc`. It then checks each stage against a **budget**.

Measured on `scene_0` (a tiny 3×9 grid, dev machine): segmentation ~1 ms, depth ~1.3 ms,
fusion ~0.03 ms, terrain ~0.15 ms, full run ~5.4 ms, ~45 KiB peak.

**Honesty about the numbers:** the budgets are *generous smoke ceilings* on a dev laptop,
not the real rover CPU target — a laptop has no thermal/power throttling and isn't
representative. Their job is to catch a **10–100× regression** (e.g. an accidental O(n³)
loop landing in a "measurement" stage), not to certify rover-readiness. The *real* target
envelope (rad-hard CPU class, ~256 MB RAM, low-watt, 1–5 s cadence) lives in `edge-ai.md`
as the design input to tune against once real hardware exists. Naming that gap explicitly
is the point — it's an honest budget framework, not a fake benchmark.

## 9.3 Quantization (`quantize.py`) — from zero

**Quantization** = storing numbers with *fewer bits* to save memory and speed up math.
Neural nets normally use **32-bit floats** (`float32`). **INT8 quantization** stores each
number as an **8-bit integer** (0–255 range) — **4× smaller**, and integer math is much
faster and lower-power than float math (huge on a CPU with no GPU).

The trick is the mapping. **Affine (asymmetric) quantization:**
```
scale      = (max − min) / 255
zero_point = round(−min / scale) − 128
q          = clip( round(x / scale) + zero_point, −128, 127 )   # store this int8
dequant(q) = (q − zero_point) · scale                            # recover ≈ x
```
You lose a little precision (rounding), which is why you must *verify accuracy didn't
break*.

**What we quantize:** our segmentation classifier's only float "parameters" are its
**class-colour centroids** in the 6-D feature space (the classical stand-in has no neural
weights — depth/SLAM have *no* learned parameters at all). `quantize.py` quantizes those
centroids per-feature-dimension to INT8, and `classify_int8` does nearest-centroid in the
dequantized space.

**Result:** ~**8× smaller** centroid storage, and — the safety-critical check — the
self-check proves **0 class flips** across the 8 centroids and all 27 `scene_0` cells,
with hazard classes explicitly verified stable, and confidence only ever *decreased* by
quantization (a `_MARGIN_DERATE = 0.9` ensures rounding can't make it look *more*
confident). **Quantization must not create a false-safe** — and it's proven not to.

## 9.4 The bigger edge story (what happens when a real model lands)

`edge-ai.md` documents the plan for when a trained model replaces the classical stages:
- **Backbone decision: MobileNetV3-Small** — a CNN designed for phones/edge: cheap
  per-parameter accuracy on CPU, a well-trodden INT8 quantization target, ~2.5 M params
  fits the envelope. The *interim* "backbone" is the classical stack.
- **Quantization pipeline:** train → export to **ONNX** → INT8 **post-training
  quantization** (fallback to FP16 / quantization-aware training) → **ONNX Runtime** on
  CPU — gated on entry criteria (IoU beats the classical baseline, latency within budget,
  safety regression still green).
- **Depth/SLAM have no weights** → their shrink levers aren't quantization but **input-
  resolution downscale** and matcher/search-radius knobs (same accuracy↔cost trade,
  applied to inputs instead of weights).
- **Cadence tricks** (documented, not yet implemented): run heavy segmentation *less
  often* than depth; **skip inference when the scene is static** (frame-diff gate). These
  cut average compute without touching the model.

## 9.5 Decisions & tradeoffs

| Decision | Why | Gave up |
|---|---|---|
| **Quantize the classifier now** (even though it's classical) | Proves the INT8 capability + no-false-safe under quantization; real 8× shrink | The absolute byte savings are tiny (8 centroids) — the *scheme* is the value, not the size |
| Budgets are **generous smoke ceilings** | A dev laptop can't represent a rad-hard CPU; tight ceilings would be flaky | Can't claim "meets rover latency" — honestly, that needs real hardware |
| **Defer** the trained model / real quantization pipeline | No labelled data yet; keep `torch`/`onnxruntime` off until a model earns them | Real accuracy today |
| MobileNetV3-Small as the **target** | Best accuracy/watt on CPU, quantizes cleanly | Some accuracy vs a bigger backbone we can't afford on-rover |

## 9.6 Alternatives
- **Pruning + distillation** (shrink a big model into a small one) — complements
  quantization; standard edge toolkit.
- **FPGA / neuromorphic accelerators** — some space processors add these; huge speedups,
  but hardware-specific and complex.
- **TensorRT / TFLite / ONNX Runtime** — the deployment runtimes; we name ONNX Runtime as
  the CPU target.
- **Do it in the cloud** — impossible here (latency wall). Naming *why* the obvious
  answer fails is itself a good interview point.

## 9.7 Q&A
**Q: Why is edge hard for a rover specifically?** Rad-hard CPUs are ~1990s-slow, power is
scarce, memory is tiny, and there's no cloud fallback — all while needing real-time
decisions.

**Q: What did you actually quantize?** The classifier's colour centroids to INT8 (8×
smaller), with a self-check proving zero class flips and no false-safe under quantization
— the *capability and its safety* are demonstrated even though the current model is
classical.

**Q: Are your latency numbers rover-representative?** No — they're smoke ceilings on a dev
machine to catch gross regressions. Real rover budgets need real (or emulated) rad-hard
hardware; that's documented in `edge-ai.md`, not faked.

**Q: How would you deploy a real model to the rover?** MobileNetV3-Small → ONNX → INT8
post-training quantization → ONNX Runtime on CPU, gated on beating the classical baseline
and keeping the safety regression green.
