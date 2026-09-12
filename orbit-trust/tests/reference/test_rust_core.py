"""Validate the Rust production core (orbit_core) against the independent Python
oracle (orbit_trust.numerics) across the encounter fixtures (doc 12, T01-T10).

Requires the compiled extension: run under the build venv, e.g.
  .venv312/bin/python tests/reference/test_rust_core.py
The Rust core is NEVER its own oracle; the Python oracle is the reference."""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import orbit_core  # compiled extension  # noqa: E402
from orbit_trust import numerics  # noqa: E402

FX = ROOT / "data" / "fixtures" / "encounter_reference.json"


def _flat(m):
    return [x for row in m for x in row]


def _states(enc):
    return enc["primary"], enc["secondary"], enc["interval_start_offset_s"], enc["interval_end_offset_s"]


def test_rust_matches_oracle():
    cases = json.loads(FX.read_text())["cases"]
    for c in cases:
        enc = c["input"]["encounter"]
        p, s, start, end = _states(enc)
        tca, miss, pc = orbit_core.project_and_pc(
            p["position_m"], p["velocity_m_s"], _flat(p["position_covariance_m2"]),
            s["position_m"], s["velocity_m_s"], _flat(s["position_covariance_m2"]),
            p["hard_body_radius_m"], s["hard_body_radius_m"], start, end,
        )
        ref = numerics.evaluate_encounter(enc)
        assert ref["status"] == "supported", c["id"]
        assert abs(tca - ref["tca_offset_s"]) < 1e-6, (c["id"], tca, ref["tca_offset_s"])
        assert abs(miss - ref["miss_distance_m"]) < 1e-6, (c["id"], miss, ref["miss_distance_m"])
        tol = max(1e-12, 1e-6 * ref["pc"])  # cross-method (Rust GL/trapezoid vs SciPy)
        assert abs(pc - ref["pc"]) <= tol, (c["id"], pc, ref["pc"])


def test_rust_matches_fixture_expected():
    # T01-T03 directly against the checked fixture Pc values, via the Rust core.
    for c in json.loads(FX.read_text())["cases"]:
        enc = c["input"]["encounter"]
        p, s, start, end = _states(enc)
        _tca, _miss, pc = orbit_core.project_and_pc(
            p["position_m"], p["velocity_m_s"], _flat(p["position_covariance_m2"]),
            s["position_m"], s["velocity_m_s"], _flat(s["position_covariance_m2"]),
            p["hard_body_radius_m"], s["hard_body_radius_m"], start, end,
        )
        exp = c["expected"]["pc"]
        assert abs(pc - exp) <= max(1e-12, 1e-6 * exp), (c["id"], pc, exp)


def test_batch_matches_sequential():
    problems = [[100.0, 0.0, 400.0, 0.0, 400.0, 10.0],
                [35.0, -12.0, 900.0, 180.0, 400.0, 10.0],
                [0.0, 0.0, 2500.0, 0.0, 2500.0, 10.0]]
    batch = orbit_core.pc_2d_batch(problems)
    seq = [orbit_core.pc_2d(*p) for p in problems]
    for b, s in zip(batch, seq):
        assert abs(b - s) < 1e-15


def test_error_paths():
    import pytest

    enc = next(c["input"]["encounter"] for c in json.loads(FX.read_text())["cases"] if c["id"] == "sigma-50")
    p, s = enc["primary"], enc["secondary"]
    # zero relative speed
    with pytest.raises(ValueError, match="relative_speed"):
        orbit_core.project_and_pc(
            p["position_m"], p["velocity_m_s"], _flat(p["position_covariance_m2"]),
            s["position_m"], p["velocity_m_s"], _flat(s["position_covariance_m2"]),
            5.0, 5.0, -5.0, 5.0,
        )
    # tca outside interval (relative v [5,0,0] along miss -> tau=-20)
    with pytest.raises(ValueError, match="tca_outside_supported_interval"):
        orbit_core.project_and_pc(
            p["position_m"], p["velocity_m_s"], _flat(p["position_covariance_m2"]),
            s["position_m"], [5.0, 7500.0, 0.0], _flat(s["position_covariance_m2"]),
            5.0, 5.0, -0.001, 0.001,
        )


if __name__ == "__main__":
    test_rust_matches_oracle()
    test_rust_matches_fixture_expected()
    test_batch_matches_sequential()
    try:
        test_error_paths()
    except ImportError:
        pass  # pytest optional for the __main__ path
    print("OK: Rust core matches Python oracle + fixtures (T01-T10 via orbit_core)")
