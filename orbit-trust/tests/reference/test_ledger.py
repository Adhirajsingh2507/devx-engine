"""Report ledger checks (doc 05, T16-T18) driven by the relations in
report_update_cases.json. Digests are synthesized by mutating a base report body
according to each case's raw_digest_relation."""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import ledger  # noqa: E402
from orbit_trust.hashing import canonical_digest  # noqa: E402

FX = ROOT / "data" / "fixtures"


def _base():
    cases = json.loads((FX / "encounter_reference.json").read_text())["cases"]
    r = copy.deepcopy(next(c["input"] for c in cases if c["id"] == "sigma-50"))
    r["source_revision"] = "r1"
    r["created_at"] = "2026-09-11T12:00:00Z"
    return r


def test_identical_retry_dedup():  # T16
    lg = ledger.ReportLedger()
    r = _base()
    assert lg.ingest(r) == ledger.CURRENT
    assert lg.ingest(copy.deepcopy(r)) == ledger.DEDUP


def test_out_of_order_preserves_history():  # T16
    lg = ledger.ReportLedger()
    assert lg.ingest(_base()) == ledger.CURRENT
    older = _base()
    older["source_revision"] = "r0"
    older["created_at"] = "2026-09-11T11:00:00Z"
    older["notes"] = "different body"
    assert canonical_digest(older) != canonical_digest(_base())
    assert lg.ingest(older) == ledger.PRESERVE


def test_conflicting_source_body():  # T17
    lg = ledger.ReportLedger()
    assert lg.ingest(_base()) == ledger.CURRENT
    conflicting = _base()  # same source_revision r1, different body
    conflicting["notes"] = "same revision, different content"
    assert lg.ingest(conflicting) == ledger.CONFLICT


def test_event_pair_conflict_rejected():  # T18
    lg = ledger.ReportLedger()
    assert lg.ingest(_base()) == ledger.CURRENT
    other_pair = _base()
    other_pair["secondary_object_id"] = "C"  # event-AB reused with pair {A,C}
    assert lg.ingest(other_pair) == ledger.REJECT_PAIR


def test_canonicalization_key_order():  # doc 04 canonical digest property
    a = {"x": 1, "y": [1, 2], "z": {"b": 2, "a": 1}}
    b = {"z": {"a": 1, "b": 2}, "y": [1, 2], "x": 1}
    assert canonical_digest(a) == canonical_digest(b)


if __name__ == "__main__":
    test_identical_retry_dedup()
    test_out_of_order_preserves_history()
    test_conflicting_source_body()
    test_event_pair_conflict_rejected()
    test_canonicalization_key_order()
    print("OK: ledger checks passed (T16-T18 + canonical digest)")
