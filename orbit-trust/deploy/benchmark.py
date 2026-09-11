"""Benchmark the encounter Pc core (doc 12): sequential Python reference vs
sequential Rust vs parallel Rust (Rayon) vs cached, on identical work.

Run under the build venv (needs orbit_core + numpy/scipy):
  .venv312/bin/python deploy/benchmark.py
Synthetic timings on the dev machine; not a public-tier measurement (doc 12)."""

from __future__ import annotations

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import orbit_core  # noqa: E402
from orbit_trust import numerics  # noqa: E402

# identical work: N distinct 2D Pc problems [mx,my,sxx,sxy,syy,R]
N = 2000
problems = [[35.0 + (i % 50), -12.0, 900.0, 180.0, 400.0, 10.0] for i in range(N)]


def _time(label, fn):
    t = time.perf_counter()
    out = fn()
    dt = (time.perf_counter() - t) * 1000
    print(f"  {label:24} {dt:8.1f} ms")
    return out, dt


def main():
    print(f"Pc core benchmark, {N} problems (identical work):")
    ref, _ = _time("sequential Python (ref)", lambda: [numerics.pc_general((p[0], p[1]), ((p[2], p[3]), (p[3], p[4])), p[5]) for p in problems])
    rseq, _ = _time("sequential Rust", lambda: [orbit_core.pc_2d(*p) for p in problems])
    rpar, _ = _time("parallel Rust (Rayon)", lambda: orbit_core.pc_2d_batch(problems))

    cache: dict = {}

    def cached():
        out = []
        for p in problems:
            k = tuple(p)
            if k not in cache:
                cache[k] = orbit_core.pc_2d(*p)
            out.append(cache[k])
        return out

    _time("cached Rust", cached)

    # correctness: all methods agree
    for a, b in zip(ref, rpar):
        assert abs(a - b) <= max(1e-12, 1e-6 * abs(a)), (a, b)
    for a, b in zip(rseq, rpar):
        assert abs(a - b) < 1e-15
    print("  all methods agree on identical work: OK")


if __name__ == "__main__":
    main()
