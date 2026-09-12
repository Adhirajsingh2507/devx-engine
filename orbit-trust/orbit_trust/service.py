"""Workspace domain service (docs 05/06/19).

Orchestrates the deterministic cores (validation, ledger, assessment, policy)
over the workspace store to implement the doc-05 core loop: create a demo
workspace, import canonical bundles into a case queue, re-assess, record
review dispositions through the workflow state machine, and run the bounded
investigate fallback. Every number/finding/urgency is host-owned here; the
agent only selects.

The store is in-memory today (see store.py). This module is written so the
Supabase transactional store can replace store.py without touching callers.
"""

from __future__ import annotations

from typing import Optional

from . import agent, assessment, ledger, policy, store
from .hashing import canonical_digest
from .models import parse_utc
from .validation import ACCEPT, REJECT, UNSUPPORTED, classify_record

DEMO_CLOCK = "2026-09-11T12:20:00Z"  # fixed demo clock (docs 02/22)
_RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

# workflow transitions (doc 05). Reopen from monitoring/closed happens only on
# new material evidence at import time, never as an operator action.
_TRANSITIONS = {
    "new": {"begin_review": "reviewing"},
    "reviewing": {"request_information": "awaiting_information", "record_decision": "decision_recorded"},
    "awaiting_information": {"resume_review": "reviewing"},
    "decision_recorded": {"monitor": "monitoring", "close": "closed"},
    "monitoring": {},
    "closed": {},
}
_RATIONALE_REQUIRED = {"record_decision", "monitor", "close"}
_ACK_REQUIRED = {"monitor", "close"}   # must acknowledge the latest assessment


class WorkspaceError(Exception):
    def __init__(self, code: str, message: str, status: int, *, retryable: bool = False, field_errors=None, extra=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.retryable = retryable
        self.field_errors = field_errors or []
        self.extra = extra or {}


# --- identity / workspace resolution ---------------------------------------

def create_demo_workspace(owner_id: str, mode: str, idempotency_key: Optional[str], request_digest: str) -> dict:
    with store.LOCK:
        def produce():
            ws = store.create_workspace(owner_id, mode)
            ws.record_audit(owner_id, "workspace_created", ws.workspace_id, {"mode": mode})
            return {"workspace_id": ws.workspace_id, "owner_id": owner_id, "mode": mode, "revision": ws.revision}

        if idempotency_key:
            try:
                return store.idempotent(store.create_idempotency_table(), f"{owner_id}:{idempotency_key}", request_digest, produce)
            except KeyError:
                raise WorkspaceError("idempotency_conflict", "Idempotency-Key reused with a different request", 409)
        return produce()


def resolve_workspace(owner_id: str, workspace_id: str) -> store.Workspace:
    ws = store.get_workspace(workspace_id)
    if ws is None:
        raise WorkspaceError("not_found", "workspace not found", 404)
    # A workspace ID in the request is not authorization (doc 05): membership is.
    if owner_id not in ws.members:
        raise WorkspaceError("forbidden", "not a member of this workspace", 403)
    return ws


# --- imports ----------------------------------------------------------------

def _material(assessment_dict: dict) -> bool:
    return any(f.get("material") for f in assessment_dict.get("findings", []))


def _assess_body(ws: store.Workspace, body: dict) -> dict:
    a = assessment.assess(body, now=parse_utc(DEMO_CLOCK), mode=ws.mode).to_dict()
    a["assessment_id"] = store.new_id("as")
    a["policy_version"] = policy.POLICY_VERSION
    a["created_at"] = store.now_iso()
    a["report_id"] = body["report_id"]
    ws.assessments[a["assessment_id"]] = a
    return a


def _apply_current(ws: store.Workspace, case: store.Case, body: dict) -> None:
    """Recompute the case's assessment from the newest applicable report and
    fold in reopen + the unacknowledged urgency floor (doc 06)."""
    a = _assess_body(ws, body)
    case.assessment = a
    case.latest_assessment_id = a["assessment_id"]
    case.current_report_created_at = body["created_at"]
    case.reported_tca = body["reported_tca"]

    new_state, ack_required = assessment.reopen_on_new_evidence(case.state, new_material=_material(a))
    case.state = new_state

    if a.get("review_required"):
        case.latest_assessment_acknowledged = False
        proposed = a.get("proposed_urgency", "P3")
        if proposed in ("P0", "P1"):
            floor = proposed if case.unacknowledged_floor is None else policy.more_urgent(case.unacknowledged_floor, proposed)
            case.unacknowledged_floor = floor
    elif ack_required:
        case.latest_assessment_acknowledged = False


def _store_report(ws: store.Workspace, body: dict, outcome: str, *, make_current: bool) -> store.Case:
    event_key = body["event_key"]
    pair = tuple(sorted((body["primary_object_id"], body["secondary_object_id"])))
    case = ws.cases.get(event_key)
    if case is None:
        case = store.Case(case_id=store.new_id("case"), event_key=event_key, pair=pair, reported_tca=body["reported_tca"])
        ws.cases[event_key] = case
    case.reports.append(store.StoredReport(
        report_id=body["report_id"], source_name=body["source_name"], source_revision=body["source_revision"],
        created_at=body["created_at"], reported_tca=body["reported_tca"], digest=canonical_digest(body),
        outcome=outcome, body=body,
    ))
    if make_current:
        _apply_current(ws, case, body)
    case.revision += 1
    return case


def import_batch(ws: store.Workspace, owner_id: str, records: list[dict], expected_workspace_revision: int,
                 idempotency_key: Optional[str], request_digest: str) -> dict:
    with store.LOCK:
        def produce():
            # Revision is guarded only when actually producing a result; an
            # idempotent replay (below) returns the original summary even though
            # the workspace has since advanced (doc 05).
            if expected_workspace_revision != ws.revision:
                raise WorkspaceError("revision_conflict", "workspace revision changed", 409,
                                     extra={"current_revision": ws.revision})
            counts = {"accepted": 0, "deduplicated": 0, "conflicted": 0, "rejected": 0, "unsupported": 0}
            errors: list[dict] = []
            affected: set[str] = set()
            stored_any = False

            for i, obj in enumerate(records):
                outcome = classify_record(obj)
                if outcome.status == REJECT:
                    counts["rejected"] += 1
                    errors.append({"index": i, "status": REJECT, "reason": outcome.reason})
                    continue
                if outcome.kind != "encounter_report":
                    # scenario inputs (candidate_set/economic/reentry/comms) are
                    # consumed by the compute endpoints, not the case queue.
                    counts["accepted"] += 1
                    continue

                res = ws.ledger.ingest(obj)
                if res == ledger.REJECT_PAIR:
                    counts["rejected"] += 1
                    errors.append({"index": i, "status": REJECT, "reason": ledger.REJECT_PAIR})
                elif res == ledger.DEDUP:
                    counts["deduplicated"] += 1
                elif res == ledger.CONFLICT:
                    counts["conflicted"] += 1
                    case = _store_report(ws, obj, ledger.CONFLICT, make_current=False)
                    affected.add(case.case_id)
                    stored_any = True
                else:  # CURRENT or PRESERVE
                    make_current = (res == ledger.CURRENT)
                    tag = UNSUPPORTED if outcome.status == UNSUPPORTED else res
                    case = _store_report(ws, obj, tag, make_current=make_current)
                    affected.add(case.case_id)
                    stored_any = True
                    if outcome.status == UNSUPPORTED:
                        counts["unsupported"] += 1
                        errors.append({"index": i, "status": UNSUPPORTED, "reason": outcome.reason})
                    else:
                        counts["accepted"] += 1

            if stored_any:
                ws.bump()
                ws.record_audit(owner_id, "import", ws.workspace_id, {k: counts[k] for k in counts})
            return {**counts, "errors": errors, "affected_case_ids": sorted(affected),
                    "workspace_revision": ws.revision}

        if idempotency_key:
            try:
                return store.idempotent(ws.idempotency, idempotency_key, request_digest, produce)
            except KeyError:
                raise WorkspaceError("idempotency_conflict", "Idempotency-Key reused with a different request", 409)
        return produce()


# --- queue / read -----------------------------------------------------------

def _case_summary(case: store.Case) -> dict:
    return {
        "case_id": case.case_id,
        "event_key": case.event_key,
        "object_pair": list(case.pair),
        "reported_tca": case.reported_tca,
        "state": case.state,
        "revision": case.revision,
        "urgency": case.effective_urgency(),
        "proposed_urgency": (case.assessment or {}).get("proposed_urgency"),
        "deadline": case.deadline(),
        "material_concern": case.material_concern(),
        "review_required": bool((case.assessment or {}).get("review_required")),
        "acknowledged": case.latest_assessment_acknowledged,
        "latest_assessment_id": case.latest_assessment_id,
    }


def _sort_key(case: store.Case):
    dl = case.deadline()
    return (
        _RANK[case.effective_urgency()],
        0 if dl is None else 1,          # unknown deadline first within its tier
        dl or "",
        0 if case.material_concern() else 1,
        case.case_id,
    )


def list_cases(ws: store.Workspace, cursor: Optional[str], limit: int) -> dict:
    with store.LOCK:
        limit = max(1, min(limit or 50, 100))
        offset = 0
        if cursor:
            try:
                rev_s, off_s = cursor.split(":", 1)
                if int(rev_s) != ws.revision:
                    raise WorkspaceError("queue_changed", "queue changed between pages; refresh", 409,
                                         extra={"current_revision": ws.revision})
                offset = int(off_s)
            except (ValueError, AttributeError):
                raise WorkspaceError("bad_cursor", "malformed cursor", 400)

        ordered = sorted(ws.cases.values(), key=_sort_key)
        page = ordered[offset:offset + limit]
        next_cursor = f"{ws.revision}:{offset + limit}" if offset + limit < len(ordered) else None

        urgency_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for c in ordered:
            urgency_counts[c.effective_urgency()] += 1
        unresolved_urgent = sum(
            1 for c in ordered if c.effective_urgency() in ("P0", "P1") and c.unresolved_required_review()
        )
        return {
            "cases": [_case_summary(c) for c in page],
            "total": len(ordered),
            "next_cursor": next_cursor,
            "queue_revision": ws.revision,
            "urgency_counts": urgency_counts,
            "workspace_unresolved_urgent": unresolved_urgent,
        }


def _get_case(ws: store.Workspace, case_id: str) -> store.Case:
    for c in ws.cases.values():
        if c.case_id == case_id:
            return c
    raise WorkspaceError("not_found", "case not found", 404)


def get_case(ws: store.Workspace, case_id: str) -> dict:
    with store.LOCK:
        c = _get_case(ws, case_id)
        d = _case_summary(c)
        d["assessment"] = c.assessment
        d["assignment"] = c.assignment
        return d


def get_case_reports(ws: store.Workspace, case_id: str) -> dict:
    with store.LOCK:
        c = _get_case(ws, case_id)
        reports = [{
            "report_id": r.report_id, "source_name": r.source_name, "source_revision": r.source_revision,
            "created_at": r.created_at, "reported_tca": r.reported_tca, "digest": r.digest, "outcome": r.outcome,
        } for r in sorted(c.reports, key=lambda r: r.created_at)]
        return {"case_id": case_id, "reports": reports, "total": len(reports)}


def assess_case(ws: store.Workspace, owner_id: str, case_id: str, expected_revision: int) -> dict:
    with store.LOCK:
        c = _get_case(ws, case_id)
        if expected_revision != c.revision:
            raise WorkspaceError("revision_conflict", "case revision changed", 409, extra={"current_revision": c.revision})
        if c.current_report_created_at is None:
            raise WorkspaceError("unsupported", "no applicable report to assess", 409)
        current = max((r for r in c.reports if r.outcome != ledger.CONFLICT), key=lambda r: r.created_at)
        _apply_current(ws, c, current.body)
        c.revision += 1
        ws.bump()
        ws.record_audit(owner_id, "assess", c.case_id, {"assessment_id": c.latest_assessment_id})
        return get_case(ws, case_id)


def record_action(ws: store.Workspace, owner_id: str, case_id: str, expected_revision: int,
                  action: str, rationale: Optional[str], assessment_id: Optional[str]) -> dict:
    with store.LOCK:
        c = _get_case(ws, case_id)
        if expected_revision != c.revision:
            raise WorkspaceError("revision_conflict", "case revision changed", 409, extra={"current_revision": c.revision})
        allowed = _TRANSITIONS.get(c.state, {})
        if action not in allowed:
            raise WorkspaceError("invalid_transition", f"action '{action}' not allowed from '{c.state}'", 409,
                                 extra={"allowed_next_actions": sorted(allowed)})
        if action in _RATIONALE_REQUIRED and not (rationale and rationale.strip()):
            raise WorkspaceError("rationale_required", f"action '{action}' requires a rationale", 422,
                                 field_errors=[{"field": "rationale", "error": "required"}])
        if action in _ACK_REQUIRED:
            # latest-version acknowledgement (doc 06): must ack the current assessment.
            if assessment_id != c.latest_assessment_id:
                raise WorkspaceError("stale_acknowledgement", "must acknowledge the latest assessment", 409,
                                     extra={"latest_assessment_id": c.latest_assessment_id})
            c.latest_assessment_acknowledged = True
            c.unacknowledged_floor = None

        c.state = allowed[action]
        c.revision += 1
        ws.bump()
        ws.record_audit(owner_id, f"action:{action}", c.case_id, {"rationale": rationale, "state": c.state})
        return get_case(ws, case_id)


def investigate_case(ws: store.Workspace, case_id: str, assessment_id: Optional[str]) -> dict:
    with store.LOCK:
        c = _get_case(ws, case_id)
        a = c.assessment
        if a is None:
            raise WorkspaceError("unsupported", "case has no assessment to investigate", 409)
        if assessment_id is not None and assessment_id != a["assessment_id"]:
            raise WorkspaceError("stale_acknowledgement", "assessment_id is not the latest", 409,
                                 extra={"latest_assessment_id": a["assessment_id"]})
        result = agent.investigate(a)
        ws.record_audit("agent", "investigate", c.case_id, {"mode": result["generation_mode"]})
        return result


def reset_workspace(ws: store.Workspace, owner_id: str, expected_revision: int) -> dict:
    with store.LOCK:
        if expected_revision != ws.revision:
            raise WorkspaceError("revision_conflict", "workspace revision changed", 409, extra={"current_revision": ws.revision})
        ws.cases.clear()
        ws.ledger = ledger.ReportLedger()
        ws.assessments.clear()
        ws.bump()
        ws.record_audit(owner_id, "reset", ws.workspace_id, {})
        return {"workspace_id": ws.workspace_id, "revision": ws.revision}


def activity(ws: store.Workspace, after_sequence: int, limit: int) -> dict:
    with store.LOCK:
        limit = max(1, min(limit or 50, 200))
        events = [e for e in ws.audit if e["sequence"] > after_sequence][:limit]
        return {"events": events, "latest_sequence": len(ws.audit)}
