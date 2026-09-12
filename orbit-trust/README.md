# ORBIT-TRUST

Evidence-first satellite conjunction review. The repository includes a Next.js mission workspace, the independent GARUDA/game engine, and the Rust/Python backend with Supabase migrations and a bounded ADK/Groq investigator.

## Frontend

From `orbit-trust/apps/web`, run `npm run dev` for local development or `npm run build` for a static export. Dependencies must already be installed from the repository's pnpm lockfile. The public landing page leads to separate app pages under `/app/`: overview, satellites, orbital view, collision review, agents, finance, terrain, activity and methods.

The interface currently uses explicitly marked local demonstration data. Backend services merged from main are preserved but are not silently represented as live connections. GARUDA and the shared ray-tracing engine remain intact in `3d-game/`.

## Backend

From `orbit-trust`, the existing API command is `python -m uvicorn app:app --reload`. The entrypoint exports `orbit_trust.api.app`; health is `/api/v1/health`. Backend code is in `orbit_trust/`, native calculations in `crates/orbit_core/`, fixtures in `data/fixtures/`, and database migrations in `supabase/migrations/`.

`orbit-trust/vercel.json` retains the backend deployment configuration. The frontend is independently deployable from `orbit-trust/apps/web` with access to the sibling engine source. Do not repurpose the GARUDA Vercel project.

## Documentation

- `docs/BUILD_STATUS.md`: backend and frontend milestone records
- `docs/FRONTEND_EXPERIENCE_V2.md`: prior Earth experience details
- `docs/SETUP.md`: backend credentials and infrastructure setup
- `specification/START_HERE.md`: full implementation handoff

Secrets belong only in ignored environment files or deployment settings, never in the frontend bundle or Git history.
