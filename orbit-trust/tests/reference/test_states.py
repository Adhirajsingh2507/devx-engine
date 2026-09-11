"""Unsupported / precision states (doc 06, T08-T09) via evaluate_encounter."""

from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import numerics  # noqa: E402

FX = ROOT / "data" / "fixtures"


def _enc():
    cases = json.loads((FX / "encounter_reference.json").read_text())["cases"]
    return copy.deepcopy(next(c["input"]["encounter"] for c in cases if c["id"] == "sigma-50"))


def test_supported_baseline():
    out = numerics.evaluate_encounter(_enc())
    assert out["status"] == "supported"
    assert abs(out["pc"] - 0.002733592576274527) <= max(1e-12, 1e-7 * out["pc"])


def test_low_relative_speed_unsupported():  # T08
    enc = _enc()
    enc["secondary"]["velocity_m_s"] = enc["primary"]["velocity_m_s"]  # |rel v| = 0
    out = numerics.evaluate_encounter(enc)
    assert out["status"] == "unsupported"
    assert out["pc"] is None


def test_tca_outside_interval_unsupported():  # T08 endpoint-only
    enc = _enc()
    # relative velocity [5,0,0] along the [100,0,0] miss -> tau = -20 s, well
    # outside a narrow interval.
    enc["secondary"]["velocity_m_s"] = [5.0, 7500.0, 0.0]  # primary is [0,7500,0]
    enc["interval_start_offset_s"] = -0.001
    enc["interval_end_offset_s"] = 0.001
    out = numerics.evaluate_encounter(enc)
    assert out["status"] == "unsupported"
    assert out["reason"] == "tca_outside_supported_interval"


def test_invalid_covariance_unsupported():  # T07/T08 boundary
    enc = _enc()
    enc["primary"]["position_covariance_m2"][0][0] = -1.0
    out = numerics.evaluate_encounter(enc)
    assert out["status"] == "unsupported"
    assert out["reason"] == "domain_invalid_covariance"


def test_underflow_below_precision():  # T09
    enc = _enc()
    tiny = [[1e-6, 0, 0], [0, 1e-6, 0], [0, 0, 1e-6]]
    enc["primary"]["position_covariance_m2"] = tiny
    enc["secondary"]["position_covariance_m2"] = tiny
    enc["secondary"]["position_m"] = [7000000 + 100000, 0, 0]  # huge miss vs tiny sigma
    out = numerics.evaluate_encounter(enc)
    # Must NOT assert a definitive zero collision probability.
    assert out["status"] in {"below_computable_precision", "supported"}
    if out["status"] == "below_computable_precision":
        assert out["pc"] is None


if __name__ == "__main__":
    test_supported_baseline()
    test_low_relative_speed_unsupported()
    test_tca_outside_interval_unsupported()
    test_invalid_covariance_unsupported()
    test_underflow_below_precision()
    print("OK: encounter state checks passed (T08 low-speed/endpoint/covariance, T09 precision)")
