"""Triage policy checks (doc 06, T11-T15) against data/fixtures/triage_cases.json."""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import policy  # noqa: E402
from orbit_trust.models import parse_utc  # noqa: E402

FIXTURE = ROOT / "data" / "fixtures" / "triage_cases.json"


def test_proposed_urgency():
    data = json.loads(FIXTURE.read_text())
    slack = data["immediate_slack_s"]
    for c in data["cases"]:
        deadline = parse_utc(c["review_deadline"]) if c["review_deadline"] else None
        got = policy.proposed_urgency(
            parse_utc(c["now"]), deadline, c["review_required"], immediate_slack_s=slack
        )
        assert got == c["expected_proposed_urgency"], (c["id"], got, c["expected_proposed_urgency"])


def test_acknowledgement_floor():
    # T14: a downgrade after an urgent alert holds until latest-version ack.
    data = json.loads(FIXTURE.read_text())
    for c in data["acknowledgement_cases"]:
        got = policy.effective_urgency(
            c["new_proposed_urgency"],
            unacknowledged_floor=c["previous_unacknowledged_floor"],
            latest_assessment_acknowledged=c["latest_assessment_acknowledged"],
        )
        assert got == c["expected_effective_urgency"], (c["id"], got)


def test_review_deadline_fixture():
    # doc 06: command 14:30, allowance 90 min -> deadline 13:00; at 12:20 slack 40 min -> P1.
    dl = policy.review_deadline("2026-09-11T14:30:00Z", 5400)
    assert dl == parse_utc("2026-09-11T13:00:00Z")
    assert policy.proposed_urgency(parse_utc("2026-09-11T12:20:00Z"), dl, True) == "P1"


if __name__ == "__main__":
    test_proposed_urgency()
    test_acknowledgement_floor()
    test_review_deadline_fixture()
    print("OK: triage policy checks passed (T12 deadline tiers, T14 ack floor)")
