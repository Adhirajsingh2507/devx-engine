//! Deterministic short-linear-encounter math core (handoff doc 06), exposed to
//! Python via PyO3. Production path for orbit_trust.numerics; validated against
//! that independent Python oracle (doc 12), never used as its own oracle.
//!
//! Pc uses Gauss-Legendre quadrature in the radial direction and the periodic
//! trapezoid rule in the angular direction (spectrally accurate for the smooth
//! 2*pi-periodic integrand), with the doc-06 two-grid convergence gate
//! (64x128 vs 128x256, tol max(1e-12, 1e-7*Pc); 256x512 fallback; else
//! numerical_nonconvergence). Nodes are computed at runtime (Newton on the
//! Legendre polynomial), not hand-entered constants.

use pyo3::prelude::*;
use rayon::prelude::*;
use std::f64::consts::PI;

const MIN_REL_SPEED: f64 = 1.0;

// --- small vector helpers on [f64; 3] --------------------------------------
fn sub(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [a[0] - b[0], a[1] - b[1], a[2] - b[2]]
}
fn dot(a: [f64; 3], b: [f64; 3]) -> f64 {
    a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
}
fn cross(a: [f64; 3], b: [f64; 3]) -> [f64; 3] {
    [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
}
fn norm3(a: [f64; 3]) -> f64 {
    dot(a, a).sqrt()
}
fn scale(a: [f64; 3], s: f64) -> [f64; 3] {
    [a[0] * s, a[1] * s, a[2] * s]
}

// --- Gauss-Legendre nodes/weights on [-1, 1] -------------------------------
fn legendre(n: usize, x: f64) -> (f64, f64) {
    // returns (P_n(x), P_n'(x)) via the recurrence
    let mut p0 = 1.0;
    let mut p1 = x;
    if n == 0 {
        return (1.0, 0.0);
    }
    for k in 2..=n {
        let kf = k as f64;
        let pk = ((2.0 * kf - 1.0) * x * p1 - (kf - 1.0) * p0) / kf;
        p0 = p1;
        p1 = pk;
    }
    let dp = n as f64 * (x * p1 - p0) / (x * x - 1.0);
    (p1, dp)
}

fn gauss_legendre(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut nodes = vec![0.0; n];
    let mut weights = vec![0.0; n];
    let m = (n + 1) / 2;
    for i in 0..m {
        let mut xi = (PI * (i as f64 + 0.75) / (n as f64 + 0.5)).cos();
        for _ in 0..100 {
            let (p, dp) = legendre(n, xi);
            let dx = -p / dp;
            xi += dx;
            if dx.abs() < 1e-15 {
                break;
            }
        }
        let (_, dp) = legendre(n, xi);
        let w = 2.0 / ((1.0 - xi * xi) * dp * dp);
        nodes[i] = -xi;
        nodes[n - 1 - i] = xi;
        weights[i] = w;
        weights[n - 1 - i] = w;
    }
    (nodes, weights)
}

// --- 2D collision probability over the disk x^2+y^2 <= R^2 ------------------
fn pc_grid(mx: f64, my: f64, sxx: f64, sxy: f64, syy: f64, radius: f64, nr: usize, nth: usize) -> f64 {
    let det = sxx * syy - sxy * sxy;
    let norm = 1.0 / (2.0 * PI * det.sqrt());
    let (rn, rw) = gauss_legendre(nr);
    let dth = 2.0 * PI / nth as f64;
    let mut total = 0.0;
    for k in 0..nr {
        // map GL node from [-1,1] to [0, R]; radial weight carries R/2 Jacobian
        let rho = radius * (rn[k] + 1.0) / 2.0;
        let wr = rw[k] * radius / 2.0;
        let mut ring = 0.0;
        for j in 0..nth {
            let theta = j as f64 * dth;
            let dx = rho * theta.cos() - mx;
            let dy = rho * theta.sin() - my;
            let quad = (syy * dx * dx - 2.0 * sxy * dx * dy + sxx * dy * dy) / det;
            ring += (-0.5 * quad).exp();
        }
        ring *= dth; // periodic trapezoid weight
        total += wr * ring * rho * norm; // rho is the polar Jacobian
    }
    total
}

fn pc_2d_inner(mx: f64, my: f64, sxx: f64, sxy: f64, syy: f64, radius: f64) -> Result<f64, &'static str> {
    let det = sxx * syy - sxy * sxy;
    if det <= 0.0 {
        return Err("nonpositive_definite_projected_covariance");
    }
    let pc1 = pc_grid(mx, my, sxx, sxy, syy, radius, 64, 128);
    let pc2 = pc_grid(mx, my, sxx, sxy, syy, radius, 128, 256);
    if (pc1 - pc2).abs() <= f64::max(1e-12, 1e-7 * pc2.abs()) {
        return Ok(pc2);
    }
    let pc3 = pc_grid(mx, my, sxx, sxy, syy, radius, 256, 512);
    if (pc2 - pc3).abs() <= f64::max(1e-12, 1e-7 * pc3.abs()) {
        return Ok(pc3);
    }
    Err("numerical_nonconvergence")
}

// --- full projection + Pc for one pair -------------------------------------
#[allow(clippy::too_many_arguments)]
fn project_inner(
    pa: [f64; 3], va: [f64; 3], ca: [[f64; 3]; 3],
    pb: [f64; 3], vb: [f64; 3], cb: [[f64; 3]; 3],
    ra: f64, rb: f64, start: f64, end: f64,
) -> Result<(f64, f64, f64), &'static str> {
    let r = sub(pb, pa);
    let v = sub(vb, va);
    let speed = norm3(v);
    if speed < MIN_REL_SPEED {
        return Err("relative_speed_below_supported_minimum");
    }
    let n = scale(v, 1.0 / speed);
    // Cartesian axis least aligned with n (ties x<y<z)
    let mut axis_idx = 0;
    for i in 1..3 {
        if n[i].abs() < n[axis_idx].abs() {
            axis_idx = i;
        }
    }
    let mut axis = [0.0; 3];
    axis[axis_idx] = 1.0;
    let mut e1 = cross(axis, n);
    e1 = scale(e1, 1.0 / norm3(e1));
    let e2 = cross(n, e1);

    let tau = -dot(r, v) / dot(v, v);
    if tau < start || tau > end {
        return Err("tca_outside_supported_interval");
    }
    let miss_vec = [r[0] + tau * v[0], r[1] + tau * v[1], r[2] + tau * v[2]];
    let miss = norm3(miss_vec);

    // combined covariance C = ca + cb (independent errors)
    let mut c = [[0.0; 3]; 3];
    for i in 0..3 {
        for j in 0..3 {
            c[i][j] = ca[i][j] + cb[i][j];
        }
    }
    // projected mean and 2x2 covariance: m = B x miss, S = B C B^T, B rows e1,e2
    let mx = dot(e1, miss_vec);
    let my = dot(e2, miss_vec);
    let ce1 = mat_vec(c, e1);
    let ce2 = mat_vec(c, e2);
    let sxx = dot(e1, ce1);
    let sxy = dot(e1, ce2);
    let syy = dot(e2, ce2);

    let pc = pc_2d_inner(mx, my, sxx, sxy, syy, ra + rb)?;
    Ok((tau, miss, pc))
}

fn mat_vec(m: [[f64; 3]; 3], v: [f64; 3]) -> [f64; 3] {
    [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]
}

fn as3(v: &[f64]) -> Result<[f64; 3], &'static str> {
    if v.len() != 3 {
        return Err("expected_length_3_vector");
    }
    Ok([v[0], v[1], v[2]])
}
fn as33(v: &[f64]) -> Result<[[f64; 3]; 3], &'static str> {
    if v.len() != 9 {
        return Err("expected_length_9_covariance");
    }
    Ok([[v[0], v[1], v[2]], [v[3], v[4], v[5]], [v[6], v[7], v[8]]])
}

fn err(reason: &str) -> PyErr {
    pyo3::exceptions::PyValueError::new_err(reason.to_string())
}

// --- Python surface --------------------------------------------------------
/// 2D collision probability over the disk of `radius`, mean (mx,my) and
/// covariance (sxx, sxy, syy). Raises numerical_nonconvergence if the two-grid
/// gate is not met.
#[pyfunction]
fn pc_2d(mx: f64, my: f64, sxx: f64, sxy: f64, syy: f64, radius: f64) -> PyResult<f64> {
    pc_2d_inner(mx, my, sxx, sxy, syy, radius).map_err(err)
}

/// Project two object states (position_m, velocity_m_s, row-major 3x3
/// covariance, hard-body radius) and return (tca_offset_s, miss_distance_m, pc).
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn project_and_pc(
    pa: Vec<f64>, va: Vec<f64>, ca: Vec<f64>,
    pb: Vec<f64>, vb: Vec<f64>, cb: Vec<f64>,
    ra: f64, rb: f64, interval_start: f64, interval_end: f64,
) -> PyResult<(f64, f64, f64)> {
    let inner = (|| {
        Ok(project_inner(
            as3(&pa)?, as3(&va)?, as33(&ca)?, as3(&pb)?, as3(&vb)?, as33(&cb)?,
            ra, rb, interval_start, interval_end,
        )?)
    })();
    inner.map_err(|e: &'static str| err(e))
}

/// Parallel batch of 2D Pc problems (Rayon). Each problem is
/// [mx, my, sxx, sxy, syy, radius]. Used for independent fleet pair jobs.
#[pyfunction]
fn pc_2d_batch(py: Python<'_>, problems: Vec<Vec<f64>>) -> PyResult<Vec<f64>> {
    py.allow_threads(|| {
        problems
            .par_iter()
            .map(|p| {
                if p.len() != 6 {
                    return Err("expected_length_6_problem");
                }
                pc_2d_inner(p[0], p[1], p[2], p[3], p[4], p[5])
            })
            .collect::<Result<Vec<f64>, &'static str>>()
    })
    .map_err(err)
}

#[pymodule]
fn orbit_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pc_2d, m)?)?;
    m.add_function(wrap_pyfunction!(project_and_pc, m)?)?;
    m.add_function(wrap_pyfunction!(pc_2d_batch, m)?)?;
    m.add("__doc__", "ORBIT-TRUST deterministic encounter math core.")?;
    Ok(())
}
