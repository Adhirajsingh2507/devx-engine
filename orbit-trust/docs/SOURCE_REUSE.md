# Source reuse record

This implementation keeps `3d-game/` as an independent, important future project. The Earth milestone adds a browser Earth renderer under its client and a packed-BVH export in its server library; GARUDA and the game remain intact. The table below records the initial console milestone; current Earth reuse is documented in [FRONTEND_EXPERIENCE_V2.md](FRONTEND_EXPERIENCE_V2.md).

| Source | Original path | Reused now | Boundary |
| --- | --- | --- | --- |
| devx-engine 3D engine | `3d-game/packages/math` | `Vec3` for the encounter visualization | Visual projection only; operational orbital calculation belongs to the future Rust scientific core. |
| devx-engine 3D engine | `3d-game/apps/client/src/sphere.ts` | Adapted procedural UV sphere mesh in `apps/web/src/engine/uv-sphere.ts` for the Earth visual | The local adapter makes the isolated Vercel root buildable. It is a presentation model, not an Earth gravity or reentry model. |
| devx-engine graphics client | `3d-game/apps/client/src/renderer.ts`, `gl.ts`, `shaders.ts` | Coordinate, rendering, reduced-motion and quality conventions informed the adapter | The full PBR pipeline stays in the game project until the adapter has a measured bundle/performance budget. |
| devx-engine physics | `3d-game/packages/physics` | Contracts and future simulation seam documented in the UI | Rigid-body game physics must not be presented as orbital dynamics. |
| devx-engine server renderer | `3d-game/apps/server` | Backend rendering capability inventoried for later evidence snapshots | It is not included in the Vercel web bundle in this UI milestone. |
| ORBIT-TRUST handoff | `specification/` | Product language, routes, states, fixtures, contracts, colors and accessibility rules | The fixture UI is clearly labelled synthetic and makes no operational claim. |

The owner's latest instruction authorizes integration work. Reuse remains selective because the game physics model and conjunction model have different scientific domains.
