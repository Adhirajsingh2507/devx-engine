"""Structural + domain validation checks (doc 05, T07) against the encounter
negative mutations and a positive import over all fixtures."""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import validation  # noqa: E402

FX = ROOT / "data" / "fixtures"


def _apply_pointer(obj: dict, pointer: str, *, replacement=None, remove=False):
    parts = pointer.strip("/").split("/")
    cur = obj
    for p in parts[:-1]:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    last = parts[-1]
    key = int(last) if isinstance(cur, list) else last
    if remove:
        del cur[key]
    else:
        cur[key] = replacement


def test_negative_mutations():
    data = json.loads((FX / "encounter_reference.json").read_text())
    base = next(c["input"] for c in data["cases"] if c["id"] == "sigma-50")
    for mut in data["negative_mutations"]:
        obj = copy.deepcopy(base)
        _apply_pointer(obj, mut["json_pointer"], replacement=mut.get("replacement"), remove=mut.get("remove", False))
        outcome = validation.classify_record(obj)
        assert outcome.reason == mut["expected_rejection"], (mut["id"], outcome.status, outcome.reason)


def test_positive_import():
    objs = []
    for c in json.loads((FX / "encounter_reference.json").read_text())["cases"]:
        objs.append(c["input"])
    for name in ["economics", "reentry", "fleet_candidates", "communications"]:
        objs.append(json.loads((FX / f"{name}.json").read_text())["input"])
    summary = validation.import_summary(objs)
    assert summary["rejected"] == 0 and summary["unsupported"] == 0, summary
    assert summary["accepted"] == len(objs)


if __name__ == "__main__":
    test_negative_mutations()
    test_positive_import()
    print("OK: validation checks passed (T07 negative mutations + positive import)")
