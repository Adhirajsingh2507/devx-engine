"""Reentry exposure checks (doc 08, T31-T33) against reentry.json."""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import reentry  # noqa: E402

FX = ROOT / "data" / "fixtures" / "reentry.json"


def _doc():
    return json.loads(FX.read_text())


def test_primary_footprint():  # T31, T33
    scn = _doc()["input"]
    got = reentry.evaluate(scn)
    exp = _doc()["expected"]
    assert sorted(got["included_population_ids"]) == sorted(exp["included_population_ids"])
    assert got["represented_population"] == exp["represented_population"]           # 150 (inside+boundary; hole excluded)
    assert sorted(got["included_asset_ids"]) == sorted(exp["included_asset_ids"])
    assert got["asset_count"] == exp["asset_count"]
    assert got["exposed_value_by_currency"] == exp["exposed_value_by_currency"]     # INR 1,500,000
    assert got["conditional_expected_damage_by_currency"] == exp["conditional_expected_damage_by_currency"]  # INR 150,000


def test_boundary_point_included():  # T31 boundary convention
    scn = _doc()["input"]
    bc = _doc()["boundary_case"]
    assert reentry.point_in_geometry(bc["coordinates"], scn["footprint"]) == bc["expected_included"]


def test_alternative_footprint_missing_vulnerability():  # T32/T33
    doc = _doc()
    scn = dict(doc["input"], footprint=doc["alternative"]["footprint"])
    got = reentry.evaluate(scn)
    exp = doc["alternative"]["expected"]
    assert got["included_population_ids"] == exp["included_population_ids"]  # pop-outside
    assert got["represented_population"] == exp["represented_population"]    # 500
    assert got["included_asset_ids"] == exp["included_asset_ids"]            # asset-D
    assert got["exposed_value_by_currency"] == exp["exposed_value_by_currency"]  # INR 100,000
    assert got["damage_status"] == exp["damage_status"]                     # unavailable_missing_vulnerability


if __name__ == "__main__":
    test_primary_footprint()
    test_boundary_point_included()
    test_alternative_footprint_missing_vulnerability()
    print("OK: reentry checks passed (T31 holes/boundary, T32 alt footprint, T33 missing vulnerability)")
