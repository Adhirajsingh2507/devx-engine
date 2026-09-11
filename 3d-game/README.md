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
  physics/    🟡 RigidBody · World (gravity, Euler). Next: broadphase → narrowphase → solver
  engine/     ⬜ ECS · scene graph · events · serialization
  net/        ⬜ serialization · replication · prediction · reconciliation
apps/
  client/     ⬜ renderer · input · audio · prediction
  server/     ⬜ authoritative simulation · matchmaking · persistence
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
node --test --experimental-strip-types packages/*/test/*.test.ts   # or: pnpm test
```

Node ≥ 22 runs the `.ts` sources directly via type-stripping — no build step
needed for tests. `pnpm install` only when a package first takes a real
dependency.
```
