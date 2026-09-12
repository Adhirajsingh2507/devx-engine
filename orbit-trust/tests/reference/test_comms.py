"""Communication simulation checks (doc 07, T28) against communications.json."""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import comms  # noqa: E402

FX = ROOT / "data" / "fixtures" / "communications.json"


def _doc():
    return json.loads(FX.read_text())


def test_timing_fits():
    scn = _doc()["input"]
    got = comms.timing_feasibility(scn)
    exp = _doc()["expected"]
    assert got["timing_status"] == exp["timing_status"]
    assert got["modeled_completion"] == exp["modeled_completion"]
    assert got["real_transmission_performed"] is False


def test_scripted_sequence():
    scn = _doc()["input"]
    p = comms.Packet(scn)
    dispatch = {
        "authorize": p.authorize,
        "send": p.send,
        "acknowledge": p.acknowledge,
        "report_execution": p.report_execution,
    }
    for ev in _doc()["scripted_events"]:
        state = dispatch[ev["event"]](ev["at"])
        assert state == ev["expected_state"], (ev["event"], state, ev["expected_state"])


def test_negative_cases():
    d = _doc()
    scn = d["input"]

    # outside-contact: send after the window closes -> rejected, not sent
    p = comms.Packet(scn)
    p.authorize(scn["now"])
    assert p.send("2026-09-11T14:16:00Z") == comms.REJECT_SEND

    # expired-packet: send at/after expiry -> expired (inclusive)
    p = comms.Packet(scn)
    p.authorize(scn["now"])
    assert p.send("2026-09-11T14:20:00Z") == comms.EXPIRED

    # no-ack: sent then timeout -> failed, never executed
    p = comms.Packet(scn)
    p.authorize(scn["now"])
    p.send(scn["now"])
    assert p.ack_timeout() == comms.FAILED
    assert p.report_execution(scn["now"]) == comms.FAILED  # cannot execute a failed packet

    # stale-comparison: authorization rejected
    p = comms.Packet(scn)
    assert p.authorize(scn["now"], comparison_stale=True) == comms.REJECT_AUTH

    # unknown-contact: missing contact_start -> timing_unknown
    unknown = dict(scn, contact_start=None)
    assert comms.timing_feasibility(unknown)["timing_status"] == "timing_unknown"


if __name__ == "__main__":
    test_timing_fits()
    test_scripted_sequence()
    test_negative_cases()
    print("OK: communication simulation checks passed (T28)")
