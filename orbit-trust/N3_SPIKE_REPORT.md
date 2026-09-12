# N3 Spike Report — Bounded ADK ↔ Groq Investigator

Phase N3 (doc 09): a real Google ADK two-stage agent wired behind
`agent.investigate()`, backed by Groq via LiteLLM, with the deterministic
selection preserved unchanged as the safety net. The host owns every number,
finding and template; the model only *selects and orders* from facts that
already exist, and every proposal is host-validated before it is accepted.

## Environment

| Item | Value |
| --- | --- |
| Python | 3.12.14 (uv-managed `.venv312`, per handoff target — not system 3.13) |
| google-adk | 2.9.0 |
| litellm | 1.100.1 (past the compromised 1.82.7 / 1.82.8) |
| groq | 1.7.0 |
| pydantic | 2.13.5 |
| Model | `openai/gpt-oss-20b` via `groq/openai/gpt-oss-20b` (LiteLLM) |

Pins are in `requirements.txt`. No stray `svg` dependency was added (the
proposal's suggestion had no import proving it necessary).

## What was built

| File | Role |
| --- | --- |
| `orbit_trust/investigator.py` | Real ADK workflow: **Investigator** `LlmAgent` (3 allowlisted read-only tools, ID-only args, 4 KiB result cap, bounded tool loop) → tool-free **PacketFormatter** `LlmAgent` (emits one `AgentSelection` JSON) → host validation + trace capture. |
| `orbit_trust/quota.py` | In-memory run/token quotas: global concurrency, per-user daily run cap, global daily token cap, per-run token cap, reserve-then-reconcile. |
| `orbit_trust/sanitize.py` | Injection-marker detection (flag, never obey), contact masking (email/phone), hard text truncation before any text reaches the model. |
| `orbit_trust/agent.py` | `investigate()` now tries live Groq → host-validates → falls back deterministically with a labeled `fallback_reason`. **All deterministic functions unchanged in behavior.** |
| `tests/reference/test_agent_integration.py` | T34–T37, dual-mode (LIVE_GROQ / DETERMINISTIC_FALLBACK), writes `n3_test_results.json` + captures a genuine live trace. |

### Trust boundary (why this is safe)

The model never sets a value. The Investigator can call only three read-only
tools that expose the host's own assessment snapshot. The Formatter's JSON is
validated on the host (`investigator._validate`):

- schema-strict via `models.AgentSelection` (types, enums, **no extra fields**);
- every cited finding/fact id must exist in the snapshot;
- the `summary_template_code` **must equal** the template the host facts support
  (`agent._summary_code`) — the model cannot re-narrate the outcome;
- the `request_template_code` must be applicable to the present findings;
- all **material** findings must be included.

Any violation → `LiveUnavailable` → deterministic fallback. The authoritative
summary text is rendered from a host template code in **every** mode.

## Bounds & quotas enforced (doc 09)

- **Allowlisted tools:** exactly `get_assessment_summary`, `list_findings`,
  `get_finding` — read-only, ID-only args, 4 KiB result cap. A non-allowlisted
  call is rejected host-side (`forbidden_tool:*`); structurally there is no
  fetch/network tool to exfiltrate through.
- **Tool loop:** ≤ 3 tool rounds; final answer always captured.
- **Wall time:** 30 s hard budget (daemon-thread join); 20 s per provider call.
- **Retry:** one shared retry on transient failures (429 / timeout / provider
  error) with a 3 s backoff, then fallback.
- **Quotas:** concurrency, per-user/day, global tokens/day, per-run token cap;
  reserve at estimate, reconcile to actual usage. Over-limit → labeled fallback,
  never a hard error.
- **Stale rejection:** `service.investigate_case` already rejects a non-latest
  `assessment_id` (409) before the agent runs.

## Failure handling → labeled deterministic fallback

`groq_disabled_or_no_key`, `timeout`, `rate_limited`, `provider_error:*`,
`malformed:*` (no/blank JSON, schema violation), `invalid:*` (invented/omitted/
mis-templated selection), `quota:*` — each returns
`generation_mode: "template_fallback"` with a matching `fallback_reason`.

## Test results

`python tests/reference/test_agent_integration.py` — **12 / 12 PASS.**

| Case | Mode (key present) | Checks |
| --- | --- | --- |
| T34 investigate host-owned | LIVE_GROQ | live packet host-validated; summary host-supported; trace has real tool calls + tokens |
| T35 invented finding | DETERMINISTIC | host rejects `cited_unknown_finding` |
| T35 omitted required | DETERMINISTIC | host rejects `required_finding_omitted` |
| T35 wrong template | DETERMINISTIC | host rejects `summary_template_not_supported_by_facts` |
| T35 schema extra field | DETERMINISTIC | pydantic rejects additional property |
| T35 forbidden tool | DETERMINISTIC | allowlist is exactly the 3 read-only tools |
| T36 injection is data | LIVE_GROQ | injection flagged, no exfil tool exists, host summary unchanged |
| T37 timeout / 429 / malformed / quota / disabled | DETERMINISTIC | each → labeled fallback with matching reason |

Without a key (`N3_OFFLINE=1`): the same 12 cases pass, T34/T36 as
DETERMINISTIC_FALLBACK — full fallback/validation coverage with no network.

**Regression (requirement 12):** `pytest tests/` — **52 / 52 PASS**
(48 pre-existing + 4 new integration functions). Zero regressions; no
deterministic behavior changed.

## Captured live Groq run (genuine — `docs/n3_live_trace.json`)

Case `asmt-sigma-200` (recomputed Pc ≈ 1.1e-3 ≥ 1e-4 threshold):

| Field | Value |
| --- | --- |
| Model | `groq/openai/gpt-oss-20b` |
| Generation mode | `groq` (host-validated, accepted) |
| Tool calls | `get_assessment_summary()`, `list_findings()`, `get_finding(code="RISK_THRESHOLD_EXCEEDED")` |
| Source ids | `RISK_THRESHOLD_EXCEEDED` |
| Stage latency | Investigator ≈ 4.07 s, Formatter ≈ 1.02 s (≈ 5.1 s total) |
| Provider calls | 5 |
| Token usage | 3071 total |
| Retries | 0 |
| Host validation | **accepted**; summary `REVIEW_DUE_TO_RISK` matches host facts |
| Investigator note | *"…P1 urgency because the recomputed probability of close approach (PC ≈ 0.0011) exceeds the critical threshold of 0.0001, as indicated by the material finding RISK_THRESHOLD_EXCEEDED…"* |

No trace was fabricated. Under Groq free-tier rate limits, back-to-back full
runs occasionally 429 and honestly report `provider_error:RateLimitError` →
deterministic fallback; a spaced run captures the trace above.

## Known limitations

- **gpt-oss + Groq quirk:** the model returns `reasoning_content`, which Groq
  rejects when ADK echoes the assistant turn back on a tool call. Fixed by
  `reasoning_format="hidden"` on the ADK `LiteLlm` model. Documented in code.
- **Quotas are in-memory** (single process), per the N3 in-memory seam. DB
  reservations (durable across workers/restarts) land with N2.
- **Wall-time timeout** abandons a hung provider call on a daemon thread; the
  reservation still accounts for it. Fine for the demo; revisit with async runner.
- **Free-tier rate limits** make rapid repeated live runs flaky; space them out
  or use a paid key for the demo recording.
- ADK's sync `Runner.run` is deprecated (works, emits a warning); migrate to
  `run_async` when convenient.

## Activating the live path

```bash
# .env (already set for this spike):
GROQ_ENABLED=true
GROQ_API_KEY=gsk_...
ADK_LITELLM_MODEL=groq/openai/gpt-oss-20b
# run:
.venv312/bin/python tests/reference/test_agent_integration.py   # live when key present
N3_OFFLINE=1 .venv312/bin/python tests/reference/test_agent_integration.py   # forced fallback
```

Supabase persistence is **out of scope for N3** (in-memory seam retained).
