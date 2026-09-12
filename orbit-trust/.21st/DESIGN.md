# ORBIT-TRUST design context

## Product

ORBIT-TRUST is a compact mission-operations decision-support console. It helps an analyst prioritize conjunction cases, audit evidence, compare supplied fleet responses and inspect a separate reentry-exposure scenario.

## Direction

- Dark `#101827` navigation with a light `#F3F5F7` workspace and white panels.
- Blue `#1D4ED8` for primary action. Red and amber identify urgency or missing evidence. Green means a completed software check only.
- System sans-serif typography, 8px spacing rhythm, 8px panels, 6px controls and minimal elevation.
- Dense semantic tables on desktop; contained horizontal table scrolling on small screens.
- The central visual explains evidence or a pair comparison. 3D supports the decision and never becomes a decorative full-screen globe.

## Required interaction behavior

- Keep urgency and evidence quality visibly separate.
- Express every status with text or an icon as well as color.
- Show synthetic-data and model-boundary labels persistently.
- Preserve loading, empty, error, stale and partial-data seams as the backend is connected.
- Maintain keyboard focus, semantic controls, reduced motion and a usable 390px layout.

## Engine integration

The visual adapter consumes `@engine/math` from the preserved `3d-game` project and adapts its procedural sphere mesh. Game physics remains a separate domain and cannot produce operational orbital claims. See `docs/SOURCE_REUSE.md`.

## Avoid

Animated starfields, glass effects, excessive cards, unlabelled risk colors, fake confidence percentages, safety guarantees, predicted crash locations and operational maneuver claims.

