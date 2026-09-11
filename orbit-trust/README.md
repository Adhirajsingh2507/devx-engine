# ORBIT-TRUST

ORBIT-TRUST is the planned satellite conjunction-warning reliability, evidence-audit and fleet-response decision-support application. The complete, implementation-ready handoff is in [`specification/START_HERE.md`](specification/START_HERE.md).

The repository now contains the first production UI foundation alongside the specifications and reference fixtures. Continue implementation from `specification/00_BOOTSTRAP_PROMPT.md` and the milestones in `specification/13_IMPLEMENTATION_MILESTONES.md`.

## UI implementation

The Next.js application in `apps/web` includes the fixed static routes, mission-console design system, synthetic review queue, evidence-first case view, fleet response matrix, satellite registry, reentry exposure sandbox, activity ledger, settings and method boundaries.

```bash
cd orbit-trust
pnpm install
pnpm dev
```

Run `pnpm check` before a release. The static export is written to `apps/web/out`. The encounter visual imports the preserved `3d-game` math package and adapts its procedural sphere model. See [`docs/SOURCE_REUSE.md`](docs/SOURCE_REUSE.md) for the scientific and repository boundaries and [`docs/BUILD_STATUS.md`](docs/BUILD_STATUS.md) for the remaining implementation work.

## Repository boundary

Build ORBIT-TRUST inside this `orbit-trust/` directory. The existing `3d-game/` application is an important future implementation asset. Preserve its source, assets, dependencies, configuration, history and deployment. Do not delete, overwrite, rename, move or repurpose it while implementing ORBIT-TRUST.

If the connected Vercel project currently deploys `3d-game/`, preserve that deployment and establish the intended ORBIT-TRUST deployment target before changing project settings.
