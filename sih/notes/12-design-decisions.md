# 12 — System-Design Decisions: what we chose, why, and what we traded ⭐

This is the file that turns "I built it" into "I *designed* it." Every significant
decision, the reasoning, the alternative we rejected, and — crucially — **what we
gained and what we gave up.** Good engineering isn't picking the "best" option; it's
picking the right *trade* for the constraints. Interviewers and judges probe exactly
this.

A frame to use out loud: *"Every design choice buys you something and costs you
something. Here's what we bought, and what we paid."*

---

## Decision 1 — Split measurement from decision (the keystone)

**Choice:** Perception stages (segmentation/depth/SLAM/terrain) only *measure* the
world; a single deterministic layer (`scoring.py`) makes *every* zone decision. The
boundary is enforced by a runnable test (terrain assembly is proven to never call
scoring).

**Why:** The decision is safety-critical and must be auditable, testable, and provable.
ML perception is a black box you can't fully verify. So we quarantine the black box on
the *measurement* side and make the *decision* a transparent rule engine.

**Alternative:** One end-to-end model that goes pixels → zones directly.
**Gained:** Auditability, exhaustive testability, a provable "no-false-safe," and a
clean seam (swap the model without touching the decision).
**Gave up:** The raw accuracy and adaptivity a single learned policy *might* achieve; and
some engineering overhead maintaining the interface.

> This is the decision to lead with. It's the project's identity.

---

## Decision 2 — Deterministic rules for the safety decision (no ML there)

**Choice:** The Safety Score + Zone logic is plain, deterministic if/else math.

**Why:** You can read it, test every branch, and *prove* it never approves a hazard.
Certification bodies (and judges) trust rules they can inspect; nobody certifies a black
box for a life-safety decision.

**Alternative:** A learned safety policy (classifier / reinforcement learning).
**Gained:** Predictability, transparency, provable invariants, trivial debugging.
**Gave up:** Potential accuracy on nuanced cases a model could learn; adaptivity.

---

## Decision 3 — Make "no false-safe" *structural*, not *hoped-for*

**Choice:** Uncertainty mathematically degrades toward caution. Concretely: NaN/inf → 0;
`class_f = 0.4 + (bearing−0.4)·conf` collapses unsure classes to neutral; hazard
precedence is checked first; Zone 0 needs *four* independent gates; the default is Zone 1.

**Why:** "We tested that it usually behaves" is not a safety guarantee. We wanted the
*math* to make a false-safe impossible, not merely unlikely.

**Alternative:** Score everything, threshold at the end, rely on tests to catch bad
cases.
**Gained:** A safety property that holds *by construction* and is locked by range-sweep
regression tests + a false-safe-rate metric.
**Gave up:** Zone-0 coverage — we over-refuse good ground (false negatives). For this
problem that's the correct asymmetry: re-surveying is cheap, a collapsed habitat isn't.

---

## Decision 4 — Four zones, not binary safe/unsafe

**Choice:** Zone 0 (build) / 1 (drive) / 2 (protect-science) / 3 (avoid), precedence
hazard > geological > navigation > safe.

**Why:** A rover has *multiple jobs* — building, driving, doing science, surviving. One
binary label can't serve navigation *and* science-protection *and* construction. Zone 2
in particular says "scientifically precious — don't bulldoze it," which "unsafe" would
wrongly lump with hazards.

**Alternative:** Binary buildable / not-buildable.
**Gained:** Actionable labels for every rover subsystem; protects science targets.
**Gave up:** Simplicity; more rules and thresholds to define and defend.

---

## Decision 5 — Freeze the API contract on day one

**Choice:** Fix the five endpoint shapes immediately; lock them with a test; serve them
from mock before the real pipeline existed.

**Why:** Let the frontend and backend/ML teams build fully in parallel without blocking
each other or renegotiating shapes.

**Alternative:** Let the API evolve as the backend matures; frontend adapts continuously.
**Gained:** True parallelism (the frontend was contract-perfect and worked with the real
backend on day one); a stable integration target; drift caught by CI.
**Gave up:** Flexibility to change shapes freely later — any change is now a coordinated
event. (We consider that discipline a feature.)

---

## Decision 6 — Mock-or-Supabase fallback

**Choice:** `db.fetch` serves live Supabase when configured, else `mock/*.json`; same code
path.

**Why:** The API must never block on database provisioning, and the deploy should work
with zero secrets.

**Alternative:** Require a real database always.
**Gained:** Frontend never blocked; prod deploys secret-free (serves mock); swap to live
= one env var, no code change; resilient demos.
**Gave up:** A second (mock) source of truth to keep consistent with the schema.

---

## Decision 7 — Build the *skeleton* first: classical stubs behind frozen interfaces

**Choice:** Implement every perception stage as an honest classical stand-in behind a
frozen internal contract (`SegCell`, `DepthCell`, `FusedCell`), rather than pouring all
time into one real model.

**Why:** Hackathon time is finite. A *complete, correct, end-to-end system* with a
provable safety property and a working demo beats a single half-trained model with no
system around it. The frozen interfaces mean a real model drops in without a rewrite.

**Alternative:** Spend the whole hackathon training one segmentation model.
**Gained:** A full working pipeline, a real decision layer, a deployed demo, and
model-readiness — all defensible.
**Gave up:** Real perception accuracy today (the honest caveat). We bet that *system +
safety + demo* scores better than *one model, no system* — and it lets us frame the model
as a bounded next step.

---

## Decision 8 — Ship the smallest working end-to-end slice first (P0/P1)

**Choice:** First deliverable was a thin thread through *every* stage (stub → stub → …→
scoring → API → served), before deepening any single stage.

**Why:** An end-to-end slice de-risks integration early and gives a demoable product at
all times; isolated-perfect stages that don't connect are worthless at a demo.

**Alternative:** Perfect segmentation, then perfect depth, then integrate at the end.
**Gained:** Always-demoable; integration bugs found early; a stable contract for parallel
work.
**Gave up:** Early depth in any single stage (each stage started shallow, deepened later).

---

## Decision 9 — Lean deployed backend; heavy CV is offline/rover tooling

**Choice:** The API installs `requirements.txt` only; numpy/opencv/torch live in
`requirements-cv.txt`, never in the deployed function (`app.main` doesn't import them).

**Why:** The serverless API only *serves* precomputed results; loading a CV stack would
bloat cold starts and cost for no benefit. Perception runs on the rover / offline.

**Alternative:** One fat backend that both serves *and* runs CV.
**Gained:** Fast, cheap, small deployed function; a clean "serve vs compute" separation.
**Gave up:** Can't run CV *inside* the API (by design — it's the wrong place for it).

---

## Decision 10 — The cell/grid is the unit of decision (not the pixel)

**Choice:** Classify/score per grid cell, not per pixel.

**Why:** "Can a lander leg go *here*?" is a per-patch question; cells are the natural
granularity and vastly cheaper than per-pixel decisions.

**Alternative:** Per-pixel zones.
**Gained:** Cheap, matches the real decision, easy to serve/draw.
**Gave up:** Sub-cell spatial detail.

---

## Decision 11 — NaN means "bad," never "neutral"

**Choice:** Any missing/invalid measurement forces its safety contribution to 0.

**Why:** A dropped sensor or failed stereo match must read as *worse*, never as
flat/far/safe — otherwise sensor failure could cause a false-safe.

**Alternative:** Impute missing values (fill with a default/average).
**Gained:** Sensor failure degrades toward caution automatically.
**Gave up:** Coverage — some cells have no verdict rather than a guessed one (the safe
error).

---

## Decision 12 — Thresholds are per-dataset calibration knobs, not universal constants

**Choice:** Slope/roughness/crater thresholds and camera calibration are explicitly
"tuning knobs," stored as data (calibration JSON), differing per body/dataset.

**Why:** Regolith mechanics and camera rigs vary (lunar ≠ Mars-analog); pretending a
threshold is universal physics would be dishonest and brittle.

**Alternative:** Hard-code "the" thresholds.
**Gained:** Honesty; easy re-tuning per dataset without code changes.
**Gave up:** Accuracy is only as good as the calibration — you must tune per dataset to be
*accurate* (though the system is *safe* regardless).

---

## Decision 13 — Testing = tested *invariants*, not just examples

**Choice:** `test_safety_regression.py` sweeps *ranges* of inputs; `eval/metrics.py` has a
false-safe-rate metric; the measurement↔decision boundary is asserted by monkey-patching.

**Why:** Point tests prove "these examples work"; range sweeps prove "no configuration in
this space breaks the invariant," so a future threshold tweak that reopens a false-safe
*fails CI*.

**Alternative:** A few example unit tests.
**Gained:** Safety properties become continuously-enforced invariants.
**Gave up:** More test-writing effort (worth it for a safety system).

---

## Decision 14 — Development workflow: one owning agent + skill per domain

**Choice:** Each subsystem (perception, depth, SLAM, scoring, dataset, edge, devops,
testing) has an owning agent + a domain "skill," with a frozen contract between them, and
a human/orchestrator integrating.

**Why:** Clear ownership + frozen interfaces let parallel work proceed without collisions;
each domain is reasoned about by a specialist.
**Gained:** Parallelism, separation of concerns, consistent per-domain quality.
**Gave up:** Coordination overhead; risk of a wrong domain call (which is exactly why the
orchestrator independently verifies — e.g., we caught the Vercel two-project
misdiagnosis).

---

## The one-slide summary (for a judge)

> We separated **measurement (fast, fallible ML/CV)** from **decision (slow, trustworthy
> rules)**; made **safety structural** so uncertainty always degrades toward caution;
> **froze the contract** so we built full-stack in parallel; and **built the whole
> skeleton end-to-end** with honest classical stand-ins behind frozen interfaces, so a
> trained model is a bounded drop-in, not a rewrite. Everywhere, we chose **auditable and
> safe over clever and opaque** — and we can point to the exact line of code and the exact
> test that enforces each of those choices.
