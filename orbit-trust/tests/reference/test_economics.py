"""Economics checks (doc 08, T29-T30) against economics.json.

Fixtures are parsed with parse_float=Decimal so probabilities carry exact
decimal text into the money arithmetic (doc 05/08)."""

from __future__ import annotations

import copy
import json
import pathlib
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import economics  # noqa: E402

FX = ROOT / "data" / "fixtures" / "economics.json"


def _doc():
    return json.loads(FX.read_text(), parse_float=Decimal)


def _apply_pointer(obj, pointer, replacement):
    parts = pointer.strip("/").split("/")
    cur = obj
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    key = parts[-1]
    cur[int(key) if isinstance(cur, list) else key] = replacement


def test_reference_case():  # T29
    scn = _doc()["input"]
    got = economics.evaluate(scn)
    exp = _doc()["expected"]
    assert got["status"] == "available"
    for k in ("currency", "loss_before", "loss_after", "expected_loss_before",
              "expected_loss_after", "gross_reduction", "net_benefit"):
        assert got[k] == exp[k], (k, got[k], exp[k])


def test_negative_mutations():  # T30
    doc = _doc()
    for mut in doc["negative_mutations"]:
        scn = copy.deepcopy(doc["input"])
        _apply_pointer(scn, mut["json_pointer"], mut.get("replacement"))
        got = economics.evaluate(scn)
        if "expected_rejection" in mut:
            assert got["status"] == "unavailable", (mut["id"], got)
            assert got["reason"] == mut["expected_rejection"], (mut["id"], got["reason"])
        else:  # negative-net: displayed, not clipped
            assert got["status"] == "available"
            assert got["net_benefit"] == mut["expected_net_benefit"], (mut["id"], got["net_benefit"])


if __name__ == "__main__":
    test_reference_case()
    test_negative_mutations()
    print("OK: economics checks passed (T29 reference, T30 mixed-currency/unknown/negative-net)")
