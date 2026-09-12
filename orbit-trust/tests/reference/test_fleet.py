"""Fleet comparison checks (doc 07, T25-T26) against fleet_candidates.json.

The hero case: candidate-one improves A-B but creates an A-C conflict -> blocked;
candidate-two moves clear -> passes; baseline is blocked. Every pair's evidence
stays visible."""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import fleet  # noqa: E402

FX = ROOT / "data" / "fixtures" / "fleet_candidates.json"


def _pc_tol(ref: float) -> float:
    return max(1e-18, 1e-6 * abs(ref)) if ref else 1e-18


def test_fleet_comparison():
    doc = json.loads(FX.read_text())
    result = fleet.compare(doc["input"])
    expected = doc["expected"]

    got = {c["candidate_id"]: c for c in result["candidate_results"]}
    exp = {c["candidate_id"]: c for c in expected["candidate_results"]}
    assert set(got) == set(exp)

    for cid, ec in exp.items():
        gc = got[cid]
        assert gc["disposition"] == ec["disposition"], (cid, gc["disposition"], ec["disposition"])
        gpairs = {tuple(p["pair"]): p for p in gc["pairs"]}
        for ep in ec["pairs"]:
            gp = gpairs[tuple(ep["pair"])]
            assert abs(gp["miss_distance_m"] - ep["miss_distance_m"]) < 0.5, (cid, ep["pair"])
            assert gp["threshold_exceeded"] == ep["threshold_exceeded"], (cid, ep["pair"])
            assert abs(gp["pc"] - ep["pc"]) <= _pc_tol(ep["pc"]), (cid, ep["pair"], gp["pc"], ep["pc"])

    assert result["preferred_among_passing_alternatives"] == expected["preferred_among_passing_alternatives"]
    assert result["coverage_label"] == expected["coverage_label"]


def test_ab_improvement_creates_ac_conflict():
    # T25: candidate-one fixes A-B but its A-C pair now exceeds threshold.
    doc = json.loads(FX.read_text())
    result = fleet.compare(doc["input"])
    c1 = next(c for c in result["candidate_results"] if c["candidate_id"] == "candidate-one")
    ab = next(p for p in c1["pairs"] if p["pair"] == ["A", "B"])
    ac = next(p for p in c1["pairs"] if p["pair"] == ["A", "C"])
    assert not ab["threshold_exceeded"]  # A-B improved
    assert ac["threshold_exceeded"]      # A-C now a concern
    assert c1["disposition"] == fleet.BLOCKED


if __name__ == "__main__":
    test_fleet_comparison()
    test_ab_improvement_creates_ac_conflict()
    print("OK: fleet comparison checks passed (T25-T26, hero reversal)")
