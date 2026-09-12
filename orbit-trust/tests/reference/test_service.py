"""End-to-end self-check for the workspace service layer (docs 05/06).

Runnable without a test framework: `python3 tests/reference/test_service.py`.
Drives the full core loop against real fixture reports and asserts the workflow,
dedup/revision/transition guards and the investigate fallback.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from orbit_trust import service, store  # noqa: E402
from orbit_trust.service import WorkspaceError  # noqa: E402

_FIX = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fixtures", "encounter_reference.json")


def _reports():
    cases = json.load(open(_FIX))["cases"]
    inputs = [c["input"] for c in cases if c.get("schema_definition") == "Report"]
    assert inputs, "no Report inputs in fixture"
    return inputs


def _expect_error(code, fn):
    try:
        fn()
    except WorkspaceError as e:
        assert e.code == code, f"expected {code}, got {e.code}"
        return e
    raise AssertionError(f"expected WorkspaceError {code}, none raised")


def demo():
    reports = _reports()
    r0 = reports[0]

    # create workspace
    ws_info = service.create_demo_workspace("user-1", "public_synthetic", None, "d0")
    ws = service.resolve_workspace("user-1", ws_info["workspace_id"])
    assert ws.revision == 0

    # isolation: a different identity cannot touch it
    _expect_error("forbidden", lambda: service.resolve_workspace("intruder", ws.workspace_id))

    # import one report -> one accepted, one case
    summ = service.import_batch(ws, "user-1", [r0], 0, None, "i0")
    assert summ["accepted"] == 1, summ
    assert len(summ["affected_case_ids"]) == 1
    assert ws.revision == 1

    # stale workspace revision -> 409
    _expect_error("revision_conflict", lambda: service.import_batch(ws, "user-1", [r0], 0, None, "i-stale"))

    # identical re-import -> deduplicated, no new revision
    summ2 = service.import_batch(ws, "user-1", [r0], 1, None, "i1")
    assert summ2["deduplicated"] == 1 and summ2["accepted"] == 0, summ2
    assert ws.revision == 1

    # queue
    q = service.list_cases(ws, None, 50)
    assert q["total"] == 1
    case_id = q["cases"][0]["case_id"]
    assert q["cases"][0]["urgency"] in ("P0", "P1", "P2", "P3")
    assert set(q["urgency_counts"]) == {"P0", "P1", "P2", "P3"}

    # queue cursor bound to a stale revision -> 409 QUEUE_CHANGED
    _expect_error("queue_changed", lambda: service.list_cases(ws, "0:0", 50))

    # case detail carries the assessment + findings
    detail = service.get_case(ws, case_id)
    assert detail["assessment"] is not None
    assert "findings" in detail["assessment"]
    latest = detail["latest_assessment_id"]
    rev = detail["revision"]

    # reports history
    hist = service.get_case_reports(ws, case_id)
    assert hist["total"] >= 1

    # invalid transition from 'new'
    err = _expect_error("invalid_transition",
                        lambda: service.record_action(ws, "user-1", case_id, rev, "close", "x", latest))
    assert "begin_review" in err.extra["allowed_next_actions"]

    # begin_review (revision guarded)
    _expect_error("revision_conflict",
                  lambda: service.record_action(ws, "user-1", case_id, 999, "begin_review", None, None))
    c = service.record_action(ws, "user-1", case_id, rev, "begin_review", None, None)
    assert c["state"] == "reviewing"

    # record_decision requires a rationale
    _expect_error("rationale_required",
                  lambda: service.record_action(ws, "user-1", case_id, c["revision"], "record_decision", "", latest))
    c = service.record_action(ws, "user-1", case_id, c["revision"], "record_decision", "reviewed; synthetic", latest)
    assert c["state"] == "decision_recorded"

    # close requires acknowledging the LATEST assessment
    _expect_error("stale_acknowledgement",
                  lambda: service.record_action(ws, "user-1", case_id, c["revision"], "close", "done", "as_wrong"))
    c = service.record_action(ws, "user-1", case_id, c["revision"], "close", "done; monitored", latest)
    assert c["state"] == "closed"
    assert c["acknowledged"] is True

    # investigate: deterministic, validated template fallback
    inv = service.investigate_case(ws, case_id, None)
    assert inv["generation_mode"] == "template_fallback"
    assert inv["selection"]["summary_template_code"]
    for fid in inv["selection"]["ordered_finding_ids"]:
        assert any(f["code"] == fid for f in detail["assessment"]["findings"])

    # reset clears the sandbox
    before = ws.revision
    service.reset_workspace(ws, "user-1", before)
    assert service.list_cases(ws, None, 50)["total"] == 0

    # idempotent import replay returns the original summary; different body -> 409
    ws2_info = service.create_demo_workspace("user-2", "public_synthetic", None, "d2")
    ws2 = service.resolve_workspace("user-2", ws2_info["workspace_id"])
    a = service.import_batch(ws2, "user-2", [r0], 0, "K1", "same")
    b = service.import_batch(ws2, "user-2", [r0], 0, "K1", "same")   # replay
    assert a == b, "idempotent replay must return the original result"
    _expect_error("idempotency_conflict",
                  lambda: service.import_batch(ws2, "user-2", [r0], ws2.revision, "K1", "different"))

    print("PASS test_service: full core loop, guards, investigate fallback, idempotency")


if __name__ == "__main__":
    demo()
