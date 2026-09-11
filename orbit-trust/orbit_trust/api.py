"""FastAPI surface (handoff docs 04-05).

Only /health and /capabilities are implemented in M0. Neither requires a
workspace identity and neither exposes secrets. All other endpoints in doc 05
arrive in later milestones. The app is versioned under /api/v1.
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from . import BUILD_ID, __version__, assessment, comms, economics, fleet, numerics, reentry
from .models import CandidateSet, CommunicationScenario, EconomicScenario, ReentryScenario, Report, parse_utc

_DEMO_CLOCK = "2026-09-11T12:20:00Z"  # fixed demo clock (doc 02/22)

app = FastAPI(title="ORBIT-TRUST API", version=__version__)


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _rust_core_available() -> bool:
    try:
        import orbit_core  # noqa: F401  (compiled PyO3 extension)

        return True
    except Exception:
        return False


@app.get("/api/v1/health")
def health() -> dict:
    """Liveness and build ID. No secrets, no external calls (doc 05)."""
    return {"status": "ok", "build_id": BUILD_ID, "version": __version__}


@app.get("/api/v1/capabilities")
def capabilities() -> dict:
    """Engine/model configuration and supported modes. No credentials (doc 05).

    Reports only names and booleans; never secret values. GROQ_ENABLED=false
    yields the labeled deterministic fallback (docs 09/14)."""
    groq_enabled = _env_bool("GROQ_ENABLED", False)
    rust = _rust_core_available()
    return {
        "app_mode": os.environ.get("APP_MODE", "public_synthetic"),
        "policy_version": os.environ.get("POLICY_VERSION", "demo-2.0"),
        "numerical_engine": "rust-orbit-core" if rust else "python-reference",
        "rust_core_available": rust,
        "supported_encounter_model": "short_linear_gaussian_independent",
        "groq_enabled": groq_enabled,
        "groq_model": os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b") if groq_enabled else None,
        "generation_mode": "groq" if groq_enabled else "template_fallback",
        "smoke": numerics.smoke(),
    }


# --- M3 compute-only endpoints ---------------------------------------------
# Deterministic computation over an inline bundle. Workspace identity,
# persistence, DB leases and resumable batching (doc 04) are added when Supabase
# credentials exist; these are the pure cores those endpoints will wrap.


@app.post("/api/v1/fleet/compare")
def fleet_compare(candidate_set: CandidateSet) -> dict:
    """Bounded comparison of supplied response candidates (doc 07). Input is
    validated against the CandidateSet contract (422 on malformed input)."""
    return fleet.compare(candidate_set.model_dump())


@app.post("/api/v1/communications/simulate")
def communications_simulate(scenario: CommunicationScenario) -> dict:
    """Timing feasibility for a supplied communication scenario (doc 07).
    Simulation only; no real transmission."""
    return comms.timing_feasibility(scenario.model_dump())


# --- M4 compute-only endpoints ---------------------------------------------


@app.post("/api/v1/economics/evaluate")
def economics_evaluate(scenario: EconomicScenario) -> dict:
    """Conditional expected-loss change (doc 08). Decimal arithmetic; unknown
    probability/loss or mixed currency -> unavailable, never a fabricated saving."""
    return economics.evaluate(scenario.model_dump())


@app.post("/api/v1/reentry/evaluate")
def reentry_evaluate(scenario: ReentryScenario) -> dict:
    """Exposure and optional conditional damage under a supplied footprint
    (doc 08). Not a predicted crash location; missing value stays unknown."""
    return reentry.evaluate(scenario.model_dump())


@app.post("/api/v1/assess")
def assess(report: Report, now: str = _DEMO_CLOCK) -> dict:
    """Deterministic assessment for one report at the demo clock (docs 05/06):
    recomputed Pc, evidence findings, evidence state, urgency. Compute-only;
    persistence + case workflow arrive with the storage layer (N2)."""
    return assessment.assess(report.model_dump(), now=parse_utc(now)).to_dict()
