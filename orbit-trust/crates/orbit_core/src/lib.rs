//! Deterministic encounter math core (handoff doc 06), exposed to Python via PyO3.
//!
//! M0 scope: one synthetic smoke calculation (isotropic zero-miss / general
//! isotropic Pc) so the native wheel path can be proven end to end. The full
//! projection + polar-quadrature + Rayon pair batches land in M2/M3. Per doc 12
//! this core is validated against the *independent* Python oracle
//! (orbit_trust.numerics), never used as its own oracle.

use pyo3::prelude::*;

/// Isotropic 2D collision probability via the closed form for a circular
/// integration region and isotropic covariance:
///   P = 1 - exp(-R^2 / (2 sigma^2))            (zero miss)
/// General isotropic uses a Marcum-Q / series; M0 ships the zero-miss form as
/// the smoke value and defers the full series to M2.
#[pyfunction]
fn pc_zero_miss_isotropic(sigma: f64, radius: f64) -> PyResult<f64> {
    if sigma <= 0.0 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "nonpositive_projected_covariance",
        ));
    }
    Ok(1.0 - (-(radius * radius) / (2.0 * sigma * sigma)).exp())
}

#[pymodule]
fn orbit_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pc_zero_miss_isotropic, m)?)?;
    m.add("__doc__", "ORBIT-TRUST deterministic encounter math core (M0 smoke).")?;
    Ok(())
}
