# 14 — Technical Interview Questions (with model answers)

Organized by area. Answers are concise model answers you can expand. Practice saying
them out loud.

---

## A. System design & architecture

**Q: Walk me through your architecture.**
Six stages: segmentation, stereo depth, SLAM/fusion, terrain analysis (all *measurement*),
then a deterministic scoring/zone *decision* layer, then a FastAPI serving a frozen
contract to a Next.js frontend. The key design axis is the **measurement↔decision split**:
perception only reports facts + confidence; a single pure-rules layer makes every safety
decision, so it's auditable and provably can't be tricked into a false-safe.

**Q: Why separate measurement from decision?**
Safety-criticality. ML perception is a non-verifiable black box; a life-safety decision
must be inspectable, exhaustively testable, and provable. Quarantining the black box on
the measurement side and making the decision deterministic gives you both good guessing
*and* a trustworthy verdict. Bonus: it's a clean seam — swap the model without touching
the decision.

**Q: How do you enforce that boundary in code, not just convention?**
The terrain-assembly module's self-check monkey-patches `zone`/`safety_score` with call
counters and asserts zero calls. The measurement↔decision rule is a *tested invariant*.

**Q: How would this scale to a real, huge map / continuous operation?**
Move from per-scene grids to a tiled, streaming world grid; add loop closure to bound SLAM
drift; replace the O(n²) boundary walk with a distance-transform / contour extraction;
persist incrementally to Supabase (already idempotent); and add delta-encoding for the
Earth downlink (send only changed high-priority tiles).

**Q: What are the failure modes and how does the system degrade?**
Missing/invalid data → NaN → scores 0 (bad, not neutral). Low perception confidence →
class collapses to neutral 0.4 (can't approve). Low localization confidence → rover mode
full→cautious→survey→safe-hold. Every failure mode degrades toward caution, by construction.

**Q: If you had one more week, what would you build?**
Wire a real stereo pair through SGBM (turn "synthetic" into "real frame"), train a
MobileNetV3 segmenter behind the frozen interface, and add SLAM loop closure. All are
plug-ins by design.

## B. Computer vision & ML fundamentals

**Q: What is semantic segmentation, and how would you build a real one here?**
Per-pixel classification (label every pixel). Real answer: a U-Net or DeepLabv3+ CNN
(encoder-decoder with skip connections) trained with cross-entropy on labelled terrain;
for a rover, a MobileNetV3-small backbone, INT8-quantized, on ONNX Runtime.

**Q: How does stereo depth work?**
Two offset cameras; the same world point lands at different horizontal pixels (disparity
`d`). Depth `Z = f·b/d` (focal × baseline / disparity). Hard part is *matching* — finding
the corresponding pixel — classically via SGBM (semi-global block matching). Invalid
matches → NaN depth, never a fabricated value.

**Q: What is SLAM and why is it hard?**
Simultaneous Localization And Mapping — estimate pose *and* build the map, each depending
on the other. Hard because of the chicken-and-egg bootstrap and **drift** (accumulating
pose error). Fixes: loop closure, sensor fusion (IMU + wheel odometry + vision).

**Q: Featureless terrain breaks visual SLAM — what do you do?**
Corner-based tracking fails on uniform regolith. We use height-field SSD registration
whose confidence is sharpness×coverage, so a flat patch *self-reports* low confidence
(every shift scores equally), and we degrade to cautious/survey mode and lean on odometry.

**Q: What is confidence, and why does it matter for safety?**
A [0,1] estimate of how sure a prediction is. In our system it's the lever that enforces
"no false-safe": `class_f = 0.4 + (bearing−0.4)·conf`, so low confidence drags the score
toward neutral — an unsure label can't approve construction.

**Q: What is quantization? What did you quantize and how did you verify safety?**
Storing numbers in fewer bits (INT8 = 8-bit) for 4× smaller, faster integer math. We
INT8-quantized the classifier's colour centroids (affine, per-dimension), verified 0 class
flips on the fixture + hazard cells stable, and a margin derate ensures quantization can
only *lower* confidence — so it can't create a false-safe.

**Q: Precision vs recall — which do you optimize, and why?**
For "is it safe to build," we optimize **precision of the 'safe' label** (never a
false-positive) at the cost of recall (we miss some genuinely-safe ground). A false 'safe'
is catastrophic; a false 'unsafe' just means re-survey. Same asymmetry as a medical test
for a deadly disease.

## C. Backend, API, data

**Q: Why FastAPI? Why a frozen contract?**
FastAPI: fast, typed, minimal for a small read API. Frozen contract: lets frontend and
backend build in parallel against fixed shapes; a test locks the shapes so drift fails CI.

**Q: How does the app work without a database?**
`db.fetch` returns Supabase data when `SUPABASE_URL/KEY` are set, else reads `mock/*.json`
— same code path. The prod deploy runs secret-free on mock; swap to live = one env var.

**Q: How do you make writes idempotent?**
The pipeline regenerates the whole map each run, so `persist` upserts on natural keys
(tiles on (x,y), sites on id, path on t) and full-replaces boundaries (no natural key) —
re-runs overwrite in place, never duplicate.

**Q: How do you keep the service-role key safe?**
Backend env only, never `NEXT_PUBLIC_*`, never in the bundle, never committed (CI greps
for it). RLS: public read, backend write via service-role bypass.

**Q: A production endpoint 404s but the build was green — how do you debug?**
Exactly what happened: `curl` the live endpoint. `{"detail":"Not Found"}` = FastAPI running
but no matching route → a *path* problem. Root cause: Vercel's `services` rewrite forwards
the full `/api/backend/*` path unstripped; FastAPI routes are unprefixed. Fix: a
`StripPrefix` ASGI middleware → proxy-agnostic. Lesson: "it builds ≠ it works."

## D. Frontend

**Q: Why did the frontend integrate with the backend with zero rework?**
Both were built against the same frozen contract; `types.ts` mirrors the endpoint shapes
exactly, and the API base defaults to the same-origin `/api/backend` the deploy provides.

**Q: How does the dashboard stay resilient?**
Live→mock fallback: it tries `/api/backend/*`, falls back to bundled `public/mock/*.json`,
so it never shows a blank screen; `/health` drives a Live/Simulation badge.

**Q: Why render zones by colour and the score as text?**
So the *decision* is visible: a high-score cell painted hazard (crater keep-out) shows the
safety layer overriding good geometry. (Weakness: brightness-only encoding is an
accessibility gap.)

## E. DevOps

**Q: How do you prevent broken code from merging?**
A single `validate-terrasight.sh` gate (syntax, imports, safety regression, contract
shapes, frontend build, secret grep) runs locally *and* in GitHub Actions on every PR.

**Q: Why is the deployed backend so small?**
It installs `requirements.txt` only — the API just serves precomputed results; CV deps
(numpy/opencv) are offline/rover tooling, never in the serverless function.

**Q: Tell me about a deployment bug.**
(Pick from `11.5`: the `output:standalone` build break, or the `services` prefix 404.) The
meta-lesson: local-dev and prod behaved differently; only a real prod check caught it.

## F. CS fundamentals (they'll sneak these in)

**Q: What's the time complexity of your boundary tracing?**
O(n²) greedy nearest-neighbour per feature class (n = border cells) — fine per scene;
documented ceiling is a KD-tree or distance transform for large grids.

**Q: Standard deviation — what is it and where do you use it?**
The typical distance of values from their mean (`sqrt(mean((x−mean)²))`). We use it for
**roughness** — the spread of heights in a 3×3 neighbourhood (bumpiness).

**Q: What's a race condition / how do you avoid one in `persist`?**
Concurrent writes clobbering each other. Our rover is effectively a single writer, and the
full-map replace is per-table; at real scale you'd wrap it in a transaction. (Naming the
single-writer assumption is the good answer.)

**Q: Determinism — why does it matter here?**
Same input → same output, always. It makes the safety decision testable and provable; you
can assert "no input in this range reaches Zone 0" and it *stays* true. ML lacks that.

**Q: How do you test something that must never happen (a false-safe)?**
You can't enumerate infinite inputs, so you **sweep ranges** across the input space
asserting the invariant holds, and add a metric (false-safe rate) that would go non-zero
if it broke. Property-style testing over example-based.

## G. Behavioral / project

**Q: What are you most proud of?**
Making "no false-safe" a *structural, tested* property rather than a hope — you can point
at the exact lines (NaN→0, confidence collapse, precedence, four gates) and the exact
tests that lock them.

**Q: What's the biggest weakness / what would you do differently?**
No trained perception model or real imagery yet, so it doesn't generalize to real terrain.
I'd budget time to wire one real stereo pair and train a small segmenter earlier — though
building the safe, complete system first was the right call for a demo.

**Q: How did you divide the work?**
Owning agent + skill per domain (perception, depth, SLAM, scoring, dataset, edge, devops,
testing) behind frozen interfaces, with independent integration verification — which is
how we caught a wrong platform-config call before it shipped.

**Q: If perception is a black box, how can you trust the whole system?**
Because the black box only *measures*; it can't *decide*. The deterministic decision layer
between perception and the verdict means even confidently-wrong perception can't force an
unsafe approval — geometry and keep-out backstops still apply, and low confidence degrades
toward caution.
