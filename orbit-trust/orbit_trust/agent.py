"""Bounded case-review agent (docs 05/09).

Right now this is the deterministic, labeled *fallback* only — no provider call.
The Groq/ADK Investigator + PacketFormatter (doc 09) slot in behind
`investigate()` later: a model proposes an `AgentSelection`, and the SAME host
validator here decides what is authoritative. The host owns every number,
finding and template; the model may only *select* from facts that already
exist. A malformed / injected / over-reaching proposal is rejected and this
deterministic selection is used instead.
"""

from __future__ import annotations

from typing import Optional

# summary template <- (method_status, evidence_state, material_concern)
_SUMMARY_TEXT = {
    "CALCULATION_UNSUPPORTED": "Recomputation is not applicable to the supplied encounter; review the reported value and evidence.",
    "REVIEW_DUE_TO_CONFLICT": "Sources or evidence times are inconsistent; review required before any disposition.",
    "REVIEW_DUE_TO_MISSING_EVIDENCE": "Required evidence is missing or stale; review required to classify the encounter.",
    "REVIEW_DUE_TO_RISK": "Recomputed/reported collision probability exceeds the review threshold; review required.",
    "MONITOR_SUPPORTED": "Evidence is usable and no review threshold is exceeded; monitor.",
}

# finding code -> the information request that would resolve it (doc 05 codes).
_REQUEST_FOR = {
    "INVALID_COVARIANCE": "REQUEST_STATE_COVARIANCE",
    "MISSING_FRAME_EPOCH": "REQUEST_FRAME_EPOCH",
    "UNSUPPORTED_ENCOUNTER": "REQUEST_FRAME_EPOCH",
    "MANEUVER_CONTEXT_UNKNOWN": "REQUEST_MANEUVER_CONTEXT",
    "DEADLINE_UNKNOWN": "REQUEST_DEADLINE",
}


def _summary_code(assessment: dict) -> str:
    if assessment.get("method_status") == "unsupported":
        return "CALCULATION_UNSUPPORTED"
    state = assessment.get("evidence_state")
    if state == "inconsistent":
        return "REVIEW_DUE_TO_CONFLICT"
    if assessment.get("material_concern"):
        return "REVIEW_DUE_TO_RISK"
    if state == "incomplete":
        return "REVIEW_DUE_TO_MISSING_EVIDENCE"
    return "MONITOR_SUPPORTED"


def _select(assessment: dict) -> dict:
    """Deterministic AgentSelection over the assessment's own findings."""
    findings = assessment.get("findings", [])
    codes = [f["code"] for f in findings]
    summary = _summary_code(assessment)
    request_code = next((_REQUEST_FOR[c] for c in codes if c in _REQUEST_FOR), None)
    # material findings first, then the rest — a stable, explainable order.
    ordered = [f["code"] for f in findings if f.get("material")] + [
        f["code"] for f in findings if not f.get("material")
    ]
    return {
        "assessment_id": assessment.get("assessment_id"),
        "ordered_finding_ids": ordered,
        "selected_fact_ids": codes,
        "summary_template_code": summary,
        "request_template_code": request_code if summary != "MONITOR_SUPPORTED" else None,
        "question_to_analyst_code": None,
    }


def validate_selection(selection: dict, assessment: dict) -> Optional[str]:
    """Host validator (doc 09): every cited finding/fact must exist in the
    snapshot, and the summary must be a known template. Returns None if valid,
    else a short reason. This is what guards a model proposal later."""
    codes = {f["code"] for f in assessment.get("findings", [])}
    if selection.get("summary_template_code") not in _SUMMARY_TEXT:
        return "unknown_summary_template"
    for fid in selection.get("ordered_finding_ids", []):
        if fid not in codes:
            return f"cited_unknown_finding:{fid}"
    for fid in selection.get("selected_fact_ids", []):
        if fid not in codes:
            return f"cited_unknown_fact:{fid}"
    if selection.get("assessment_id") not in (None, assessment.get("assessment_id")):
        return "assessment_id_mismatch"
    return None


def _fallback(assessment: dict, *, reason: Optional[str] = None) -> dict:
    """Deterministic, host-validated review packet — the safety net."""
    selection = _select(assessment)
    val = validate_selection(selection, assessment)
    if val is not None:  # our own deterministic selection should always pass
        raise AssertionError(f"deterministic selection failed validation: {val}")
    packet = {
        "generation_mode": "template_fallback",
        "selection": selection,
        "authoritative_text": _SUMMARY_TEXT[selection["summary_template_code"]],
    }
    if reason is not None:
        packet["fallback_reason"] = reason
    return packet


def investigate(assessment: dict, *, user_id: str = "demo") -> dict:
    """Return a validated, host-owned review packet.

    Attempts the live ADK/Groq investigator first; its proposal is accepted only
    if it passes host validation. On disabled/unavailable Groq, quota, timeout,
    429, tool failure, or any malformed/invalid output, returns the deterministic
    `template_fallback` (with a `fallback_reason`). The host owns the
    authoritative text in every mode.
    """
    from . import investigator  # lazy: keeps ADK/LiteLLM off the deterministic path

    if not investigator.is_enabled():
        return _fallback(assessment, reason="groq_disabled_or_no_key")
    try:
        live = investigator.run_investigation(assessment, user_id=user_id)
    except investigator.LiveUnavailable as e:
        return _fallback(assessment, reason=e.reason)

    selection = live["selection"]
    return {
        "generation_mode": "groq",
        "selection": selection,
        "authoritative_text": _SUMMARY_TEXT[selection["summary_template_code"]],
        "trace": live["trace"],
        "retries": live.get("retries", 0),
    }
