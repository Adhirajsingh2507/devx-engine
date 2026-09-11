# devx — Hackathon Dev Toolkit

One folder with everything needed to work fast at a hackathon: skill sources, reusable skills, MCP servers, and reference projects.

## Layout

- `repos/` — skill/best-practice sources
  - `claude-code-best-practice/` — shanraisshan/claude-code-best-practice
  - `hackathon-skills-marketplace/` — asadullah48/hackathon-skills-marketplace
  - `2d-games/` — agent-skills-hub 2d-games skill (sparse)
  - `agent-skills/`, `skills/`, `ui-ux-pro-max-skill/`, `bencium-claude-code-design-skill/`, `claude-marketplace/` — local skill sources from ~/kaggle
- `skills/` — all 64 installed Claude skills (copied from ~/.claude/skills)
- `sih/` — SIH/TerraSight docs & config (CLAUDE.md, DEPLOY.md, phases.md, docs/, notes/). Code, .git and secrets excluded.
- `kaggle-projects/` — reference docs from prior projects
  - `personal-cfo/` — architecture, cost analysis, hackathon Q&A
  - `vibeforge/` — README, API contract, demo script
- `.mcp.json` — 10 MCP servers: supabase, vercel, github, context7, sentry, playwright, filesystem (scoped to devx), postgres, arxiv, docker

## MCP notes
- `github` needs `${GITHUB_PAT}`, `postgres` needs `${DATABASE_URL}` in your env.
- `filesystem` server is scoped to this devx folder.
- Secrets (.env.local) were intentionally NOT copied from source projects.
