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
    # Distinct fixtures: all accepted, nothing deduplicated/conflicted/rejected.
    # (The six encounter cases share event_key event-AB with distinct source
    # revisions, so they are separate ledger revisions, not duplicates.)
    objs = []
    for c in json.loads((FX / "encounter_reference.json").read_text())["cases"]:
        obj = copy.deepcopy(c["input"])
        obj["source_revision"] = c["id"]  # make each a distinct source revision
        objs.append(obj)
    for name in ["economics", "reentry", "fleet_candidates", "communications"]:
        objs.append(json.loads((FX / f"{name}.json").read_text())["input"])
    summary = validation.import_summary(objs)
    assert summary["rejected"] == 0 and summary["unsupported"] == 0, summary
    assert summary["deduplicated"] == 0 and summary["conflicted"] == 0, summary
    assert summary["accepted"] == len(objs), summary


def test_import_dedup_and_conflict_counts():
    # doc 05 import summary distinguishes deduplicated and conflicted.
    base = next(
        c["input"] for c in json.loads((FX / "encounter_reference.json").read_text())["cases"]
        if c["id"] == "sigma-50"
    )
    base = copy.deepcopy(base)
    base["source_revision"] = "r1"
    dup = copy.deepcopy(base)                       # identical -> deduplicated
    conflict = copy.deepcopy(base)
    conflict["notes"] = "same revision, different body"  # -> conflicted
    summary = validation.import_summary([base, dup, conflict])
    assert summary["accepted"] == 1, summary
    assert summary["deduplicated"] == 1, summary
    assert summary["conflicted"] == 1, summary


if __name__ == "__main__":
    test_negative_mutations()
    test_positive_import()
    test_import_dedup_and_conflict_counts()
    print("OK: validation checks passed (T07 mutations + import accept/dedup/conflict)")
