# TerraSight — Complete Learning Notes

Everything you need to understand this project **from zero to deep** — the problem,
every layer of the architecture, the math behind the computer-vision, the
system-design decisions we made (and the alternatives we rejected and why), plus
question banks for **hackathon judges** and **technical interviews**.

You should be able to read only this folder and understand the entire project.

---

## How to use this

Read in order the first time. After that, jump to any file.

| # | File | What it covers | Depth |
|---|------|----------------|-------|
| 00 | `README.md` | This index + the 60-second story | — |
| 01 | `01-overview.md` | The problem, the mission, the whole pipeline in plain English | ⭐⭐ |
| 02 | `02-cv-foundations.md` | From-0 primer: pixels, images, matrices, cameras, stereo, depth, coordinate frames, confidence | ⭐⭐⭐ |
| 03 | `03-segmentation.md` | "What is this pixel?" — semantic segmentation | ⭐⭐⭐ |
| 04 | `04-stereo-depth.md` | "How far / how steep?" — stereo depth, slope, roughness | ⭐⭐⭐ |
| 05 | `05-slam-fusion.md` | "Where is the rover, and one map from many frames" — SLAM | ⭐⭐⭐ |
| 06 | `06-terrain-analysis.md` | Per-cell descriptors, crater-distance, boundary tracing | ⭐⭐ |
| 07 | `07-safety-scoring.md` | **The heart**: deterministic Safety Score + Zones + no-false-safe | ⭐⭐⭐⭐ |
| 08 | `08-backend-api-data.md` | FastAPI, the frozen contract, Supabase, mock fallback, persistence | ⭐⭐⭐ |
| 09 | `09-edge-quantization.md` | Running on a rover: latency budgets, INT8 quantization | ⭐⭐ |
| 10 | `10-frontend.md` | Next.js dashboard + Three.js 3D world + data flow | ⭐⭐ |
| 11 | `11-devops-deploy.md` | Docker, Vercel `services`, CI/CD, and the real bugs we hit | ⭐⭐ |
| 12 | `12-design-decisions.md` | **Every big decision, why, the alternative, what we gained/gave up** | ⭐⭐⭐⭐ |
| 13 | `13-questions-hackathon.md` | What judges ask + exactly how to answer (incl. the honest framing) | ⭐⭐⭐ |
| 14 | `14-questions-interview.md` | Technical interview Q&A with model answers | ⭐⭐⭐ |
| 15 | `15-glossary.md` | Every term, defined from 0 + a one-page cheat-sheet | ⭐⭐ |

**If you only have 1 hour before judging:** read `01`, `07`, `12`, `13`, and the cheat-sheet in `15`.

---

## The 60-second story (memorize this)

> A planetary rover is ~3–22 light-minutes from Earth. It **cannot** ask Earth
> "is this ground safe to build on?" and wait 40 minutes for an answer. TerraSight
> is the **onboard eyes + brain**: it takes the rover's camera feed, figures out
> *what* each patch of ground is and *how steep/rough* it is, then labels the world
> into four **decision zones** and scores each patch for construction — **all on
> the rover, in real time, with a hard guarantee it will never call dangerous
> ground "safe."**

Four zones: **0 = safe to build**, **1 = drivable but not buildable**, **2 =
scientifically interesting (protect it)**, **3 = hazard (avoid)**.

The one sentence that wins arguments: **"Uncertainty degrades toward caution —
the system can be wrong by refusing good ground, but it is architecturally
prevented from ever approving bad ground."**

---

## The honest framing (say this before a judge forces it out of you)

TerraSight today is a **complete, safety-first software system with a real
decision layer**, running its perception stages as **classical algorithms on
simulated data**. There is **no trained neural network yet** — the segmentation,
depth, and SLAM stages are honest classical stand-ins behind **frozen interfaces**,
so dropping in a trained model is a bounded, documented step, not a rewrite.

Why this is a *strength*, not a weakness, and how to say it: see `13-questions-hackathon.md`.

---

## What's real vs simulated (know this cold)

| Layer | Status |
|---|---|
| Safety Score + Zone decision logic | ✅ **Real**, deterministic, tested with range sweeps |
| Trust gates (NaN/stale/off-grid) | ✅ Real |
| API + frozen contract + mock/Supabase fallback | ✅ Real, deployed, live-verified |
| Terrain assembly (crater-dist, boundary tracing) | ✅ Real algorithm, on synthetic grid |
| INT8 quantization of the classifier | ✅ Real |
| Frontend dashboard + 3D view | ✅ Real, deployed |
| Segmentation | 🟡 Classical (colour-centroid), **not a neural net** |
| Stereo depth | 🟡 Real SGBM code path exists, but **untested on real images** (no OpenCV/images wired) |
| SLAM | 🟡 Classical numpy registration on synthetic frames |
| Datasets | 🟡 Synthetic placeholders; no real Mars/lunar imagery processed yet |

Live demo: **https://terrasight-liard.vercel.app**
