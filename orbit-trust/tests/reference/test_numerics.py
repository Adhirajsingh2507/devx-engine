"""Independent reference checks for the encounter probability core (doc 12, T01-T06).

Runnable now with numpy/scipy; validates the Python oracle against the checked
fixture values in data/fixtures/encounter_reference.json. When the Rust core
lands, its outputs are compared against THIS oracle, never the reverse.

Run: python -m pytest tests/reference/test_numerics.py
 or: python tests/reference/test_numerics.py   (self-check, no framework)
"""

from __future__ import annotations

import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from orbit_trust import numerics  # noqa: E402

FIXTURE = ROOT / "data" / "fixtures" / "encounter_reference.json"


def _tol(ref: float) -> float:
    # T01: abs error <= max(1e-12, 1e-7 * reference Pc)
    return max(1e-12, 1e-7 * ref)


def _cases():
    data = json.loads(FIXTURE.read_text())
    return data["cases"]


def test_reference_encounters():
    for case in _cases():
        enc = case["input"]["encounter"]
        proj = numerics.project_encounter(enc["primary"], enc["secondary"])
        exp = case["expected"]

        assert abs(proj.miss_distance_m - exp["miss_distance_m"]) < 0.5, (
            case["id"], proj.miss_distance_m, exp["miss_distance_m"])
        assert abs(proj.combined_radius_m - exp["combined_radius_m"]) < 1e-9

        pc = numerics.collision_probability(proj)
        assert abs(pc - exp["pc"]) <= _tol(exp["pc"]), (case["id"], pc, exp["pc"])

        if "projected_mean_m" in exp:  # anisotropic case: verify geometry too (T03)
            assert abs(proj.mean_m[0] - exp["projected_mean_m"][0]) < 1e-6
            assert abs(proj.mean_m[1] - exp["projected_mean_m"][1]) < 1e-6
            ecov = exp["projected_covariance_m2"]
            for i in range(2):
                for j in range(2):
                    assert abs(proj.covariance_m2[i][j] - ecov[i][j]) < 1e-6


def test_zero_miss_analytic():
    # T02: zero miss isotropic matches analytic 1 - exp(-R^2/(2 sigma^2))
    sigma, radius = 50.0, 10.0
    analytic = 1.0 - math.exp(-(radius**2) / (2.0 * sigma**2))
    pc = numerics.pc_isotropic(0.0, sigma, radius)
    assert abs(pc - analytic) <= _tol(analytic)


def test_radius_monotonic():
    # T10: increasing hard-body radius does not decrease Pc
    prev = -1.0
    for radius in (5.0, 10.0, 20.0, 40.0):
        pc = numerics.pc_isotropic(100.0, 50.0, radius)
        assert pc >= prev - 1e-15
        prev = pc


def _anisotropic_case():
    for c in _cases():
        if c["id"] == "anisotropic":
            return c["input"]["encounter"]
    raise AssertionError("anisotropic fixture missing")


def _baseline_pc():
    enc = _anisotropic_case()
    return numerics.collision_probability(numerics.project_encounter(enc["primary"], enc["secondary"]))


def test_rotation_invariance():
    # T04: rotate all states/covariances by one orthogonal matrix -> Pc invariant.
    import numpy as np

    q, _ = np.linalg.qr(np.random.default_rng(20260911).standard_normal((3, 3)))
    enc = _anisotropic_case()

    def rot(o):
        p = np.asarray(o["position_m"], float)
        v = np.asarray(o["velocity_m_s"], float)
        c = np.asarray(o["position_covariance_m2"], float)
        return {
            "object_id": o["object_id"],
            "position_m": (q @ p).tolist(),
            "velocity_m_s": (q @ v).tolist(),
            "position_covariance_m2": (q @ c @ q.T).tolist(),
            "hard_body_radius_m": o["hard_body_radius_m"],
        }

    pc = numerics.collision_probability(numerics.project_encounter(rot(enc["primary"]), rot(enc["secondary"])))
    assert abs(pc - _baseline_pc()) <= _tol(_baseline_pc())


def test_swap_symmetry():
    # T05: swapping primary/secondary gives the same Pc.
    enc = _anisotropic_case()
    pc = numerics.collision_probability(numerics.project_encounter(enc["secondary"], enc["primary"]))
    assert abs(pc - _baseline_pc()) <= _tol(_baseline_pc())


def test_translation_invariance():
    # T06: common position translation leaves the relative encounter unchanged.
    import numpy as np

    shift = np.array([1234.0, -5678.0, 9012.0])
    enc = _anisotropic_case()

    def move(o):
        o = dict(o)
        o["position_m"] = (np.asarray(o["position_m"], float) + shift).tolist()
        return o

    pc = numerics.collision_probability(numerics.project_encounter(move(enc["primary"]), move(enc["secondary"])))
    assert abs(pc - _baseline_pc()) <= _tol(_baseline_pc())


if __name__ == "__main__":
    test_reference_encounters()
    test_zero_miss_analytic()
    test_radius_monotonic()
    test_rotation_invariance()
    test_swap_symmetry()
    test_translation_invariance()
    print("OK: reference + invariance checks passed (T01-T06, T10)")
