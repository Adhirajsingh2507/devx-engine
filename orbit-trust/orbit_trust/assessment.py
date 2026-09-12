"""Deterministic assessment engine (handoff docs 05/06).

Combines the supported recomputation, the reported provider value, evidence
findings and the review policy into an immutable Assessment. Evidence quality is
audited separately from urgency: a low recomputed Pc never erases a review that
missing/stale/inconsistent evidence requires. All facts here are host-owned; the
LLM never sets a number, finding or urgency.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

from . import numerics, policy
from .models import parse_utc

STALE_S = 21_600          # 6h demo default (doc 06)
FUTURE_TOL_S = 5          # declared demo allowance (doc 06)

# evidence_state precedence (doc 05): unsupported applicability, then material
# inconsistency, then missing required data, otherwise usable. RISK_THRESHOLD_
# EXCEEDED is a *concern*, not an evidence gap, so it never degrades the state.
_UNSUPPORTED_CODES = {"INVALID_COVARIANCE", "UNSUPPORTED_ENCOUNTER", "MISSING_FRAME_EPOCH"}
_INCONSISTENT_CODES = {"FUTURE_EVIDENCE_TIME", "SOURCE_REVISION_CONFLICT", "SCENARIO_CLASSIFICATION_CONFLICT"}
_MISSING_CODES = {"STALE_SOLUTION", "STALE_OBSERVATION", "MISSING_OBSERVATION_METADATA",
                  "COVARIANCE_REALISM_UNVERIFIED", "MANEUVER_CONTEXT_UNKNOWN"}


@dataclass
class Finding:
    code: str
    material: bool
    detail: str
    source_ref: str


@dataclass
class Assessment:
    reported_pc: Optional[float]
    recomputed_pc: Optional[float]
    method_status: str
    evidence_state: str
    material_concern: bool
    review_required: bool
    proposed_urgency: str
    deadline: Optional[str]
    findings: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["findings"] = [asdict(f) if not isinstance(f, dict) else f for f in self.findings]
        return d


def _stale_findings(role: str, em: dict, now: datetime) -> list[Finding]:
    out: list[Finding] = []
    sol = em.get(f"{role}_solution_epoch")
    obs = em.get(f"{role}_last_observation_at")
    ref = f"/evidence_metadata/{role}_solution_epoch"
    if sol is None:
        out.append(Finding("MISSING_OBSERVATION_METADATA", True, f"{role} solution epoch missing", ref))
    else:
        t = parse_utc(sol)
        if (t - now).total_seconds() > FUTURE_TOL_S:
            out.append(Finding("FUTURE_EVIDENCE_TIME", True, f"{role} solution epoch in the future", ref))
        elif (now - t).total_seconds() > STALE_S:
            out.append(Finding("STALE_SOLUTION", True, f"{role} solution older than {STALE_S}s", ref))
    ref_o = f"/evidence_metadata/{role}_last_observation_at"
    if obs is None:
        out.append(Finding("MISSING_OBSERVATION_METADATA", True, f"{role} last observation missing", ref_o))
    else:
        t = parse_utc(obs)
        if (t - now).total_seconds() > FUTURE_TOL_S:
            out.append(Finding("FUTURE_EVIDENCE_TIME", True, f"{role} observation in the future", ref_o))
        elif (now - t).total_seconds() > STALE_S:
            out.append(Finding("STALE_OBSERVATION", True, f"{role} observation older than {STALE_S}s", ref_o))
    return out


def assess(report: dict, *, now: datetime, mode: str = "public_synthetic", threshold: float = policy.REVIEW_THRESHOLD) -> Assessment:
    findings: list[Finding] = []

    # 1. recomputation
    enc = report.get("encounter")
    recomputed = None
    if enc is None:
        method_status = "unsupported"
        findings.append(Finding("MISSING_FRAME_EPOCH", True, "no encounter supplied", "/encounter"))
    else:
        ev = numerics.evaluate_encounter(enc)
        method_status = ev["status"]
        if ev["status"] == "supported":
            recomputed = ev["pc"]
        else:
            reason = ev.get("reason", "")
            code = "INVALID_COVARIANCE" if "covariance" in reason else "UNSUPPORTED_ENCOUNTER"
            findings.append(Finding(code, True, reason or ev["status"], "/encounter"))

    # 2. risk threshold on the applicable value (reported or supported recomputation)
    reported = report.get("reported_pc")
    candidates = [p for p in (recomputed, reported) if p is not None]
    risk_pc = max(candidates) if candidates else None
    if risk_pc is not None and risk_pc >= threshold:
        findings.append(Finding("RISK_THRESHOLD_EXCEEDED", True, f"pc {risk_pc:g} >= {threshold:g}", "/reported_pc"))

    # 3. evidence metadata audit
    em = report["evidence_metadata"]
    findings += _stale_findings("primary", em, now)
    findings += _stale_findings("secondary", em, now)
    basis = em["covariance_realism_basis"]
    if basis == "unverified" or (basis == "synthetic_assumption" and mode != "public_synthetic"):
        findings.append(Finding("COVARIANCE_REALISM_UNVERIFIED", True, f"covariance basis {basis}", "/evidence_metadata/covariance_realism_basis"))
    if em["maneuver_information_status"] == "unknown":
        findings.append(Finding("MANEUVER_CONTEXT_UNKNOWN", True, "maneuver information unknown", "/evidence_metadata/maneuver_information_status"))

    # 4. deadline (timing only, not a concern by itself)
    planning = report["planning"]
    deadline = None
    if planning["latest_command_at"] and planning["review_allowance_s"] is not None:
        deadline = policy.review_deadline(planning["latest_command_at"], planning["review_allowance_s"])
    else:
        findings.append(Finding("DEADLINE_UNKNOWN", False, "no command opportunity/allowance", "/planning"))

    # 5. summaries
    material = [f for f in findings if f.material]
    material_concern = any(f.code == "RISK_THRESHOLD_EXCEEDED" for f in findings)
    review_required = bool(material)  # risk OR any material evidence gap requires review

    if any(f.code in _UNSUPPORTED_CODES for f in findings):
        evidence_state = "unsupported"
    elif any(f.code in _INCONSISTENT_CODES for f in findings):
        evidence_state = "inconsistent"
    elif any(f.code in _MISSING_CODES for f in findings):
        evidence_state = "incomplete"
    else:
        evidence_state = "usable"

    proposed = policy.proposed_urgency(now, deadline, review_required)

    return Assessment(
        reported_pc=reported,
        recomputed_pc=recomputed,
        method_status=method_status,
        evidence_state=evidence_state,
        material_concern=material_concern,
        review_required=review_required,
        proposed_urgency=proposed,
        deadline=deadline.strftime("%Y-%m-%dT%H:%M:%SZ") if deadline else None,
        findings=findings,
    )


def reopen_on_new_evidence(current_state: str, *, new_material: bool) -> tuple[str, bool]:
    """New material evidence reopens a monitored/closed case as reviewing and
    requires latest-version acknowledgement; a duplicate or cosmetic change does
    not (docs 05/06). Returns (new_state, acknowledgement_required)."""
    if current_state in ("monitoring", "closed") and new_material:
        return "reviewing", True
    return current_state, False
