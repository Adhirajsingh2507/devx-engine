# 01 — The Big Picture (from zero)

## 1. The problem we're solving

Humanity wants to build things on the Moon and Mars — habitats, landing pads,
solar arrays, mining sites. To build, you first need to answer a simple-sounding
question for every patch of ground:

> **"Is this piece of ground safe and suitable to build on?"**

On Earth, a human surveyor answers this. On another planet, there is no human.
There *is* a rover with cameras. The obvious idea: stream the video to Earth, let
humans decide. **This does not work**, for one brutal reason:

### The latency wall (the reason TerraSight exists)

Radio signals travel at the speed of light. Mars is **3 to 22 light-minutes** from
Earth depending on orbits. A round trip (rover asks → Earth answers) is **6 to 44
minutes**. During those minutes the rover is either frozen (wasting a mission that
costs hundreds of millions of dollars) or driving blind. You **cannot** put a human
in the real-time control loop of a planetary rover.

**Therefore the decision must happen *on the rover*.** That is the whole thesis.
The rover needs onboard "eyes and a brain" that turn camera pixels into
build/drive/avoid decisions **autonomously, in real time**.

That onboard eyes-and-brain is **TerraSight**.

## 2. What TerraSight produces (the output)

TerraSight labels every patch of ground ("cell") into one of **four zones**, and
gives each a **Safety Score** from 0 to 1.

| Zone | Name | Meaning | Rover action |
|------|------|---------|--------------|
| **0** | Construction-safe | Flat, compact, high load-bearing, clear of hazards | Build here |
| **1** | Navigation-only | Drivable, but not safe to build (loose/uneven) | Drive across, don't build |
| **2** | Geological interest | Ancient water beds, ice, mineral edges | Protect / study, don't disturb |
| **3** | Hazard | Crater rims, steep slopes, boulders | Route around it |

**Why four zones and not just "safe / not safe"?** Because a rover has *multiple
jobs*: it must build (needs Zone 0), navigate (Zone 1 is fine), do science (Zone 2
must be protected, not bulldozed), and survive (Zone 3 must be avoided). One
binary label can't serve all four. This is a real design decision — see `12`.

**Precedence when signals conflict:** `hazard > geological > navigation > safe`.
If a patch looks flat and buildable but sits on a crater rim, it is Zone 3. **When
in doubt, never Zone 0.** This single rule is the safety soul of the project.

## 3. The pipeline — how pixels become zones

Think of it as an assembly line. Raw camera data enters on the left; decisions
come out on the right. Each station does one job and hands a clean, well-defined
package to the next.

```
   CAMERAS                 PERCEPTION (measure the world)              DECISION        SERVE
 ┌─────────┐   ┌──────────────────────────────────────────────┐   ┌───────────┐   ┌────────┐
 │ left +  │   │ 1. Segmentation   "what is this pixel?"        │   │           │   │        │
 │ right   │──▶│    → terrain class + confidence                │   │           │   │        │
 │ (stereo)│   │                                                │   │           │   │        │
 │ + RGB   │   │ 2. Stereo depth   "how far / how steep?"       │──▶│ 5. SAFETY │──▶│ 6. API │──▶ frontend
 └─────────┘   │    → depth, slope, roughness                   │   │  SCORE +  │   │ (frozen│   (dashboard
               │                                                │   │  ZONE     │   │contract)   + 3D view)
               │ 3. SLAM/fusion    "where am I? one world map"   │   │           │   │        │
               │    → world-aligned grid + rover path           │   │ the ONLY  │   │        │
               │                                                │   │ place a   │   │        │
               │ 4. Terrain analysis  "describe each cell"      │   │ decision  │   │        │
               │    → class, slope, roughness, crater-distance  │   │ is made   │   │        │
               └──────────────────────────────────────────────┘   └───────────┘   └────────┘
                        MEASUREMENT (facts about the world)          DECISION (rules)
```

Read that boundary carefully — it's the most important idea in the whole project:

- **Stages 1–4 are MEASUREMENT.** They only report *facts*: "this pixel looks like
  rock," "this cell has an 18° slope," "confidence 0.6." They never decide anything.
- **Stage 5 is the ONLY DECISION.** It takes the measurements and, using
  **deterministic rules** (plain if/else math, no AI), produces the Safety Score
  and Zone.

Why separate them so strictly? Because the decision is **safety-critical** and
must be **auditable, testable, and impossible to fool**. A neural network is a
black box you can't fully verify. So we keep the black-box parts (perception) on
the *measurement* side, and make the *decision* a transparent rule engine that a
human can read, test, and trust. This is the **measurement ↔ decision split**, and
it's covered deeply in `07` and `12`.

## 4. The stages in one line each

1. **Segmentation** (`backend/app/perception/segment.py`) — classifies each pixel
   into 9 terrain classes (compact_soil, soil, loose_soil, rock, crater, shadow,
   waterbed, mineral_edge, unknown) with a **confidence** 0–1.
2. **Stereo depth** (`backend/app/depth/`) — uses the *two* camera images (left/right)
   to compute how far away each point is, then derives **slope** (degrees) and
   **roughness** (metres) per cell.
3. **SLAM / fusion** (`backend/app/slam/`) — figures out how the rover moved between
   frames and fuses many frames into **one** consistent world map + the rover's path.
4. **Terrain analysis** (`backend/app/terrain/assemble.py`) — packages each grid cell
   into a descriptor (class, slope, roughness, distance-to-nearest-crater) and traces
   region boundaries (crater rims, mineral edges).
5. **Safety scoring** (`backend/app/scoring.py`) — the deterministic rule engine:
   descriptors → `safety_score ∈ [0,1]` + `zone ∈ {0,1,2,3}`.
6. **API** (`backend/app/main.py`) — a FastAPI server that exposes the results as a
   **frozen contract** (`/map/tiles`, `/rover/path`, `/sites`, `/boundaries`,
   `/health`) that the frontend consumes.

The **frontend** (Next.js + Three.js) shows a 2D mission-control dashboard and a
drive-the-rover 3D voxel view of the terrain.

## 5. The two "brains": measurement is smart-but-fallible, decision is dumb-but-trustworthy

A mental model that will serve you in every Q&A:

- **Perception = a clever intern.** Fast, sees patterns, but sometimes wrong and
  can't explain itself. Great at *guessing what things are*.
- **Scoring = a strict, boring safety inspector.** Follows a written rulebook to
  the letter, never improvises, can justify every decision. Great at *deciding what's
  allowed*.

You want the intern to *inform* the inspector, but you never let the intern
*overrule* the inspector. That's the architecture.

## 6. What's real vs simulated (repeat until reflexive)

The **decision layer, API, persistence, edge quantization, and frontend are real
and deployed.** The **perception stages are classical algorithms on synthetic
data** — there's no trained neural net yet, and no real Mars image has flowed
through the pipeline. This is honestly documented, the interfaces are frozen so a
real model drops in cleanly, and — crucially — **the safety guarantees don't
depend on the model being good.** That last point is the whole pitch. Details and
how to say it under pressure: `13`.

---

### Check yourself
- Why can't a human make the rover's real-time decisions? *(latency wall)*
- What are the 4 zones and the precedence rule? *(hazard > geo > nav > safe)*
- Which stage is the *only* one allowed to decide a zone? *(scoring.py)*
- Why keep measurement and decision separate? *(auditable, testable, model can't force a false-safe)*
