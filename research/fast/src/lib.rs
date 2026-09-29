//! CE-BRAIN 빠른 계산 핵심.
//!
//! 스파이크는 NWB처럼 평탄한 시각 배열 `times`와 단위별 끝 색인 `ends`로 받는다. 단위마다 시각은
//! 오름차순이어야 하고, 모든 칸은 반열린 구간 [시작, 끝)이다. 단위별로 나누어 GIL 밖에서 병렬로 센다.

use numpy::ndarray::{Array1, Array2, Array3};
use numpy::{IntoPyArray, PyArray1, PyArray2, PyArray3, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rayon::prelude::*;

type Times<'py> = PyReadonlyArray1<'py, f64>;
type Ends<'py> = PyReadonlyArray1<'py, i64>;

/// Split flat spike times into per-unit slices, checking the index and the order of every unit.
fn units<'a>(times: &'a [f64], ends: &[i64]) -> PyResult<Vec<&'a [f64]>> {
    let mut start = 0;
    let mut out = Vec::with_capacity(ends.len());
    for (i, &end) in ends.iter().enumerate() {
        let end = usize::try_from(end)
            .ok()
            .filter(|&e| e >= start && e <= times.len())
            .ok_or_else(|| PyValueError::new_err(format!("bad end index of unit {i}")))?;
        let unit = &times[start..end];
        if unit.windows(2).any(|w| !(w[0] <= w[1])) {
            return Err(PyValueError::new_err(format!("spike times of unit {i} are not sorted")));
        }
        out.push(unit);
        start = end;
    }
    Ok(out)
}

/// Number of spikes before time x.
fn before(unit: &[f64], x: f64) -> u32 {
    unit.partition_point(|&s| s < x) as u32
}

/// Spike counts (units × bins) in contiguous bins [edges[k], edges[k+1]).
#[pyfunction]
fn bin_counts<'py>(
    py: Python<'py>,
    times: Times<'py>,
    ends: Ends<'py>,
    edges: Times<'py>,
) -> PyResult<Bound<'py, PyArray2<u32>>> {
    let (times, ends, edges) = (times.as_slice()?, ends.as_slice()?, edges.as_slice()?);
    if edges.windows(2).any(|w| !(w[0] < w[1])) {
        return Err(PyValueError::new_err("edges must increase"));
    }
    let units = units(times, ends)?;
    let bins = edges.len().saturating_sub(1);
    let mut out = vec![0u32; units.len() * bins];
    if bins > 0 {
        py.detach(|| {
            out.par_chunks_mut(bins).zip(&units).for_each(|(row, unit)| {
                let mut k = 0;
                for &t in &unit[before(unit, edges[0]) as usize..] {
                    while k < bins && t >= edges[k + 1] {
                        k += 1;
                    }
                    if k == bins {
                        break;
                    }
                    row[k] += 1;
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((units.len(), bins), out).unwrap().into_pyarray(py))
}

/// Spike counts (units × windows) in arbitrary, possibly overlapping windows [starts[w], stops[w]).
#[pyfunction]
fn window_counts<'py>(
    py: Python<'py>,
    times: Times<'py>,
    ends: Ends<'py>,
    starts: Times<'py>,
    stops: Times<'py>,
) -> PyResult<Bound<'py, PyArray2<u32>>> {
    let (times, ends, starts, stops) =
        (times.as_slice()?, ends.as_slice()?, starts.as_slice()?, stops.as_slice()?);
    if starts.len() != stops.len() || starts.iter().zip(stops).any(|(a, b)| !(a <= b)) {
        return Err(PyValueError::new_err("windows need starts ≤ stops of equal length"));
    }
    let units = units(times, ends)?;
    let windows = starts.len();
    let mut out = vec![0u32; units.len() * windows];
    if windows > 0 {
        py.detach(|| {
            out.par_chunks_mut(windows).zip(&units).for_each(|(row, unit)| {
                for (c, (&a, &b)) in row.iter_mut().zip(starts.iter().zip(stops)) {
                    *c = before(unit, b) - before(unit, a);
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((units.len(), windows), out).unwrap().into_pyarray(py))
}

/// Cross-correlograms (a units × b units × 2·half+1): counts of b spikes at lag t_b − t_a, in bins of
/// `width` centred on zero lag. Passing the same units twice gives all pairs, with each unit's own
/// spikes in its zero-lag bin.
#[pyfunction]
fn ccg<'py>(
    py: Python<'py>,
    a_times: Times<'py>,
    a_ends: Ends<'py>,
    b_times: Times<'py>,
    b_ends: Ends<'py>,
    width: f64,
    half: usize,
) -> PyResult<Bound<'py, PyArray3<u32>>> {
    if !(width > 0.0) {
        return Err(PyValueError::new_err("width must be positive"));
    }
    let a = units(a_times.as_slice()?, a_ends.as_slice()?)?;
    let b = units(b_times.as_slice()?, b_ends.as_slice()?)?;
    let (bins, reach) = (2 * half + 1, (half as f64 + 0.5) * width);
    let mut out = vec![0u32; a.len() * b.len() * bins];
    if !b.is_empty() {
        py.detach(|| {
            out.par_chunks_mut(b.len() * bins).zip(&a).for_each(|(block, ua)| {
                for (row, ub) in block.chunks_mut(bins).zip(&b) {
                    let mut lo = 0;
                    for &t in ua.iter() {
                        while lo < ub.len() && ub[lo] < t - reach {
                            lo += 1;
                        }
                        for &s in ub[lo..].iter().take_while(|&&s| s < t + reach) {
                            row[(((s - t + reach) / width) as usize).min(bins - 1)] += 1;
                        }
                    }
                }
            })
        });
    }
    Ok(Array3::from_shape_vec((a.len(), b.len(), bins), out).unwrap().into_pyarray(py))
}

/// SplitMix64 with Box–Muller normals: one fixed stream per trajectory, so every parameter set sees the same noise.
struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    fn uniform(&mut self) -> f64 {
        ((self.next() >> 11) as f64 + 0.5) / (1u64 << 53) as f64
    }

    fn normal(&mut self) -> f64 {
        (-2.0 * self.uniform().ln()).sqrt() * (std::f64::consts::TAU * self.uniform()).cos()
    }
}

/// The common equation on a ring, one trajectory per event, from θ(0) = 0 and h(0) = 1:
///   dθ = −D ∂E/∂θ dt + √(2D) dW,   τ ḣ = −h + e^{iθ},
///   E = −A|h|·g(θ − arg h) − A_s·g(θ − θ_s),   g(x) = e^{β(cos x − 1)}.
/// Returns the circular-mean angle of θ over each window of `substeps` Euler steps (events × windows),
/// NaN past each event's length.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_trace<'py>(
    py: Python<'py>,
    heads: Times<'py>,
    lengths: Ends<'py>,
    windows: usize,
    d: f64,
    a: f64,
    tau: f64,
    a_s: f64,
    beta: f64,
    substeps: usize,
    seed: u64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let (heads, lengths) = (heads.as_slice()?, lengths.as_slice()?);
    if heads.len() != lengths.len() || substeps == 0 || !(d >= 0.0) || !(tau > 0.0) {
        return Err(PyValueError::new_err("need equal heads and lengths, substeps > 0, D ≥ 0, τ > 0"));
    }
    let dt = 1.0 / substeps as f64;
    let noise = (2.0 * d * dt).sqrt();
    let mut out = vec![f64::NAN; heads.len() * windows];
    if windows > 0 {
        py.detach(|| {
            out.par_chunks_mut(windows).enumerate().for_each(|(i, row)| {
                let mut rng = Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03));
                let length = (lengths[i].max(0) as usize).min(windows);
                let (sh, ch) = heads[i].sin_cos();
                let (mut th, mut hr, mut hi, mut s, mut c) = (0.0f64, 1.0f64, 0.0f64, 0.0f64, 1.0f64);
                for cell in row.iter_mut().take(length) {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for _ in 0..substeps {
                        // |h|·sin(θ − arg h) = s·hr − c·hi, cos(θ − arg h) = (c·hr + s·hi)/|h|: atan2·sin·cos 없이 같은 힘
                        let m = hr.hypot(hi);
                        let mut pull = if m > 0.0 { a * (s * hr - c * hi) * (beta * ((c * hr + s * hi) / m - 1.0)).exp() } else { 0.0 };
                        if a_s != 0.0 {
                            pull += a_s * (s * ch - c * sh) * (beta * (c * ch + s * sh - 1.0)).exp();
                        }
                        th += -d * beta * pull * dt + noise * rng.normal();
                        (s, c) = th.sin_cos();
                        hr += (c - hr) * dt / tau;
                        hi += (s - hi) * dt / tau;
                        sr += c;
                        si += s;
                    }
                    *cell = si.atan2(sr);
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((heads.len(), windows), out).unwrap().into_pyarray(py))
}

/// Standard normals from Box–Muller, both values of each pair used.
struct Normals {
    rng: Rng,
    spare: Option<f64>,
}

impl Normals {
    fn next(&mut self) -> f64 {
        if let Some(z) = self.spare.take() {
            return z;
        }
        let r = (-2.0 * self.rng.uniform().ln()).sqrt();
        let (s, c) = (std::f64::consts::TAU * self.rng.uniform()).sin_cos();
        self.spare = Some(r * s);
        r * c
    }
}

/// The same ring equation as `ring_trace` (no head input), integrated by local linearisation: each step solves
/// the Ornstein–Uhlenbeck process of the well linearised at θ exactly, so steep wells stay stable at large steps;
/// the trace takes the exact exponential step with e^{iθ} held. Instead of the windows it returns the sums behind
/// the observables, over all events: for each lag bin [edges[j], edges[j+1]) of window centres k + ½ the sum of
/// cos(θ_k − offset) and the window count, then for each lag d the sum of cos(θ_{k+d} − θ_k) and the pair count.
/// The window direction averages e^{iθ} at every `thin`-th step only (the observation's samples), so the integration
/// step and the number of samples per window can be set apart. `scheme` 0 is the local linearisation above; 1 is the
/// Leimkuhler–Matthews step θ += b(θ)dt + √(2D dt)(ξ_n + ξ_{n+1})/2, Euler's cost with a second-order stationary law.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_observe<'py>(
    py: Python<'py>,
    offsets: Times<'py>,
    lengths: Ends<'py>,
    d: f64,
    a: f64,
    tau: f64,
    beta: f64,
    substeps: usize,
    seed: u64,
    edges: Times<'py>,
    deltas: Ends<'py>,
    thin: usize,
    scheme: u8,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let (offsets, lengths, edges, deltas) = (offsets.as_slice()?, lengths.as_slice()?, edges.as_slice()?, deltas.as_slice()?);
    if offsets.len() != lengths.len() || substeps == 0 || thin == 0 || !(d >= 0.0) || !(tau > 0.0) || edges.len() < 2
        || deltas.iter().any(|&x| x < 1)
    {
        return Err(PyValueError::new_err("need equal offsets and lengths, substeps > 0, D ≥ 0, τ > 0, bins, lags ≥ 1"));
    }
    let (bins, lags) = (edges.len() - 1, deltas.len());
    let dt = 1.0 / substeps as f64;
    let keep = (-dt / tau).exp();
    let sums = py.detach(|| {
        (0..offsets.len())
            .into_par_iter()
            .map(|i| {
                let mut out = vec![0.0; 2 * bins + 2 * lags];
                let mut z = Normals { rng: Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03)), spare: None };
                let length = lengths[i].max(0) as usize;
                let (mut th, mut hr, mut hi, mut s, mut c) = (0.0f64, 1.0f64, 0.0f64, 0.0f64, 1.0f64);
                let mut unit: Vec<(f64, f64)> = Vec::with_capacity(length);
                let mut last = z.next();
                for k in 0..length {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for step in 0..substeps {
                        let m = hr.hypot(hi);
                        let (drift, rate) = if m > 0.0 && a > 0.0 {
                            let (cx, sx) = ((c * hr + s * hi) / m, (s * hr - c * hi) / m);
                            let well = d * beta * a * m * (beta * (cx - 1.0)).exp();
                            (-well * sx, well * (cx - beta * sx * sx))
                        } else {
                            (0.0, 0.0)
                        };
                        let x = rate * dt;
                        th += if scheme == 1 {
                            let fresh = z.next();
                            let step = drift * dt + (0.5 * d * dt).sqrt() * (last + fresh);
                            last = fresh;
                            step
                        } else if x.abs() > 1e-6 {
                            let e = (-x).exp();
                            drift / rate * (1.0 - e) + (d * (1.0 - e * e) / rate).sqrt() * z.next()
                        } else {
                            drift * dt + (2.0 * d * dt).sqrt() * z.next()
                        };
                        (s, c) = th.sin_cos();
                        hr = c + (hr - c) * keep;
                        hi = s + (hi - s) * keep;
                        if step % thin == thin - 1 {
                            sr += c;
                            si += s;
                        }
                    }
                    let n = sr.hypot(si);
                    let u = if n > 0.0 { (sr / n, si / n) } else { (1.0, 0.0) };
                    let centre = k as f64 + 0.5;
                    if let Some(j) = (0..bins).find(|&j| edges[j] <= centre && centre < edges[j + 1]) {
                        let (so, co) = offsets[i].sin_cos();
                        out[j] += u.0 * co + u.1 * so;
                        out[bins + j] += 1.0;
                    }
                    for (j, &lag) in deltas.iter().enumerate() {
                        if let Some(p) = k.checked_sub(lag as usize).map(|p| unit[p]) {
                            out[2 * bins + j] += u.0 * p.0 + u.1 * p.1;
                            out[2 * bins + lags + j] += 1.0;
                        }
                    }
                    unit.push(u);
                }
                out
            })
            .reduce(|| vec![0.0; 2 * bins + 2 * lags], |x, y| x.iter().zip(&y).map(|(p, q)| p + q).collect())
    });
    Ok(Array1::from(sums).into_pyarray(py))
}

/// The record-field equation (v3) on a ring, one trajectory per event, from θ(0) = 0 with the record gathered there:
///   dθ = −D ∂E/∂θ dt + √(2D) dW,   τ ḣ_k = −h_k + e^{ikθ} (k = 1..K, the record's Fourier coefficients),
///   E(θ) = −A Σ_k coef_k Re(h_k e^{−ikθ})   (coef_k = 2 I_k(β) e^{−β}: a gathered record gives the well e^{β(cos x − 1)}).
/// Leimkuhler–Matthews steps. Returns the circular-mean angle of θ over each window (events × windows), NaN past each length.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_field<'py>(
    py: Python<'py>,
    lengths: Ends<'py>,
    windows: usize,
    d: f64,
    a: f64,
    tau: f64,
    coef: Times<'py>,
    substeps: usize,
    seed: u64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let (lengths, coef) = (lengths.as_slice()?, coef.as_slice()?);
    if substeps == 0 || !(d >= 0.0) || !(tau > 0.0) || coef.is_empty() {
        return Err(PyValueError::new_err("need substeps > 0, D ≥ 0, τ > 0 and at least one harmonic"));
    }
    let harmonics = coef.len();
    let dt = 1.0 / substeps as f64;
    let keep = (-dt / tau).exp();
    let mut out = vec![f64::NAN; lengths.len() * windows];
    if windows > 0 {
        py.detach(|| {
            out.par_chunks_mut(windows).enumerate().for_each(|(i, row)| {
                let mut z = Normals { rng: Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03)), spare: None };
                let mut last = z.next();
                let length = (lengths[i].max(0) as usize).min(windows);
                let (mut th, mut s, mut c) = (0.0f64, 0.0f64, 1.0f64);
                let (mut hr, mut hi) = (vec![1.0f64; harmonics], vec![0.0f64; harmonics]);
                for cell in row.iter_mut().take(length) {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for _ in 0..substeps {
                        let (mut pr, mut pi, mut drift) = (c, s, 0.0);
                        for k in 0..harmonics {
                            drift += (k + 1) as f64 * coef[k] * (hi[k] * pr - hr[k] * pi); // k·coef_k·Im(h_k e^{−ikθ})
                            (pr, pi) = (pr * c - pi * s, pr * s + pi * c);
                        }
                        let fresh = z.next();
                        th += d * a * drift * dt + (0.5 * d * dt).sqrt() * (last + fresh);
                        last = fresh;
                        (s, c) = th.sin_cos();
                        let (mut pr, mut pi) = (c, s);
                        for k in 0..harmonics {
                            hr[k] = pr + (hr[k] - pr) * keep;
                            hi[k] = pi + (hi[k] - pi) * keep;
                            (pr, pi) = (pr * c - pi * s, pr * s + pi * c);
                        }
                        sr += c;
                        si += s;
                    }
                    *cell = si.atan2(sr);
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((lengths.len(), windows), out).unwrap().into_pyarray(py))
}

/// The ring equation with an internal angular-velocity drive (the direction term F in sleep), from θ(0) = 0, h(0) = 1:
///   dθ = (−D ∂E/∂θ + ω) dt + √(2D) dW,   τ_ω dω = −ω dt + v √(2τ_ω) dW′,   τ ḣ = −h + e^{iθ},   E = −A|h|·g(θ − arg h).
/// ω is an Ornstein–Uhlenbeck velocity with stationary SD v (exact step); θ takes Leimkuhler–Matthews steps.
/// Returns the circular-mean angle of θ over each window (events × windows), NaN past each event's length.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_sweep<'py>(
    py: Python<'py>,
    lengths: Ends<'py>,
    windows: usize,
    d: f64,
    a: f64,
    tau: f64,
    beta: f64,
    speed: f64,
    tau_w: f64,
    substeps: usize,
    seed: u64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let lengths = lengths.as_slice()?;
    if substeps == 0 || !(d >= 0.0) || !(tau > 0.0) || !(tau_w > 0.0) || !(speed >= 0.0) {
        return Err(PyValueError::new_err("need substeps > 0, D ≥ 0, τ > 0, τ_ω > 0, v ≥ 0"));
    }
    let dt = 1.0 / substeps as f64;
    let (keep, carry) = ((-dt / tau).exp(), (-dt / tau_w).exp());
    let kick = speed * (1.0 - carry * carry).sqrt();
    let mut out = vec![f64::NAN; lengths.len() * windows];
    if windows > 0 {
        py.detach(|| {
            out.par_chunks_mut(windows).enumerate().for_each(|(i, row)| {
                let mut z = Normals { rng: Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03)), spare: None };
                let mut last = z.next();
                let length = (lengths[i].max(0) as usize).min(windows);
                let (mut th, mut hr, mut hi, mut s, mut c) = (0.0f64, 1.0f64, 0.0f64, 0.0f64, 1.0f64);
                let mut w = speed * z.next();
                for cell in row.iter_mut().take(length) {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for _ in 0..substeps {
                        let m = hr.hypot(hi);
                        let pull = if m > 0.0 && a > 0.0 {
                            a * (s * hr - c * hi) * (beta * ((c * hr + s * hi) / m - 1.0)).exp()
                        } else {
                            0.0
                        };
                        let fresh = z.next();
                        th += (-d * beta * pull + w) * dt + (0.5 * d * dt).sqrt() * (last + fresh);
                        last = fresh;
                        w = w * carry + kick * z.next();
                        (s, c) = th.sin_cos();
                        hr = c + (hr - c) * keep;
                        hi = s + (hi - s) * keep;
                        sr += c;
                        si += s;
                    }
                    *cell = si.atan2(sr);
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((lengths.len(), windows), out).unwrap().into_pyarray(py))
}

/// `ring_trace` with a surprise gain on the record (C3-11): τ ḣ = (1 + λ·u)(e^{iθ} − h), u = 1 − g(θ − arg h), so the
/// record moves faster the farther the state sits outside its well (innovation-driven gain, as in a change-point Kalman
/// filter). u is taken before each step. λ = 0 gives `ring_trace` bit for bit.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_trace_gain<'py>(
    py: Python<'py>,
    heads: Times<'py>,
    lengths: Ends<'py>,
    windows: usize,
    d: f64,
    a: f64,
    tau: f64,
    a_s: f64,
    beta: f64,
    substeps: usize,
    seed: u64,
    lam: f64,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let (heads, lengths) = (heads.as_slice()?, lengths.as_slice()?);
    if heads.len() != lengths.len() || substeps == 0 || !(d >= 0.0) || !(tau > 0.0) || !(lam >= 0.0) {
        return Err(PyValueError::new_err("need equal heads and lengths, substeps > 0, D ≥ 0, τ > 0, λ ≥ 0"));
    }
    let dt = 1.0 / substeps as f64;
    let noise = (2.0 * d * dt).sqrt();
    let mut out = vec![f64::NAN; heads.len() * windows];
    if windows > 0 {
        py.detach(|| {
            out.par_chunks_mut(windows).enumerate().for_each(|(i, row)| {
                let mut rng = Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03));
                let length = (lengths[i].max(0) as usize).min(windows);
                let (sh, ch) = heads[i].sin_cos();
                let (mut th, mut hr, mut hi, mut s, mut c) = (0.0f64, 1.0f64, 0.0f64, 0.0f64, 1.0f64);
                for cell in row.iter_mut().take(length) {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for _ in 0..substeps {
                        let m = hr.hypot(hi);
                        let (mut pull, mut gain) = (0.0, 1.0);
                        if m > 0.0 {
                            let g = (beta * ((c * hr + s * hi) / m - 1.0)).exp();
                            pull = a * (s * hr - c * hi) * g;
                            gain = 1.0 + lam * (1.0 - g);
                        }
                        if a_s != 0.0 {
                            pull += a_s * (s * ch - c * sh) * (beta * (c * ch + s * sh - 1.0)).exp();
                        }
                        th += -d * beta * pull * dt + noise * rng.normal();
                        (s, c) = th.sin_cos();
                        hr += (c - hr) * dt * gain / tau;
                        hi += (s - hi) * dt * gain / tau;
                        sr += c;
                        si += s;
                    }
                    *cell = si.atan2(sr);
                }
            })
        });
    }
    Ok(Array2::from_shape_vec((heads.len(), windows), out).unwrap().into_pyarray(py))
}

/// `ring_observe` with the surprise gain of `ring_trace_gain`: the record's exact exponential step uses the rate
/// (1 + λ·u)/τ, u = 1 − g(θ − arg h) taken before each step. λ = 0 gives `ring_observe` bit for bit.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn ring_observe_gain<'py>(
    py: Python<'py>,
    offsets: Times<'py>,
    lengths: Ends<'py>,
    d: f64,
    a: f64,
    tau: f64,
    beta: f64,
    substeps: usize,
    seed: u64,
    edges: Times<'py>,
    deltas: Ends<'py>,
    thin: usize,
    scheme: u8,
    lam: f64,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let (offsets, lengths, edges, deltas) = (offsets.as_slice()?, lengths.as_slice()?, edges.as_slice()?, deltas.as_slice()?);
    if offsets.len() != lengths.len() || substeps == 0 || thin == 0 || !(d >= 0.0) || !(tau > 0.0) || edges.len() < 2
        || deltas.iter().any(|&x| x < 1) || !(lam >= 0.0)
    {
        return Err(PyValueError::new_err("need equal offsets and lengths, substeps > 0, D ≥ 0, τ > 0, bins, lags ≥ 1, λ ≥ 0"));
    }
    let (bins, lags) = (edges.len() - 1, deltas.len());
    let dt = 1.0 / substeps as f64;
    let keep = (-dt / tau).exp();
    let sums = py.detach(|| {
        (0..offsets.len())
            .into_par_iter()
            .map(|i| {
                let mut out = vec![0.0; 2 * bins + 2 * lags];
                let mut z = Normals { rng: Rng(seed ^ (i as u64 + 1).wrapping_mul(0xD1B5_4A32_D192_ED03)), spare: None };
                let length = lengths[i].max(0) as usize;
                let (mut th, mut hr, mut hi, mut s, mut c) = (0.0f64, 1.0f64, 0.0f64, 0.0f64, 1.0f64);
                let mut unit: Vec<(f64, f64)> = Vec::with_capacity(length);
                let mut last = z.next();
                for k in 0..length {
                    let (mut sr, mut si) = (0.0, 0.0);
                    for step in 0..substeps {
                        let m = hr.hypot(hi);
                        let (mut drift, mut rate, mut g) = (0.0, 0.0, 1.0);
                        if m > 0.0 {
                            let (cx, sx) = ((c * hr + s * hi) / m, (s * hr - c * hi) / m);
                            g = (beta * (cx - 1.0)).exp();
                            if a > 0.0 {
                                let well = d * beta * a * m * g;
                                (drift, rate) = (-well * sx, well * (cx - beta * sx * sx));
                            }
                        }
                        let x = rate * dt;
                        th += if scheme == 1 {
                            let fresh = z.next();
                            let step = drift * dt + (0.5 * d * dt).sqrt() * (last + fresh);
                            last = fresh;
                            step
                        } else if x.abs() > 1e-6 {
                            let e = (-x).exp();
                            drift / rate * (1.0 - e) + (d * (1.0 - e * e) / rate).sqrt() * z.next()
                        } else {
                            drift * dt + (2.0 * d * dt).sqrt() * z.next()
                        };
                        (s, c) = th.sin_cos();
                        let kept = if lam == 0.0 { keep } else { (-dt * (1.0 + lam * (1.0 - g)) / tau).exp() };
                        hr = c + (hr - c) * kept;
                        hi = s + (hi - s) * kept;
                        if step % thin == thin - 1 {
                            sr += c;
                            si += s;
                        }
                    }
                    let n = sr.hypot(si);
                    let u = if n > 0.0 { (sr / n, si / n) } else { (1.0, 0.0) };
                    let centre = k as f64 + 0.5;
                    if let Some(j) = (0..bins).find(|&j| edges[j] <= centre && centre < edges[j + 1]) {
                        let (so, co) = offsets[i].sin_cos();
                        out[j] += u.0 * co + u.1 * so;
                        out[bins + j] += 1.0;
                    }
                    for (j, &lag) in deltas.iter().enumerate() {
                        if let Some(p) = k.checked_sub(lag as usize).map(|p| unit[p]) {
                            out[2 * bins + j] += u.0 * p.0 + u.1 * p.1;
                            out[2 * bins + lags + j] += 1.0;
                        }
                    }
                    unit.push(u);
                }
                out
            })
            .reduce(|| vec![0.0; 2 * bins + 2 * lags], |x, y| x.iter().zip(&y).map(|(p, q)| p + q).collect())
    });
    Ok(Array1::from(sums).into_pyarray(py))
}

#[pymodule]
fn cefast(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ring_trace_gain, m)?)?;
    m.add_function(wrap_pyfunction!(ring_observe_gain, m)?)?;
    m.add_function(wrap_pyfunction!(ring_sweep, m)?)?;
    m.add_function(wrap_pyfunction!(ring_field, m)?)?;
    m.add_function(wrap_pyfunction!(bin_counts, m)?)?;
    m.add_function(wrap_pyfunction!(window_counts, m)?)?;
    m.add_function(wrap_pyfunction!(ccg, m)?)?;
    m.add_function(wrap_pyfunction!(ring_trace, m)?)?;
    m.add_function(wrap_pyfunction!(ring_observe, m)?)?;
    Ok(())
}
