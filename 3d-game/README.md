# 3d-game — a reusable engine ecosystem

Not "a game engine." A **layered set of libraries** where math sits below
physics, physics below the engine, and the engine below the games — and where
**the browser client and the Node server share the same simulation code**
(TypeScript compiles to both, no bindings).

> The goal: every new game should need *less* engine code than the last. That's
> the proof the abstraction is real.

## Dependency graph

```
                games/*  (validation projects)
                   │
             gameplay framework
                   │
        ┌──────────┼──────────┐
     apps/client            apps/server
     (WebGL, input,         (authoritative sim,
      prediction)            networking, persistence)
        └──────────┼──────────┘
                   │
            packages/engine   (ECS · scene · events · serialization)
                   │
        ┌──────────┼──────────┐
   packages/physics      packages/net
   (collision, rigid-      (protocol, replication,
    body, solver)           prediction, snapshots)
        └──────────┼──────────┘
                   │
            packages/math   ← the bottom rung (built)
       (Vec3 · Mat4 · Quaternion · geometry · noise)
```

## Layout (grows as filled — no empty scaffolding)

```
packages/   shared code, runs on client AND server
  math/       ✅ Vec3 · Mat4 · Quaternion · Transform · geometry+intersections (61 tests)
  physics/    🟡 RigidBody · World · broadphase · contacts (sphere-sphere/AABB) · impulse solver. Next: friction + angular contacts
  engine/     ⬜ ECS · scene graph · events · serialization
  net/        ⬜ serialization · replication · prediction · reconciliation
apps/
  client/     🟡 Cinematic WebGL2 engine (Vite) — PBR · PCF shadow maps · HDR+bloom · ACES tonemap, live physics sandbox
  server/     🟡 Offline path tracer — GI · soft shadows · metals · depth of field → PNG (reuses @engine/math). Next: authoritative sim
games/        ⬜ sandbox → racing → FPS → RTS → open world
```

## Roadmap (start small, each step is usable on its own)

`Vec3 → Mat4 → Quaternion → Transform → geometry/intersections`
` → RigidBody → collision (broad/narrow/solver) → ECS → renderer`
` → networking → deterministic sim → authoritative server → games`

Highest-value order for systems depth:
**Math → Physics → ECS → memory/pooling → job system → renderer →
networking → deterministic sim → multiplayer server → asset pipeline → editor.**

Full design notes and the long-form vision live in `docs/vision.md`.

## Run

```bash
pnpm install     # once: links workspace packages + installs tsc / @types/node
pnpm check       # typecheck + tests (CI gate)
pnpm test        # tests only
pnpm typecheck   # types only
```

## Garuda devotional render

The offline renderer includes a procedural white-and-gold Garuda with layered
wings, jewelry, a devotional flight pose, and a removable Vishnu rider. It uses
the engine's triangle mesh and BVH path rather than an imported image or model.

```bash
# Fast composition preview
pnpm --filter server render 640 360 16 5 garuda-preview.png --scene garuda

# Final Full HD frontend asset
pnpm --filter server render 1920 1080 12 5 ../client/public/garuda.png --scene garuda

# Open /?mode=viewer for Garuda; / remains the physics sandbox
pnpm --filter client dev
```

`buildGaruda()` includes Vishnu for the reference-inspired hero scene. Pass
`{ includeVishnu: false }` to reuse Garuda alone in another composition.

Node ≥ 22 runs the `.ts` sources directly via type-stripping — **no build
step**. Packages import each other's source (`@engine/math` → its `src`), and
`tsc` runs as a pure checker (`noEmit`), never a compiler. When a package is
eventually published to npm, add a build step then — not before.
```
