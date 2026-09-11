# 13 — Hackathon / Judge Questions (with model answers)

How judges actually probe, and exactly how to answer — including the honest framing
that turns your biggest "weakness" into a strength.

---

## 13.1 The 90-second pitch (open with this)

> "A planetary rover can't ask Earth 'is this ground safe to build on?' and wait 40
> minutes for an answer — the latency wall makes real-time human control impossible. So
> the rover needs onboard eyes and a brain. TerraSight takes the rover's camera feed,
> figures out what each patch of ground is and how steep and rough it is, and labels the
> world into four decision zones — safe-to-build, drivable, science-protected, hazard —
> scoring each patch for construction, **all onboard, in real time.** The core is a
> safety guarantee: the system is architecturally prevented from ever calling dangerous
> ground safe. Uncertainty always degrades toward caution. It's a full working stack —
> perception → a deterministic safety decision → an API → a live 3D dashboard — deployed
> and running right now at terrasight-liard.vercel.app."

## 13.2 The honest framing (say it *before* they force it out)

Judges will ask "is the AI real?" Get ahead of it:

> "Let me be upfront about what's real and what's simulated. The **decision layer, the
> safety guarantees, the API, persistence, edge quantization, and the dashboard are real
> and deployed.** The **perception stages currently run as classical algorithms on
> simulated data — there's no trained neural net yet.** But here's why that's a
> deliberate strength, not a gap: we built the entire system behind **frozen interfaces**,
> so dropping in a trained model is a bounded, documented step — not a rewrite. And
> critically, **our safety guarantee doesn't depend on the model being good** — even a
> perfect model can't force a false-safe, because the deterministic decision layer sits
> between perception and the verdict. We chose to build a *complete, safe, demoable
> system* over a single half-trained model with nothing around it."

**Why this wins:** it's honest (judges respect it), it reframes the gap as engineering
maturity, and it forecloses the "gotcha." Never let a judge *catch* you on this — *own* it.

## 13.3 Demo script (what to click, in order)

1. Open the **dashboard** (`/`). Point at the KPIs: "82% average safety, 6 buildable
   sites, 15 hazard cells."
2. Point at the **terrain grid**: "Cell colour is the *zone*, not the score. See this
   soil cell — high score, but painted hazard? That's the crater keep-out overriding good
   geometry. **That's the safety layer refusing to be fooled by a nice-looking cell next
   to a pit.**"
3. Hover a cell: "class, slope, height — the measurements behind the decision."
4. Open **Surface View** (`/explore`): "Same perception data, rendered as a driveable 3D
   world — this is the terrain the rover reasons about. Green beacons are candidate build
   sites."
5. (If asked) show `/api/backend/map/tiles` in a browser: "The frozen contract, served
   live."

The money moment is step 2 — a visible false-safe *prevented*.

## 13.4 The questions judges ask — and model answers

**Q: Is this actually AI / is the model trained?**
See 13.2. Own it: real system + real safety layer, classical perception, model-ready.

**Q: What's novel here? Isn't terrain classification solved?**
"The novelty isn't a new segmentation net — it's the **safety architecture**: a strict
measurement↔decision split where uncertainty is *mathematically* forced toward caution,
so the system can't be tricked into approving hazardous ground even by confident wrong
perception. For *autonomous construction*, being un-foolable matters more than being 2%
more accurate."

**Q: Why can't you just stream video to Earth?**
"The latency wall — Mars is 3–22 light-minutes away; a round trip is 6–44 minutes. You
can't put a human in a rover's real-time loop. The decision *must* be onboard."

**Q: What happens when the camera is blinded / a sensor fails / it's in shadow?**
"Everything degrades toward caution. Missing depth becomes NaN, which scores 0 — treated
as bad, never neutral. Unlit pixels are labelled shadow, never guessed. Low perception
confidence collapses the class contribution toward neutral, so an unsure reading can't
approve construction. And the rover's own mode drops full→cautious→survey→safe-hold as
its localization confidence falls. **The system's failure mode is over-caution, by
design.**"

**Q: How do you *know* it never calls bad ground safe?**
"Five stacked mechanisms — NaN→0, confidence-collapse, hazard-precedence-first, four
independent Zone-0 gates, and a Zone-1 default — and we *test* it: a regression suite
sweeps ranges of inputs asserting no configuration reaches Zone 0 when it mustn't, plus a
false-safe-rate metric that's currently zero on known hazards. It's a tested invariant,
not a hope."

**Q: What's your accuracy / IoU?**
"Be careful with that number for us: our segmentation 'IoU 1.0' is a *self-consistency*
check (the classifier fed its own reference colours), not accuracy against labelled
reality — we don't have a real labelled dataset yet. So I won't quote it as accuracy.
What I *can* stand behind is the safety invariant and the end-to-end contract validity,
which we verify on live production."

**Q: How would you make it real / what's next?**
"Three bounded steps: (1) wire a real stereo image pair through the SGBM depth path;
(2) train a MobileNetV3-small segmenter on a labelled planetary dataset (AI4Mars, ESA
Katwijk) and drop it behind the frozen `SegCell` interface — nothing downstream changes;
(3) INT8-quantize it for the rover, which we've already proven doesn't create a false-safe.
The system was built to make each of these a plug-in, not a rewrite."

**Q: What was the hardest part?**
Pick one and tell it as a story: the measurement↔decision boundary design; or the prod
backend 404 bug (Vercel's `services` rewrite doesn't strip the path prefix — only a live
`curl` caught it, "it builds ≠ it works").

**Q: Real-world impact / who cares?**
"Autonomous site selection for lunar/Mars bases (Artemis, ISRO's lunar ambitions), and the
same safety-first perception→decision pattern applies to Earth robotics — disaster-zone
robots, autonomous mining, construction — anywhere a machine must decide 'is this ground
safe' without a human in the loop."

**Q: Why should uncertainty make it *more* cautious? Isn't that just refusing to work?**
"Yes — and that's correct for construction. A false 'no' costs you a re-survey; a false
'yes' sinks a habitat. We deliberately accept over-caution (false negatives) to make
false-positives structurally impossible. It's the same asymmetry as a smoke alarm: better
a few false alarms than one missed fire."

## 13.5 Traps to avoid
- **Don't** claim it's a trained deep-learning model. You'll get caught, and it's
  unnecessary — the honest story is stronger.
- **Don't** quote IoU 1.0 as accuracy.
- **Don't** say "it's fully autonomous and production-ready." Say "the system and safety
  layer are real and deployed; perception is a model-ready classical stand-in."
- **Don't** show a blank/broken screen — the frontend has a mock fallback; know it's there
  so you can explain "Simulation vs Live" if the badge shows Simulation.

## 13.6 One-liners to keep in your pocket
- "The system's failure mode is over-caution, **by design**."
- "Uncertainty degrades toward caution — we can refuse good ground, but we're
  architecturally prevented from ever approving bad ground."
- "Measurement is a clever intern; the decision is a strict safety inspector. The intern
  informs the inspector but never overrules it."
- "It builds ≠ it works — we verify on live production, not on a green checkmark."
- "You can't use GPS on Mars — that's *why* localization must be onboard."
