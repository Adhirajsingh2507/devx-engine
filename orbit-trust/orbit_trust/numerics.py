"""Supported short-linear-encounter probability (handoff doc 06).

This is the *independent Python reference oracle* (doc 12): SciPy ncx2 for
isotropic cases and deterministic polar quadrature for the general case. The
production path is the Rust/PyO3 core (crates/orbit_core); per doc 12 the Rust
routine must NOT be its own oracle, so this module stays a separate
implementation and never imports the extension.

Domain (doc 06): two positions/velocities/position-covariances at a common
Cartesian inertial epoch, independent Gaussian position errors, combined
circular hard-body region. Velocity uncertainty is neglected by this method.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import integrate
from scipy.stats import ncx2

# Numerical engineering defaults, not physical uncertainty estimates (doc 06).
_ORTHOGONALITY_TOL = 1e-8
_ISOTROPY_TOL = 1e-9


@dataclass(frozen=True)
class Projection:
    tca_offset_s: float
    miss_distance_m: float
    combined_radius_m: float
    mean_m: tuple[float, float]
    covariance_m2: tuple[tuple[float, float], tuple[float, float]]


def _encounter_plane_basis(v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic basis (doc 06): n=v/|v|; pick the Cartesian axis least
    aligned with n (ties x, then y, then z); e1=norm(axis x n), e2=n x e1."""
    speed = float(np.linalg.norm(v))
    if speed < 1.0:  # doc 06: relative speed below 1 m/s is unsupported
        raise ValueError("relative_speed_below_supported_minimum")
    n = v / speed
    alignment = np.abs(n)
    axis_index = int(np.argmin(alignment))  # np.argmin returns first on ties -> x<y<z
    axis = np.zeros(3)
    axis[axis_index] = 1.0
    e1 = np.cross(axis, n)
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(n, e1)
    return e1, e2


def project_encounter(primary: dict, secondary: dict, *, independent: bool = True) -> Projection:
    """Project the relative state onto the encounter plane.

    primary/secondary are ObjectState dicts (schema `ObjectState`): position_m,
    velocity_m_s, position_covariance_m2, hard_body_radius_m.
    """
    r_p = np.asarray(primary["position_m"], dtype=float)
    r_s = np.asarray(secondary["position_m"], dtype=float)
    v_p = np.asarray(primary["velocity_m_s"], dtype=float)
    v_s = np.asarray(secondary["velocity_m_s"], dtype=float)
    c_p = np.asarray(primary["position_covariance_m2"], dtype=float)
    c_s = np.asarray(secondary["position_covariance_m2"], dtype=float)

    if not independent:
        raise NotImplementedError("supplied_cross_covariance not yet implemented (doc 06)")

    r = r_s - r_p
    v = v_s - v_p
    vv = float(v @ v)
    tau = -float(r @ v) / vv  # unconstrained TCA relative to epoch
    miss_vec = r + tau * v

    e1, e2 = _encounter_plane_basis(v)
    b = np.vstack([e1, e2])  # 2x3
    c_rel = c_p + c_s  # independent errors (doc 06)

    mean = b @ miss_vec
    cov = b @ c_rel @ b.T

    combined_radius = float(primary["hard_body_radius_m"]) + float(secondary["hard_body_radius_m"])
    return Projection(
        tca_offset_s=tau,
        miss_distance_m=float(np.linalg.norm(miss_vec)),
        combined_radius_m=combined_radius,
        mean_m=(float(mean[0]), float(mean[1])),
        covariance_m2=((float(cov[0, 0]), float(cov[0, 1])), (float(cov[1, 0]), float(cov[1, 1]))),
    )


def _is_isotropic(cov: np.ndarray) -> bool:
    return (
        abs(cov[0, 1]) <= _ISOTROPY_TOL
        and abs(cov[1, 0]) <= _ISOTROPY_TOL
        and abs(cov[0, 0] - cov[1, 1]) <= _ISOTROPY_TOL * max(1.0, abs(cov[0, 0]))
    )


def pc_isotropic(miss_distance: float, sigma: float, radius: float) -> float:
    """Isotropic 2D case via non-central chi-square (independent reference).

    P(hit) = ncx2.cdf((R/sigma)^2, df=2, nc=(miss/sigma)^2). At zero miss this
    reduces to the analytic 1 - exp(-R^2 / (2 sigma^2)) (doc 06)."""
    if sigma <= 0:
        raise ValueError("nonpositive_projected_covariance")
    return float(ncx2.cdf((radius / sigma) ** 2, df=2, nc=(miss_distance / sigma) ** 2))


def pc_general(mean: tuple[float, float], cov, radius: float) -> float:
    """General positive-definite 2D case via deterministic polar quadrature
    over the disk x^2 + y^2 <= R^2, including the radial Jacobian (doc 06)."""
    m = np.asarray(mean, dtype=float)
    s = np.asarray(cov, dtype=float)
    det = float(np.linalg.det(s))
    if det <= 0:
        raise ValueError("nonpositive_definite_projected_covariance")
    if np.linalg.cond(s) > 1e6:  # doc 06 conditioning limit
        raise ValueError("projected_condition_number_exceeded")
    s_inv = np.linalg.inv(s)
    norm = 1.0 / (2.0 * math.pi * math.sqrt(det))

    def integrand(rho: float, theta: float) -> float:
        p = np.array([rho * math.cos(theta), rho * math.sin(theta)])
        d = p - m
        return norm * math.exp(-0.5 * float(d @ s_inv @ d)) * rho

    value, _err = integrate.dblquad(integrand, 0.0, 2.0 * math.pi, 0.0, radius)
    return float(value)


def collision_probability(projection: Projection) -> float:
    """Dispatch: exact ncx2 for isotropic, polar quadrature otherwise."""
    cov = np.asarray(projection.covariance_m2, dtype=float)
    if _is_isotropic(cov):
        return pc_isotropic(projection.miss_distance_m, math.sqrt(cov[0, 0]), projection.combined_radius_m)
    return pc_general(projection.mean_m, cov, projection.combined_radius_m)


def smoke() -> dict:
    """M0 synthetic smoke calculation rendered by /capabilities and the UI.

    Zero-miss isotropic reference (doc 06/11): sigma=sqrt(1250)*sqrt(2) combined,
    R=10 -> expected 0.019801326693244702."""
    sigma = math.sqrt(1250.0 + 1250.0)
    pc = pc_isotropic(miss_distance=0.0, sigma=sigma, radius=10.0)
    return {"case": "zero_miss_isotropic", "sigma_combined_m": sigma, "radius_m": 10.0, "pc": pc}
