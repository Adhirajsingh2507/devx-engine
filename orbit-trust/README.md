# ORBIT-TRUST

ORBIT-TRUST is the planned satellite conjunction-warning reliability, evidence-audit and fleet-response decision-support application. The complete, implementation-ready handoff is in [`specification/START_HERE.md`](specification/START_HERE.md).

The current contents are specifications and reference fixtures. The application has not yet been implemented. Start with `specification/00_BOOTSTRAP_PROMPT.md`, then follow the milestones in `specification/13_IMPLEMENTATION_MILESTONES.md`.

## Repository boundary

Build ORBIT-TRUST inside this `orbit-trust/` directory. The existing `3d-game/` application is an important future implementation asset. Preserve its source, assets, dependencies, configuration, history and deployment. Do not delete, overwrite, rename, move or repurpose it while implementing ORBIT-TRUST.

If the connected Vercel project currently deploys `3d-game/`, preserve that deployment and establish the intended ORBIT-TRUST deployment target before changing project settings.
