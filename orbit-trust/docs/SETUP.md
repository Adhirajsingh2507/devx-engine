# ORBIT-TRUST — credential setup guide

Step-by-step to provision the cloud accounts that unblock the remaining
milestones (N2 storage/auth → N3 agent → N5 deploy). Do **Part A (Supabase)
first** — it unblocks the most. Each part ends with a "ping" line so the
implementer can take over.

## Ground rules for secrets (read once)
- **Never paste the `service_role` key, Groq key, or DB password into chat** —
  it would land in the transcript. Put them in **`orbit-trust/.env`**, which is
  gitignored. It is read locally and used **without printing the values**.
- Create it once: `cp orbit-trust/.env.example orbit-trust/.env`, then fill in.
- For interactive logins, run them yourself with the `!` prefix in the Claude
  Code prompt (e.g. `! supabase login`) so the output returns to the session.

---

## Part A — Supabase (unblocks N2: storage, auth, isolation)

**A1. Create the project** — <https://supabase.com> → **New project**. Choose a
region, set a strong **database password** (save it), wait ~2 min.

**A2. Copy 5 values into `orbit-trust/.env`:**

| Supabase dashboard location | `.env` key |
| --- | --- |
| Settings → API → **Project URL** | `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL` (same value) |
| Settings → API → **anon / publishable** key | `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` |
| Settings → API → **service_role** key (secret) | `SUPABASE_SERVICE_ROLE_KEY` |
| Settings → Database → **Connection string → URI** (direct, port 5432) | add a line `SUPABASE_DB_URL=` with it |

`SUPABASE_DB_URL` is used to apply the migrations; it embeds the DB password, so
keeping it in the gitignored `.env` is correct.

**A3. Enable auth** (Authentication → Providers):
- Toggle **Anonymous** sign-ins ON (the "Try demo" path).
- **GitHub** OAuth (optional now; needed for persistent accounts): create a
  GitHub OAuth app (github.com → Settings → Developer settings → OAuth Apps →
  New), set its **Authorization callback URL** to the exact URL Supabase shows in
  the GitHub provider panel, paste GitHub's Client ID + Secret into Supabase.
  Anonymous alone is enough to prove N2 first.

**A4. Ping:** say **"Supabase ready"**.
**Then the implementer:** installs the Supabase CLI (or uses `psql` with
`SUPABASE_DB_URL`), applies migrations `0001`→`0004`, finishes the lease RPC
bodies, seeds the demo data, and runs the doc-19 isolation tests (two accounts,
forged actor, guessed UUID, expired JWT).

---

## Part B — Groq (unblocks N3: the bounded agent)

**B1.** <https://console.groq.com> → **API Keys** → **Create API Key**. Copy it.

**B2.** In `orbit-trust/.env` set:
```
GROQ_API_KEY=<the key>
GROQ_ENABLED=true
GROQ_MODEL=openai/gpt-oss-20b
ADK_LITELLM_MODEL=groq/openai/gpt-oss-20b
```

**B3.** Confirm **`openai/gpt-oss-20b`** is available for your account (Groq
console → Models / Rate limits). If not, share the model name that is.

**B4. Ping:** **"Groq ready"**.
**Then the implementer:** runs the ADK↔Groq tool-call spike, builds the bounded
Investigator + host validator + deterministic fallback, freezes the 50-item eval
set, and captures one real trace (T34–T37).

---

## Part C — Vercel (unblocks N5: public URL) — do last

**C1. Create a NEW project** — vercel.com → **Add New → Project** → import the
**`devx-engine`** repo. **Do not reuse or edit the existing `3d-game` project.**

**C2. Project settings before first deploy:**
- **Root Directory** = `orbit-trust`
- **Framework Preset** = leave as detected (verify it is the FastAPI + static
  composition, not "Next.js" — confirmed in the M0 deploy check).
- **Production branch** = `main` (or `orbit-trust` for a preview first).

**C3. Environment variables** (Settings → Environment Variables): the same values
as `.env`, plus `APP_PUBLIC_ORIGIN=<vercel url>` and `APP_MODE=public_synthetic`.
Keep `SUPABASE_SERVICE_ROLE_KEY` and `GROQ_API_KEY` secret / server-only.

**C4. Ping:** **"Vercel project made"** (paste the project URL — not a secret).
**Then the implementer:** verifies route precedence + wheel import in the
deployed function, deploys a preview, smoke-tests from a fresh browser, and
confirms the `3d-game` deployment is untouched.

---

## Minimum to get moving
The single highest-leverage step: **A1–A2 + A4**. That alone lets the database
layer be applied and multi-tenant isolation proven. Groq and Vercel can follow.

## Checklist
- [ ] A1 Supabase project created
- [ ] A2 5 values in `orbit-trust/.env` (incl. `SUPABASE_DB_URL`)
- [ ] A3 Anonymous sign-ins enabled (GitHub OAuth optional)
- [ ] A4 pinged "Supabase ready"
- [ ] B1–B3 Groq key in `.env`, `GROQ_ENABLED=true`, model confirmed
- [ ] B4 pinged "Groq ready"
- [ ] C1–C3 new Vercel project, Root Directory `orbit-trust`, env vars set
- [ ] C4 pinged "Vercel project made" + URL
