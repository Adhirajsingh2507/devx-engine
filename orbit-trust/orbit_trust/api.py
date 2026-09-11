"""FastAPI surface (handoff docs 04-05).

Only /health and /capabilities are implemented in M0. Neither requires a
workspace identity and neither exposes secrets. All other endpoints in doc 05
arrive in later milestones. The app is versioned under /api/v1.
"""

from __future__ import annotations

import os

from fastapi import FastAPI

from . import BUILD_ID, __version__, numerics

app = FastAPI(title="ORBIT-TRUST API", version=__version__)


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


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
    return {
        "app_mode": os.environ.get("APP_MODE", "public_synthetic"),
        "policy_version": os.environ.get("POLICY_VERSION", "demo-2.0"),
        "numerical_engine": "python-reference",  # rust/pyo3 core: pending toolchain (M0)
        "rust_core_available": False,
        "supported_encounter_model": "short_linear_gaussian_independent",
        "groq_enabled": groq_enabled,
        "groq_model": os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b") if groq_enabled else None,
        "generation_mode": "groq" if groq_enabled else "template_fallback",
        "smoke": numerics.smoke(),
    }
