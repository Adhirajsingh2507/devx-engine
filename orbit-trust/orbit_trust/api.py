"""FastAPI surface (handoff docs 04-05). Versioned under /api/v1.

Liveness/capabilities need no identity. The compute endpoints
(fleet/economics/reentry/comms/assess) are stateless deterministic cores over an
inline bundle. The workspace-scoped core loop (workspaces/imports/cases/...)
persists through the service layer.

Identity is a DEMO identity for now: the `X-Demo-User` header is the caller and
`X-Workspace-Id` selects the workspace (a workspace id is not authorization —
membership is checked). Real Supabase Auth (GitHub OAuth + JWT/JWKS, doc 19)
replaces `_identity()` later without changing the endpoints.
"""

from __future__ import annotations

import os
from typing import Annotated, Optional

from fastapi import Body, FastAPI, Header, Path, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, conlist

from . import BUILD_ID, __version__, comms, economics, fleet, numerics, reentry, service
from .hashing import canonical_digest
from .models import CandidateSet, CommunicationScenario, EconomicScenario, ReentryScenario, Report, parse_utc
from .service import WorkspaceError

_DEMO_CLOCK = service.DEMO_CLOCK

app = FastAPI(title="ORBIT-TRUST API", version=__version__)


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _rust_core_available() -> bool:
    try:
        import orbit_core  # noqa: F401  (compiled PyO3 extension)

        return True
    except Exception:
        return False


# --- error shape (doc 05): {code, message, request_id, retryable, field_errors} ---

def _error_body(code: str, message: str, retryable: bool, field_errors: list, extra: dict) -> dict:
    from .store import new_id
    return {"code": code, "message": message, "request_id": new_id("req"),
            "retryable": retryable, "field_errors": field_errors, **extra}


@app.exception_handler(WorkspaceError)
async def _workspace_error_handler(_request, exc: WorkspaceError):
    return JSONResponse(status_code=exc.status,
                        content=_error_body(exc.code, exc.message, exc.retryable, exc.field_errors, exc.extra))


@app.exception_handler(RequestValidationError)
async def _validation_handler(_request, exc: RequestValidationError):
    # Structural JSON/schema errors are 422 (doc 05); keep the per-field detail.
    field_errors = [{"field": ".".join(str(p) for p in e.get("loc", [])), "error": e.get("msg", "")}
                    for e in exc.errors()]
    return JSONResponse(status_code=422,
                        content=_error_body("schema_invalid", "request failed schema validation", False, field_errors, {}))


# --- demo identity / workspace resolution ----------------------------------

def _identity(x_demo_user: Optional[str]) -> str:
    if not x_demo_user or not x_demo_user.strip():
        # fail closed (doc 19): no identity, no workspace-scoped access.
        raise WorkspaceError("unauthorized", "X-Demo-User identity required", 401)
    return x_demo_user.strip()


def _ws(x_demo_user: Optional[str], x_workspace_id: Optional[str]):
    owner = _identity(x_demo_user)
    if not x_workspace_id:
        raise WorkspaceError("bad_request", "X-Workspace-Id header required", 400)
    return owner, service.resolve_workspace(owner, x_workspace_id.strip())


DemoUser = Annotated[Optional[str], Header(alias="X-Demo-User")]
WorkspaceId = Annotated[Optional[str], Header(alias="X-Workspace-Id")]
IdemKey = Annotated[Optional[str], Header(alias="Idempotency-Key")]


# --- liveness / capabilities ------------------------------------------------

@app.get("/api/v1/health")
def health() -> dict:
    """Liveness and build ID. No secrets, no external calls (doc 05)."""
    return {"status": "ok", "build_id": BUILD_ID, "version": __version__}


@app.get("/api/v1/capabilities")
def capabilities() -> dict:
    """Engine/model configuration and supported modes. No credentials (doc 05)."""
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


# --- workspace core loop (doc 05) ------------------------------------------

class DemoWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: str = "public_synthetic"
    seed_id: Optional[str] = None


class ImportEnvelope(BaseModel):
    """Outer envelope only. Per-record validation happens in the service so one
    malformed record does not discard the whole import summary (doc 05)."""
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(pattern=r"^2\.0$")
    expected_workspace_revision: int = Field(ge=0)
    records: conlist(dict, min_length=1, max_length=500)


class AssessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    policy_id: Optional[str] = None


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str
    rationale: Optional[str] = None
    assessment_id: Optional[str] = None


class InvestigateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assessment_id: Optional[str] = None


class ResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)


@app.post("/api/v1/workspaces/demo")
def create_demo_workspace(body: DemoWorkspaceRequest, x_demo_user: DemoUser = None, idempotency_key: IdemKey = None) -> dict:
    owner = _identity(x_demo_user)
    digest = canonical_digest({"path": "/workspaces/demo", "body": body.model_dump()})
    return service.create_demo_workspace(owner, body.mode, idempotency_key, digest)


@app.post("/api/v1/imports")
def imports(body: ImportEnvelope, x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None, idempotency_key: IdemKey = None) -> dict:
    owner, ws = _ws(x_demo_user, x_workspace_id)
    digest = canonical_digest({"path": "/imports", "body": body.model_dump()})
    return service.import_batch(ws, owner, list(body.records), body.expected_workspace_revision, idempotency_key, digest)


@app.get("/api/v1/cases")
def list_cases(x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None,
               cursor: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=100)) -> dict:
    _, ws = _ws(x_demo_user, x_workspace_id)
    return service.list_cases(ws, cursor, limit)


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str = Path(...), x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None) -> dict:
    _, ws = _ws(x_demo_user, x_workspace_id)
    return service.get_case(ws, case_id)


@app.get("/api/v1/cases/{case_id}/reports")
def get_case_reports(case_id: str = Path(...), x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None) -> dict:
    _, ws = _ws(x_demo_user, x_workspace_id)
    return service.get_case_reports(ws, case_id)


@app.post("/api/v1/cases/{case_id}/assess")
def assess_case(body: AssessRequest, case_id: str = Path(...), x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None) -> dict:
    owner, ws = _ws(x_demo_user, x_workspace_id)
    return service.assess_case(ws, owner, case_id, body.expected_revision)


@app.post("/api/v1/cases/{case_id}/actions")
def case_action(body: ActionRequest, case_id: str = Path(...), x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None) -> dict:
    owner, ws = _ws(x_demo_user, x_workspace_id)
    return service.record_action(ws, owner, case_id, body.expected_revision, body.action, body.rationale, body.assessment_id)


@app.post("/api/v1/cases/{case_id}/investigate")
def investigate(body: InvestigateRequest, case_id: str = Path(...), x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None) -> dict:
    _, ws = _ws(x_demo_user, x_workspace_id)
    return service.investigate_case(ws, case_id, body.assessment_id)


@app.post("/api/v1/workspaces/{workspace_id}/reset")
def reset_workspace(workspace_id: str, body: ResetRequest, x_demo_user: DemoUser = None) -> dict:
    owner = _identity(x_demo_user)
    ws = service.resolve_workspace(owner, workspace_id)
    return service.reset_workspace(ws, owner, body.expected_revision)


@app.get("/api/v1/activity")
def activity(x_demo_user: DemoUser = None, x_workspace_id: WorkspaceId = None,
             after_sequence: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)) -> dict:
    _, ws = _ws(x_demo_user, x_workspace_id)
    return service.activity(ws, after_sequence, limit)


# --- stateless compute cores (docs 06/07/08) -------------------------------
# Deterministic computation over an inline bundle; no persistence needed.

@app.post("/api/v1/fleet/compare")
def fleet_compare(candidate_set: CandidateSet) -> dict:
    """Bounded comparison of supplied response candidates (doc 07)."""
    return fleet.compare(candidate_set.model_dump())


@app.post("/api/v1/communications/simulate")
def communications_simulate(scenario: CommunicationScenario) -> dict:
    """Timing feasibility for a supplied communication scenario (doc 07)."""
    return comms.timing_feasibility(scenario.model_dump())


@app.post("/api/v1/economics/evaluate")
def economics_evaluate(scenario: EconomicScenario) -> dict:
    """Conditional expected-loss change (doc 08). Decimal arithmetic."""
    return economics.evaluate(scenario.model_dump())


@app.post("/api/v1/reentry/evaluate")
def reentry_evaluate(scenario: ReentryScenario) -> dict:
    """Exposure and optional conditional damage under a supplied footprint (doc 08)."""
    return reentry.evaluate(scenario.model_dump())


@app.post("/api/v1/assess")
def assess(report: Report, now: str = _DEMO_CLOCK) -> dict:
    """Stateless deterministic assessment for one report at the demo clock
    (docs 05/06). The persisted workflow lives under /cases."""
    from . import assessment
    return assessment.assess(report.model_dump(), now=parse_utc(now)).to_dict()
