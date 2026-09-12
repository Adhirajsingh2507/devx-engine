"""Assessment engine checks (docs 05/06): T11 (uncertainty doesn't erase
conflict), T13 (cosmetic vs material), T15 (reopen on new material evidence)."""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import assessment  # noqa: E402
from orbit_trust.models import parse_utc  # noqa: E402

FX = ROOT / "data" / "fixtures" / "encounter_reference.json"
NOW = parse_utc("2026-09-11T12:20:00Z")  # the fixed demo clock (doc 02)


def _report(case_id: str) -> dict:
    for c in json.loads(FX.read_text())["cases"]:
        if c["id"] == case_id:
            return copy.deepcopy(c["input"])
    raise AssertionError(case_id)


def test_high_uncertainty_still_reviews():  # T11
    hi = assessment.assess(_report("sigma-200"), now=NOW)   # pc ~1.1e-3 > threshold
    lo = assessment.assess(_report("sigma-1000"), now=NOW)  # pc ~5e-5 < threshold

    assert hi.material_concern and hi.review_required
    assert any(f.code == "RISK_THRESHOLD_EXCEEDED" for f in hi.findings)
    assert hi.evidence_state == "usable"  # risk crossing is a concern, not an evidence gap
    assert hi.proposed_urgency == "P1"  # deadline 13:00, now 12:20 -> slack 40m

    # sigma-1000 alone: low Pc, complete evidence -> monitor
    assert not lo.material_concern and not lo.review_required
    assert lo.proposed_urgency == "P3"

    # but a missing-evidence gap keeps the review required even at the lower Pc:
    # the reduced probability does not erase the conflict.
    r = _report("sigma-1000")
    r["evidence_metadata"]["secondary_last_observation_at"] = None
    gapped = assessment.assess(r, now=NOW)
    assert gapped.review_required
    assert not gapped.material_concern  # not asserting high collision probability
    assert any(f.code == "MISSING_OBSERVATION_METADATA" for f in gapped.findings)


def test_cosmetic_vs_material():  # T13
    base = assessment.assess(_report("sigma-1000"), now=NOW)
    assert not base.review_required and base.evidence_state == "usable"

    # cosmetic: unknown deadline (timing only, non-material) does not force review
    r = _report("sigma-1000")
    r["planning"]["latest_command_at"] = None
    cosmetic = assessment.assess(r, now=NOW)
    assert not cosmetic.review_required
    assert any(f.code == "DEADLINE_UNKNOWN" and not f.material for f in cosmetic.findings)

    # material: unknown maneuver context does force review
    r2 = _report("sigma-1000")
    r2["evidence_metadata"]["maneuver_information_status"] = "unknown"
    material = assessment.assess(r2, now=NOW)
    assert material.review_required
    assert any(f.code == "MANEUVER_CONTEXT_UNKNOWN" and f.material for f in material.findings)


def test_stale_evidence_incomplete():  # doc 06 staleness
    r = _report("sigma-200")
    r["evidence_metadata"]["primary_solution_epoch"] = "2026-09-11T00:00:00Z"  # >6h old
    a = assessment.assess(r, now=NOW)
    assert any(f.code == "STALE_SOLUTION" for f in a.findings)
    assert a.evidence_state in ("incomplete", "inconsistent")


def test_reopen_on_new_evidence():  # T15
    assert assessment.reopen_on_new_evidence("closed", new_material=True) == ("reviewing", True)
    assert assessment.reopen_on_new_evidence("monitoring", new_material=True) == ("reviewing", True)
    assert assessment.reopen_on_new_evidence("closed", new_material=False) == ("closed", False)


if __name__ == "__main__":
    test_high_uncertainty_still_reviews()
    test_cosmetic_vs_material()
    test_stale_evidence_incomplete()
    test_reopen_on_new_evidence()
    print("OK: assessment engine checks passed (T11 dilution, T13 cosmetic/material, T15 reopen)")
