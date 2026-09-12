"""Reentry geometry rejection checks (doc 05/08, T32).

Unsupported geometry is rejected visibly, never silently scored or "drawn the
long way around Earth". Builds mutations off the valid reentry.json footprint."""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import reentry  # noqa: E402

FX = ROOT / "data" / "fixtures" / "reentry.json"


def _scn():
    return copy.deepcopy(json.loads(FX.read_text())["input"])


def test_valid_scenario_passes():
    assert reentry.validate_scenario(_scn()) is None


def test_unordered_window():
    scn = _scn()
    scn["window_start"], scn["window_end"] = scn["window_end"], scn["window_start"]
    assert reentry.validate_scenario(scn) == "domain_window_unordered"
    assert reentry.evaluate(scn) == {"status": "rejected", "reason": "domain_window_unordered"}


def test_dateline_crossing():
    scn = _scn()
    scn["footprint"] = {
        "type": "Polygon",
        "coordinates": [[[170, 0], [-170, 0], [-170, 10], [170, 10], [170, 0]]],
    }
    assert reentry.validate_scenario(scn) == "domain_dateline_crossing"


def test_latitude_out_of_range():
    scn = _scn()
    scn["footprint"] = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 0], [2, 88], [0, 88], [0, 0]]],
    }
    assert reentry.validate_scenario(scn) == "domain_latitude_out_of_range"


def test_ring_not_closed():
    scn = _scn()
    scn["footprint"] = {"type": "Polygon", "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 3]]]}
    assert reentry.validate_scenario(scn) == "domain_ring_not_closed"


def test_self_intersecting_ring():
    scn = _scn()
    scn["footprint"] = {  # bowtie
        "type": "Polygon",
        "coordinates": [[[0, 0], [2, 2], [2, 0], [0, 2], [0, 0]]],
    }
    assert reentry.validate_scenario(scn) == "domain_self_intersecting_ring"


def test_hole_not_contained():
    scn = _scn()
    scn["footprint"] = {
        "type": "Polygon",
        "coordinates": [
            [[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]],
            [[5, 5], [5, 6], [6, 6], [6, 5], [5, 5]],  # hole outside the outer ring
        ],
    }
    assert reentry.validate_scenario(scn) == "domain_hole_not_contained"


def test_point_budget_exceeded():
    scn = _scn()
    scn["population_points"] = [
        {"sample_id": f"p{i}", "coordinates": [0.5, 0.5], "represented_population": 1}
        for i in range(1001)
    ]
    assert reentry.validate_scenario(scn) == "domain_point_budget_exceeded"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("OK: reentry geometry rejection checks passed (T32: window/dateline/latitude/closure/self-intersection/hole/budget)")
