//! Binary64 witness for the deterministic hybrid extension of (21.53).
//!
//! The fixture has one transversal guard crossing, a parameter-dependent
//! reset, and a terminal Gaussian output family.  Closed-form event-time,
//! saltation, mixed-tangent, and pullback-metric derivatives are checked
//! against central differences of the exact hybrid return map.  This is a
//! formal synthetic witness, not a theorem for hybrid RFDEs and not evidence
//! about neural tissue.

use std::env;
use std::fmt::Write as _;
use std::fs;
use std::path::PathBuf;

type Vector = [f64; 2];
type Matrix = [[f64; 2]; 2];

const Z_STEPS: [f64; 3] = [4.0e-4, 2.0e-4, 1.0e-4];
const THETA_STEPS: [f64; 3] = [4.0e-3, 2.0e-3, 1.0e-3];
const TRANSVERSALITY_MIN: f64 = 1.0e-8;
const EVENT_ENDPOINT_MARGIN_S: f64 = 0.25;
const J_TOLERANCE: f64 = 1.0e-8;
const EVENT_TIME_TOLERANCE: f64 = 2.0e-6;
const S_TOLERANCE: f64 = 2.0e-5;
const K_TOLERANCE: f64 = 2.0e-5;
const METRIC_TOLERANCE: f64 = 5.0e-5;
const REFINEMENT_RATIO_MAX: f64 = 0.55;
const REFINEMENT_ERROR_FLOOR: f64 = 1.0e-8;
const SYMMETRY_TOLERANCE: f64 = 1.0e-12;
const COVARIANCE_TOLERANCE: f64 = 1.0e-12;
const IDENTITY_TOLERANCE: f64 = 1.0e-12;
const MIN_ABS_DETERMINANT_J: f64 = 0.1;
const MIN_EIGENVALUE: f64 = 0.1;
const NONDEGENERACY_MIN: f64 = 1.0e-3;
const ABLATION_ERROR_MIN: f64 = 1.0e-3;
const ABLATION_RATIO_MIN: f64 = 100.0;

#[derive(Clone, Copy)]
struct Fixture {
    z: Vector,
    horizon_s: f64,
    theta: f64,
    f_pre_s_inv: Vector,
    f_post_s_inv: Vector,
    guard_n0: Vector,
    guard_n1: Vector,
    guard_c: f64,
    guard_q: f64,
    reset_a0: Matrix,
    reset_a1: Matrix,
    reset_b0: Vector,
    reset_r: Vector,
    output_sigma: Vector,
    output_gamma: Vector,
    output_rho: Vector,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum StopCode {
    GrazingOrNontransverse,
    EventWordChange,
}

impl StopCode {
    fn as_str(self) -> &'static str {
        match self {
            Self::GrazingOrNontransverse => "GRAZING_OR_NONTRANSVERSE_STOP",
            Self::EventWordChange => "EVENT_WORD_CHANGE_STOP",
        }
    }
}

#[derive(Clone, Copy)]
struct FlowResult {
    event_time_s: f64,
    denominator_s_inv: f64,
    normalized_transversality: f64,
    x_minus: Vector,
    phi_h: Vector,
}

#[derive(Clone, Copy)]
struct Analytic {
    flow: FlowResult,
    event_time_theta_s: f64,
    event_time_z_s: Vector,
    guard_theta: f64,
    saltation: Matrix,
    saltation_correction: Matrix,
    affine_jump: Vector,
    reset_sensitivity: Vector,
    event_time_sensitivity: Vector,
    state_sensitivity: Vector,
    mixed_jacobian: Matrix,
    terminal_fisher: Matrix,
    d1_fisher: Matrix,
    d2_fisher: Matrix,
    pullback_metric: Matrix,
    tangent_term: Matrix,
    d1_term: Matrix,
    d2_term: Matrix,
    metric_derivative: Matrix,
}

#[derive(Clone, Copy)]
struct LevelResult {
    z_step: f64,
    theta_step: f64,
    event_time_error: f64,
    jacobian_error: f64,
    state_sensitivity_error: f64,
    mixed_jacobian_error: f64,
    metric_derivative_error: f64,
    metric_derivative_fd: Matrix,
}

struct Report {
    base: Analytic,
    levels: [LevelResult; 3],
    refinement_ratios: [f64; 4],
    determinant_j: f64,
    minimum_eigenvalue_fisher: f64,
    minimum_eigenvalue_metric: f64,
    symmetry_error: f64,
    affine_jump_identity_error: f64,
    coordinate_saltation_error: f64,
    coordinate_mixed_error: f64,
    coordinate_metric_error: f64,
    coordinate_derivative_error: f64,
    guard_scale_saltation_error: f64,
    guard_scale_affine_error: f64,
    guard_scale_mixed_error: f64,
    guard_scale_derivative_error: f64,
    nondegeneracy_norms: [f64; 5],
    ablation_errors: [f64; 6],
    grazing_status: &'static str,
    grazing_code: &'static str,
    event_word_status: &'static str,
    event_word_code: &'static str,
    fixture_fingerprint: u64,
}

fn fixture() -> Fixture {
    Fixture {
        z: [-0.35, 0.20],
        horizon_s: 2.0,
        theta: 0.0,
        f_pre_s_inv: [1.0, 0.4],
        f_post_s_inv: [-0.3, 0.8],
        guard_n0: [1.0, -0.25],
        guard_n1: [0.2, 0.3],
        guard_c: 0.4,
        guard_q: 0.15,
        reset_a0: [[0.8, 0.2], [-0.1, 1.1]],
        reset_a1: [[0.12, -0.08], [0.05, 0.09]],
        reset_b0: [0.1, -0.05],
        reset_r: [0.18, -0.08],
        output_sigma: [0.7, 1.1],
        output_gamma: [0.3, -0.2],
        output_rho: [0.25, -0.15],
    }
}

fn v_add(a: Vector, b: Vector) -> Vector {
    [a[0] + b[0], a[1] + b[1]]
}

fn v_sub(a: Vector, b: Vector) -> Vector {
    [a[0] - b[0], a[1] - b[1]]
}

fn v_scale(a: Vector, scale: f64) -> Vector {
    [scale * a[0], scale * a[1]]
}

fn dot(a: Vector, b: Vector) -> f64 {
    a[0] * b[0] + a[1] * b[1]
}

fn vector_norm(a: Vector) -> f64 {
    dot(a, a).sqrt()
}

fn m_add(a: Matrix, b: Matrix) -> Matrix {
    [
        [a[0][0] + b[0][0], a[0][1] + b[0][1]],
        [a[1][0] + b[1][0], a[1][1] + b[1][1]],
    ]
}

fn m_sub(a: Matrix, b: Matrix) -> Matrix {
    [
        [a[0][0] - b[0][0], a[0][1] - b[0][1]],
        [a[1][0] - b[1][0], a[1][1] - b[1][1]],
    ]
}

fn m_scale(a: Matrix, scale: f64) -> Matrix {
    [
        [scale * a[0][0], scale * a[0][1]],
        [scale * a[1][0], scale * a[1][1]],
    ]
}

fn transpose(a: Matrix) -> Matrix {
    [[a[0][0], a[1][0]], [a[0][1], a[1][1]]]
}

fn m_mul(a: Matrix, b: Matrix) -> Matrix {
    [
        [
            a[0][0] * b[0][0] + a[0][1] * b[1][0],
            a[0][0] * b[0][1] + a[0][1] * b[1][1],
        ],
        [
            a[1][0] * b[0][0] + a[1][1] * b[1][0],
            a[1][0] * b[0][1] + a[1][1] * b[1][1],
        ],
    ]
}

fn m_vec(a: Matrix, x: Vector) -> Vector {
    [
        a[0][0] * x[0] + a[0][1] * x[1],
        a[1][0] * x[0] + a[1][1] * x[1],
    ]
}

fn outer(a: Vector, b: Vector) -> Matrix {
    [[a[0] * b[0], a[0] * b[1]], [a[1] * b[0], a[1] * b[1]]]
}

fn matrix_norm(a: Matrix) -> f64 {
    (a[0][0] * a[0][0] + a[0][1] * a[0][1] + a[1][0] * a[1][0] + a[1][1] * a[1][1]).sqrt()
}

fn determinant(a: Matrix) -> f64 {
    a[0][0] * a[1][1] - a[0][1] * a[1][0]
}

fn inverse(a: Matrix) -> Matrix {
    let d = determinant(a);
    [[a[1][1] / d, -a[0][1] / d], [-a[1][0] / d, a[0][0] / d]]
}

fn symmetric_eigenvalues(a: Matrix) -> [f64; 2] {
    let center = 0.5 * (a[0][0] + a[1][1]);
    let radius = ((0.5 * (a[0][0] - a[1][1])).powi(2) + a[0][1] * a[1][0]).sqrt();
    [center - radius, center + radius]
}

fn congruence(a: Matrix, tensor: Matrix) -> Matrix {
    m_mul(transpose(a), m_mul(tensor, a))
}

fn scaled_matrix_error(value: Matrix, reference: Matrix) -> f64 {
    matrix_norm(m_sub(value, reference)) / matrix_norm(reference).max(1.0)
}

fn scaled_vector_error(value: Vector, reference: Vector) -> f64 {
    vector_norm(v_sub(value, reference)) / vector_norm(reference).max(1.0)
}

fn scaled_scalar_error(value: f64, reference: f64) -> f64 {
    (value - reference).abs() / reference.abs().max(1.0)
}

fn parameterized_guard(f: Fixture, theta: f64) -> Vector {
    v_add(f.guard_n0, v_scale(f.guard_n1, theta))
}

fn parameterized_reset_matrix(f: Fixture, theta: f64) -> Matrix {
    m_add(f.reset_a0, m_scale(f.reset_a1, theta))
}

fn parameterized_reset_offset(f: Fixture, theta: f64) -> Vector {
    v_add(f.reset_b0, v_scale(f.reset_r, theta))
}

fn hybrid_flow(f: Fixture, z: Vector, theta: f64) -> Result<FlowResult, StopCode> {
    let n = parameterized_guard(f, theta);
    let denominator = dot(n, f.f_pre_s_inv);
    let normalized = denominator.abs() / (vector_norm(n) * vector_norm(f.f_pre_s_inv));
    if !denominator.is_finite() || !normalized.is_finite() || normalized <= TRANSVERSALITY_MIN {
        return Err(StopCode::GrazingOrNontransverse);
    }
    let event_time = (f.guard_c + f.guard_q * theta - dot(n, z)) / denominator;
    if !event_time.is_finite()
        || event_time <= EVENT_ENDPOINT_MARGIN_S
        || event_time >= f.horizon_s - EVENT_ENDPOINT_MARGIN_S
    {
        return Err(StopCode::EventWordChange);
    }
    let x_minus = v_add(z, v_scale(f.f_pre_s_inv, event_time));
    let a = parameterized_reset_matrix(f, theta);
    let b = parameterized_reset_offset(f, theta);
    let x_plus = v_add(m_vec(a, x_minus), b);
    let phi_h = v_add(x_plus, v_scale(f.f_post_s_inv, f.horizon_s - event_time));
    Ok(FlowResult {
        event_time_s: event_time,
        denominator_s_inv: denominator,
        normalized_transversality: normalized,
        x_minus,
        phi_h,
    })
}

fn fisher(f: Fixture, phi: Vector, theta: f64) -> Matrix {
    // Independent Gaussian outputs with fixed sigma and
    // mu_i=exp(rho_i*theta)*(phi_i+0.5*gamma_i*phi_i^2) give this diagonal
    // state Fisher field.  The finite-difference side evaluates this field at
    // the exact terminal state and never calls the analytic sensitivity path.
    let mut diagonal = [0.0; 2];
    for i in 0..2 {
        let slope = 1.0 + f.output_gamma[i] * phi[i];
        diagonal[i] =
            (2.0 * f.output_rho[i] * theta).exp() * slope * slope / f.output_sigma[i].powi(2);
    }
    [[diagonal[0], 0.0], [0.0, diagonal[1]]]
}

fn fisher_derivatives(
    f: Fixture,
    phi: Vector,
    theta: f64,
    state_sensitivity: Vector,
) -> (Matrix, Matrix, Matrix) {
    let g = fisher(f, phi, theta);
    let mut d1 = [[0.0; 2]; 2];
    let mut d2 = [[0.0; 2]; 2];
    for i in 0..2 {
        let exponential = (2.0 * f.output_rho[i] * theta).exp();
        let slope = 1.0 + f.output_gamma[i] * phi[i];
        d1[i][i] = 2.0 * exponential * slope * f.output_gamma[i] * state_sensitivity[i]
            / f.output_sigma[i].powi(2);
        d2[i][i] = 2.0 * f.output_rho[i] * g[i][i];
    }
    (g, d1, d2)
}

fn metric_derivative_terms(
    j: Matrix,
    k: Matrix,
    g: Matrix,
    d1: Matrix,
    d2: Matrix,
) -> (Matrix, Matrix, Matrix, Matrix) {
    let tangent = m_add(
        m_mul(transpose(k), m_mul(g, j)),
        m_mul(transpose(j), m_mul(g, k)),
    );
    let d1_term = congruence(j, d1);
    let d2_term = congruence(j, d2);
    let full = m_add(tangent, m_add(d1_term, d2_term));
    (tangent, d1_term, d2_term, full)
}

fn analytic(f: Fixture, z: Vector, theta: f64) -> Result<Analytic, StopCode> {
    let flow = hybrid_flow(f, z, theta)?;
    let n = parameterized_guard(f, theta);
    let a = parameterized_reset_matrix(f, theta);
    let denominator = flow.denominator_s_inv;
    let w = v_sub(f.f_post_s_inv, m_vec(a, f.f_pre_s_inv));
    let saltation_correction = m_scale(outer(w, n), 1.0 / denominator);
    let saltation = m_add(a, saltation_correction);
    let event_time_theta = (f.guard_q - dot(f.guard_n1, flow.x_minus)) / denominator;
    let event_time_z = v_scale(n, -1.0 / denominator);
    let guard_theta = dot(f.guard_n1, flow.x_minus) - f.guard_q;
    let reset_sensitivity = v_add(m_vec(f.reset_a1, flow.x_minus), f.reset_r);
    let event_time_sensitivity = v_scale(
        v_sub(m_vec(a, f.f_pre_s_inv), f.f_post_s_inv),
        event_time_theta,
    );
    let state_sensitivity = v_add(reset_sensitivity, event_time_sensitivity);
    let affine_jump = v_add(reset_sensitivity, v_scale(w, guard_theta / denominator));
    let w_theta = v_scale(m_vec(f.reset_a1, f.f_pre_s_inv), -1.0);
    let denominator_theta = dot(f.guard_n1, f.f_pre_s_inv);
    let mixed_jacobian = m_add(
        f.reset_a1,
        m_sub(
            m_scale(
                m_add(outer(w_theta, n), outer(w, f.guard_n1)),
                1.0 / denominator,
            ),
            m_scale(outer(w, n), denominator_theta / denominator.powi(2)),
        ),
    );
    let (terminal_fisher, d1_fisher, d2_fisher) =
        fisher_derivatives(f, flow.phi_h, theta, state_sensitivity);
    let pullback_metric = congruence(saltation, terminal_fisher);
    let (tangent_term, d1_term, d2_term, metric_derivative) = metric_derivative_terms(
        saltation,
        mixed_jacobian,
        terminal_fisher,
        d1_fisher,
        d2_fisher,
    );
    Ok(Analytic {
        flow,
        event_time_theta_s: event_time_theta,
        event_time_z_s: event_time_z,
        guard_theta,
        saltation,
        saltation_correction,
        affine_jump,
        reset_sensitivity,
        event_time_sensitivity,
        state_sensitivity,
        mixed_jacobian,
        terminal_fisher,
        d1_fisher,
        d2_fisher,
        pullback_metric,
        tangent_term,
        d1_term,
        d2_term,
        metric_derivative,
    })
}

fn finite_difference_jacobian(
    f: Fixture,
    z: Vector,
    theta: f64,
    step: f64,
) -> Result<Matrix, StopCode> {
    let mut result = [[0.0; 2]; 2];
    for column in 0..2 {
        let mut plus = z;
        let mut minus = z;
        plus[column] += step;
        minus[column] -= step;
        let y_plus = hybrid_flow(f, plus, theta)?.phi_h;
        let y_minus = hybrid_flow(f, minus, theta)?.phi_h;
        let derivative = v_scale(v_sub(y_plus, y_minus), 0.5 / step);
        result[0][column] = derivative[0];
        result[1][column] = derivative[1];
    }
    Ok(result)
}

fn finite_difference_state_sensitivity(
    f: Fixture,
    z: Vector,
    theta: f64,
    step: f64,
) -> Result<Vector, StopCode> {
    let plus = hybrid_flow(f, z, theta + step)?.phi_h;
    let minus = hybrid_flow(f, z, theta - step)?.phi_h;
    Ok(v_scale(v_sub(plus, minus), 0.5 / step))
}

fn finite_difference_event_time(
    f: Fixture,
    z: Vector,
    theta: f64,
    step: f64,
) -> Result<f64, StopCode> {
    let plus = hybrid_flow(f, z, theta + step)?.event_time_s;
    let minus = hybrid_flow(f, z, theta - step)?.event_time_s;
    Ok((plus - minus) * 0.5 / step)
}

fn finite_difference_mixed_jacobian(
    f: Fixture,
    z: Vector,
    theta: f64,
    z_step: f64,
    theta_step: f64,
) -> Result<Matrix, StopCode> {
    let plus = finite_difference_jacobian(f, z, theta + theta_step, z_step)?;
    let minus = finite_difference_jacobian(f, z, theta - theta_step, z_step)?;
    Ok(m_scale(m_sub(plus, minus), 0.5 / theta_step))
}

fn finite_difference_metric(
    f: Fixture,
    z: Vector,
    theta: f64,
    z_step: f64,
) -> Result<Matrix, StopCode> {
    let flow = hybrid_flow(f, z, theta)?;
    let j = finite_difference_jacobian(f, z, theta, z_step)?;
    Ok(congruence(j, fisher(f, flow.phi_h, theta)))
}

fn finite_difference_metric_derivative(
    f: Fixture,
    z: Vector,
    theta: f64,
    z_step: f64,
    theta_step: f64,
) -> Result<Matrix, StopCode> {
    let plus = finite_difference_metric(f, z, theta + theta_step, z_step)?;
    let minus = finite_difference_metric(f, z, theta - theta_step, z_step)?;
    Ok(m_scale(m_sub(plus, minus), 0.5 / theta_step))
}

fn evaluate_level(
    f: Fixture,
    base: Analytic,
    z_step: f64,
    theta_step: f64,
) -> Result<LevelResult, StopCode> {
    let event_time_fd = finite_difference_event_time(f, f.z, f.theta, theta_step)?;
    let jacobian_fd = finite_difference_jacobian(f, f.z, f.theta, z_step)?;
    let state_fd = finite_difference_state_sensitivity(f, f.z, f.theta, theta_step)?;
    let mixed_fd = finite_difference_mixed_jacobian(f, f.z, f.theta, z_step, theta_step)?;
    let metric_fd = finite_difference_metric_derivative(f, f.z, f.theta, z_step, theta_step)?;
    Ok(LevelResult {
        z_step,
        theta_step,
        event_time_error: scaled_scalar_error(base.event_time_theta_s, event_time_fd),
        jacobian_error: scaled_matrix_error(base.saltation, jacobian_fd),
        state_sensitivity_error: scaled_vector_error(base.state_sensitivity, state_fd),
        mixed_jacobian_error: scaled_matrix_error(base.mixed_jacobian, mixed_fd),
        metric_derivative_error: scaled_matrix_error(base.metric_derivative, metric_fd),
        metric_derivative_fd: metric_fd,
    })
}

fn refinement_ratio(previous: f64, current: f64) -> f64 {
    if previous <= REFINEMENT_ERROR_FLOOR {
        0.0
    } else {
        current / previous
    }
}

fn no_guard_parameter_k(f: Fixture, base: Analytic) -> Matrix {
    let n = parameterized_guard(f, f.theta);
    let w_theta = v_scale(m_vec(f.reset_a1, f.f_pre_s_inv), -1.0);
    m_add(
        f.reset_a1,
        m_scale(outer(w_theta, n), 1.0 / base.flow.denominator_s_inv),
    )
}

fn no_reset_parameter_k(f: Fixture, base: Analytic) -> Matrix {
    let a = parameterized_reset_matrix(f, f.theta);
    let n = parameterized_guard(f, f.theta);
    let w = v_sub(f.f_post_s_inv, m_vec(a, f.f_pre_s_inv));
    let d = base.flow.denominator_s_inv;
    let d_theta = dot(f.guard_n1, f.f_pre_s_inv);
    m_sub(
        m_scale(outer(w, f.guard_n1), 1.0 / d),
        m_scale(outer(w, n), d_theta / d.powi(2)),
    )
}

fn ablation_errors(f: Fixture, base: Analytic, reference: Matrix) -> [f64; 6] {
    let a = parameterized_reset_matrix(f, f.theta);
    let k_no_guard = no_guard_parameter_k(f, base);
    let k_no_reset = no_reset_parameter_k(f, base);
    let (_, _, _, no_saltation) = metric_derivative_terms(
        a,
        f.reset_a1,
        base.terminal_fisher,
        base.d1_fisher,
        base.d2_fisher,
    );
    let (_, d1_no_guard, d2_no_guard) =
        fisher_derivatives(f, base.flow.phi_h, f.theta, base.reset_sensitivity);
    let (_, _, _, no_guard) = metric_derivative_terms(
        base.saltation,
        k_no_guard,
        base.terminal_fisher,
        d1_no_guard,
        d2_no_guard,
    );
    let (_, d1_no_reset, d2_no_reset) =
        fisher_derivatives(f, base.flow.phi_h, f.theta, base.event_time_sensitivity);
    let (_, _, _, no_reset) = metric_derivative_terms(
        base.saltation,
        k_no_reset,
        base.terminal_fisher,
        d1_no_reset,
        d2_no_reset,
    );
    let (_, _, _, no_event_time_state) = metric_derivative_terms(
        base.saltation,
        base.mixed_jacobian,
        base.terminal_fisher,
        d1_no_guard,
        base.d2_fisher,
    );
    let (_, _, _, omit_k) = metric_derivative_terms(
        base.saltation,
        [[0.0; 2]; 2],
        base.terminal_fisher,
        base.d1_fisher,
        base.d2_fisher,
    );
    let (_, _, _, omit_d2) = metric_derivative_terms(
        base.saltation,
        base.mixed_jacobian,
        base.terminal_fisher,
        base.d1_fisher,
        [[0.0; 2]; 2],
    );
    [
        scaled_matrix_error(no_saltation, reference),
        scaled_matrix_error(no_guard, reference),
        scaled_matrix_error(no_reset, reference),
        scaled_matrix_error(no_event_time_state, reference),
        scaled_matrix_error(omit_k, reference),
        scaled_matrix_error(omit_d2, reference),
    ]
}

fn covariance_and_scale_errors(f: Fixture, base: Analytic) -> [f64; 8] {
    let p = [[1.2, -0.25], [0.35, 0.9]];
    let p_inverse = inverse(p);
    let n = parameterized_guard(f, f.theta);
    let a = parameterized_reset_matrix(f, f.theta);
    let f_pre_y = m_vec(p_inverse, f.f_pre_s_inv);
    let f_post_y = m_vec(p_inverse, f.f_post_s_inv);
    let n_y = m_vec(transpose(p), n);
    let n1_y = m_vec(transpose(p), f.guard_n1);
    let a_y = m_mul(p_inverse, m_mul(a, p));
    let a1_y = m_mul(p_inverse, m_mul(f.reset_a1, p));
    let w_y = v_sub(f_post_y, m_vec(a_y, f_pre_y));
    let w_theta_y = v_scale(m_vec(a1_y, f_pre_y), -1.0);
    let d = dot(n_y, f_pre_y);
    let d_theta = dot(n1_y, f_pre_y);
    let saltation_y = m_add(a_y, m_scale(outer(w_y, n_y), 1.0 / d));
    let mixed_y = m_add(
        a1_y,
        m_sub(
            m_scale(m_add(outer(w_theta_y, n_y), outer(w_y, n1_y)), 1.0 / d),
            m_scale(outer(w_y, n_y), d_theta / d.powi(2)),
        ),
    );
    let saltation_expected = m_mul(p_inverse, m_mul(base.saltation, p));
    let mixed_expected = m_mul(p_inverse, m_mul(base.mixed_jacobian, p));
    let fisher_y = congruence(p, base.terminal_fisher);
    let d1_y = congruence(p, base.d1_fisher);
    let d2_y = congruence(p, base.d2_fisher);
    let metric_y = congruence(saltation_y, fisher_y);
    let (_, _, _, derivative_y) =
        metric_derivative_terms(saltation_y, mixed_y, fisher_y, d1_y, d2_y);
    let metric_expected = congruence(p, base.pullback_metric);
    let derivative_expected = congruence(p, base.metric_derivative);

    let guard_scale = -2.75;
    let n_scaled = v_scale(n, guard_scale);
    let n1_scaled = v_scale(f.guard_n1, guard_scale);
    let d_scaled = guard_scale * base.flow.denominator_s_inv;
    let d_theta_scaled = guard_scale * dot(f.guard_n1, f.f_pre_s_inv);
    let w = v_sub(f.f_post_s_inv, m_vec(a, f.f_pre_s_inv));
    let w_theta = v_scale(m_vec(f.reset_a1, f.f_pre_s_inv), -1.0);
    let saltation_scaled = m_add(a, m_scale(outer(w, n_scaled), 1.0 / d_scaled));
    let affine_scaled = v_add(
        base.reset_sensitivity,
        v_scale(w, guard_scale * base.guard_theta / d_scaled),
    );
    let mixed_scaled = m_add(
        f.reset_a1,
        m_sub(
            m_scale(
                m_add(outer(w_theta, n_scaled), outer(w, n1_scaled)),
                1.0 / d_scaled,
            ),
            m_scale(outer(w, n_scaled), d_theta_scaled / d_scaled.powi(2)),
        ),
    );
    let (_, _, _, derivative_scaled) = metric_derivative_terms(
        saltation_scaled,
        mixed_scaled,
        base.terminal_fisher,
        base.d1_fisher,
        base.d2_fisher,
    );
    [
        scaled_matrix_error(saltation_y, saltation_expected),
        scaled_matrix_error(mixed_y, mixed_expected),
        scaled_matrix_error(metric_y, metric_expected),
        scaled_matrix_error(derivative_y, derivative_expected),
        scaled_matrix_error(saltation_scaled, base.saltation),
        scaled_vector_error(affine_scaled, base.affine_jump),
        scaled_matrix_error(mixed_scaled, base.mixed_jacobian),
        scaled_matrix_error(derivative_scaled, base.metric_derivative),
    ]
}

fn grazing_fixture(mut f: Fixture) -> Fixture {
    let epsilon = 1.0e-10;
    f.guard_n0 = [0.4 + epsilon, -1.0];
    f.guard_n1 = [0.0, 0.0];
    f.guard_q = 0.0;
    f.guard_c = dot(f.guard_n0, f.z) + 0.5 * epsilon;
    f
}

fn event_word_failure_fixture(mut f: Fixture) -> Fixture {
    f.guard_c = dot(f.guard_n0, f.z) + f.flow_speed_along_guard() * (f.horizon_s + 0.5);
    f
}

impl Fixture {
    fn flow_speed_along_guard(self) -> f64 {
        dot(self.guard_n0, self.f_pre_s_inv)
    }
}

fn fixture_fingerprint(f: Fixture) -> u64 {
    let mut hash = 0xcbf29ce484222325_u64;
    let mut update = |value: f64| {
        for byte in value.to_bits().to_le_bytes() {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
    };
    for value in f.z {
        update(value);
    }
    for value in [f.horizon_s, f.theta, f.guard_c, f.guard_q] {
        update(value);
    }
    for vector in [
        f.f_pre_s_inv,
        f.f_post_s_inv,
        f.guard_n0,
        f.guard_n1,
        f.reset_b0,
        f.reset_r,
        f.output_sigma,
        f.output_gamma,
        f.output_rho,
    ] {
        for value in vector {
            update(value);
        }
    }
    for matrix in [f.reset_a0, f.reset_a1] {
        for row in matrix {
            for value in row {
                update(value);
            }
        }
    }
    hash
}

fn evaluate() -> Result<Report, Vec<String>> {
    let f = fixture();
    let base = analytic(f, f.z, f.theta).map_err(|code| vec![code.as_str().to_string()])?;
    let levels = [
        evaluate_level(f, base, Z_STEPS[0], THETA_STEPS[0]),
        evaluate_level(f, base, Z_STEPS[1], THETA_STEPS[1]),
        evaluate_level(f, base, Z_STEPS[2], THETA_STEPS[2]),
    ];
    let levels = match levels {
        [Ok(a), Ok(b), Ok(c)] => [a, b, c],
        _ => return Err(vec!["FINITE_DIFFERENCE_EVENT_WORD_STOP".to_string()]),
    };
    let refinement_ratios = [
        refinement_ratio(levels[1].event_time_error, levels[2].event_time_error),
        refinement_ratio(
            levels[1].state_sensitivity_error,
            levels[2].state_sensitivity_error,
        ),
        refinement_ratio(
            levels[1].mixed_jacobian_error,
            levels[2].mixed_jacobian_error,
        ),
        refinement_ratio(
            levels[1].metric_derivative_error,
            levels[2].metric_derivative_error,
        ),
    ];
    let determinant_j = determinant(base.saltation);
    let minimum_eigenvalue_fisher = symmetric_eigenvalues(base.terminal_fisher)[0];
    let minimum_eigenvalue_metric = symmetric_eigenvalues(base.pullback_metric)[0];
    let symmetry_error = (base.metric_derivative[0][1] - base.metric_derivative[1][0]).abs();
    let affine_jump_identity_error = scaled_vector_error(base.affine_jump, base.state_sensitivity);
    let covariance = covariance_and_scale_errors(f, base);
    let k_no_guard = no_guard_parameter_k(f, base);
    let k_no_reset = no_reset_parameter_k(f, base);
    let nondegeneracy_norms = [
        matrix_norm(base.saltation_correction),
        vector_norm(base.event_time_sensitivity),
        vector_norm(base.reset_sensitivity),
        matrix_norm(m_sub(base.mixed_jacobian, k_no_guard)),
        matrix_norm(m_sub(base.mixed_jacobian, k_no_reset)),
    ];
    let ablation_errors = ablation_errors(f, base, levels[2].metric_derivative_fd);
    let grazing = match analytic(grazing_fixture(f), f.z, f.theta) {
        Err(StopCode::GrazingOrNontransverse) => {
            ("EXPECTED_STOP", StopCode::GrazingOrNontransverse.as_str())
        }
        _ => ("UNEXPECTED_RESULT", "MISSING_GRAZING_STOP"),
    };
    let event_word_fixture = event_word_failure_fixture(f);
    let event_word = match analytic(
        event_word_fixture,
        event_word_fixture.z,
        event_word_fixture.theta,
    ) {
        Err(StopCode::EventWordChange) => ("EXPECTED_STOP", StopCode::EventWordChange.as_str()),
        _ => ("UNEXPECTED_RESULT", "MISSING_EVENT_WORD_STOP"),
    };

    let mut failures = Vec::new();
    let finest = levels[2];
    if finest.jacobian_error > J_TOLERANCE {
        failures.push("SALTATION_FD_MISMATCH".to_string());
    }
    if finest.event_time_error > EVENT_TIME_TOLERANCE {
        failures.push("EVENT_TIME_FD_MISMATCH".to_string());
    }
    if finest.state_sensitivity_error > S_TOLERANCE {
        failures.push("STATE_SENSITIVITY_FD_MISMATCH".to_string());
    }
    if finest.mixed_jacobian_error > K_TOLERANCE {
        failures.push("MIXED_JACOBIAN_FD_MISMATCH".to_string());
    }
    if finest.metric_derivative_error > METRIC_TOLERANCE {
        failures.push("METRIC_DERIVATIVE_FD_MISMATCH".to_string());
    }
    if refinement_ratios
        .iter()
        .any(|ratio| *ratio > REFINEMENT_RATIO_MAX)
    {
        failures.push("FINITE_DIFFERENCE_REFINEMENT_FAIL".to_string());
    }
    if determinant_j.abs() <= MIN_ABS_DETERMINANT_J {
        failures.push("SALTATION_RANK_FAIL".to_string());
    }
    if minimum_eigenvalue_fisher <= MIN_EIGENVALUE || minimum_eigenvalue_metric <= MIN_EIGENVALUE {
        failures.push("SPD_FAIL".to_string());
    }
    if symmetry_error > SYMMETRY_TOLERANCE {
        failures.push("METRIC_DERIVATIVE_SYMMETRY_FAIL".to_string());
    }
    if affine_jump_identity_error > IDENTITY_TOLERANCE {
        failures.push("AFFINE_JUMP_IDENTITY_FAIL".to_string());
    }
    if covariance.iter().any(|error| *error > COVARIANCE_TOLERANCE) {
        failures.push("COVARIANCE_OR_GUARD_SCALE_FAIL".to_string());
    }
    if nondegeneracy_norms
        .iter()
        .any(|norm| *norm <= NONDEGENERACY_MIN)
    {
        failures.push("PRIMITIVE_NONDEGENERACY_FAIL".to_string());
    }
    if ablation_errors.iter().any(|error| {
        *error <= ABLATION_ERROR_MIN
            || *error <= ABLATION_RATIO_MIN * finest.metric_derivative_error
    }) {
        failures.push("ABLATION_SEPARATION_FAIL".to_string());
    }
    if grazing.0 != "EXPECTED_STOP" {
        failures.push("GRAZING_FAIL_CLOSED_MISSING".to_string());
    }
    if event_word.0 != "EXPECTED_STOP" {
        failures.push("EVENT_WORD_FAIL_CLOSED_MISSING".to_string());
    }
    if failures.is_empty() {
        Ok(Report {
            base,
            levels,
            refinement_ratios,
            determinant_j,
            minimum_eigenvalue_fisher,
            minimum_eigenvalue_metric,
            symmetry_error,
            affine_jump_identity_error,
            coordinate_saltation_error: covariance[0],
            coordinate_mixed_error: covariance[1],
            coordinate_metric_error: covariance[2],
            coordinate_derivative_error: covariance[3],
            guard_scale_saltation_error: covariance[4],
            guard_scale_affine_error: covariance[5],
            guard_scale_mixed_error: covariance[6],
            guard_scale_derivative_error: covariance[7],
            nondegeneracy_norms,
            ablation_errors,
            grazing_status: grazing.0,
            grazing_code: grazing.1,
            event_word_status: event_word.0,
            event_word_code: event_word.1,
            fixture_fingerprint: fixture_fingerprint(f),
        })
    } else {
        Err(failures)
    }
}

fn json_vector(value: Vector) -> String {
    format!("[{:.17e},{:.17e}]", value[0], value[1])
}

fn json_matrix(value: Matrix) -> String {
    format!(
        "[[{:.17e},{:.17e}],[{:.17e},{:.17e}]]",
        value[0][0], value[0][1], value[1][0], value[1][1]
    )
}

fn receipt(report: &Report, source_sha256: &str) -> String {
    let f = fixture();
    let b = report.base;
    let mut output = String::new();
    writeln!(output, "{{").unwrap();
    writeln!(
        output,
        "  \"schema\": \"CE_NPF_HYBRID_SALTATION_WITNESS_V1\","
    )
    .unwrap();
    writeln!(
        output,
        "  \"status\": \"FORMAL_L0_HYBRID_NUMERICAL_WITNESS_PASS\","
    )
    .unwrap();
    writeln!(output, "  \"failure_codes\": [],").unwrap();
    writeln!(
        output,
        "  \"scope\": \"deterministic_2d_one_event_piecewise_affine_fixed_event_word\","
    )
    .unwrap();
    writeln!(output, "  \"equations_directly_exercised\": [\"21.54a\",\"21.54b\",\"21.54c\",\"21.54e\",\"21.54f\",\"21.54g\"],").unwrap();
    writeln!(output, "  \"equations_not_certified\": [\"multiple-event product beyond algebraic form\",\"hybrid RFDE saltation operator\",\"Brownian or CTMC marginal likelihood sensitivity\",\"rank-changing strata\",\"empirical biological attribution\"],").unwrap();
    writeln!(output, "  \"claim_ceiling\": \"BIO_EVIDENCE_L0\",").unwrap();
    writeln!(output, "  \"real_neural_data_used\": false,").unwrap();
    writeln!(output, "  \"fixture\": {{").unwrap();
    writeln!(output, "    \"state_dimension\": 2,").unwrap();
    writeln!(output, "    \"event_count\": 1,").unwrap();
    writeln!(output, "    \"mode_graph\": \"pre_to_post_one_way\",").unwrap();
    writeln!(output, "    \"initial_z\": {},", json_vector(f.z)).unwrap();
    writeln!(output, "    \"horizon_s\": {:.17e},", f.horizon_s).unwrap();
    writeln!(output, "    \"theta\": {:.17e},", f.theta).unwrap();
    writeln!(
        output,
        "    \"f_pre_s_inv\": {},",
        json_vector(f.f_pre_s_inv)
    )
    .unwrap();
    writeln!(
        output,
        "    \"f_post_s_inv\": {},",
        json_vector(f.f_post_s_inv)
    )
    .unwrap();
    writeln!(output, "    \"guard_n0\": {},", json_vector(f.guard_n0)).unwrap();
    writeln!(output, "    \"guard_n1\": {},", json_vector(f.guard_n1)).unwrap();
    writeln!(output, "    \"guard_c\": {:.17e},", f.guard_c).unwrap();
    writeln!(output, "    \"guard_q\": {:.17e},", f.guard_q).unwrap();
    writeln!(output, "    \"reset_A0\": {},", json_matrix(f.reset_a0)).unwrap();
    writeln!(output, "    \"reset_A1\": {},", json_matrix(f.reset_a1)).unwrap();
    writeln!(output, "    \"reset_b0\": {},", json_vector(f.reset_b0)).unwrap();
    writeln!(output, "    \"reset_r\": {},", json_vector(f.reset_r)).unwrap();
    writeln!(
        output,
        "    \"output_sigma\": {},",
        json_vector(f.output_sigma)
    )
    .unwrap();
    writeln!(
        output,
        "    \"output_gamma\": {},",
        json_vector(f.output_gamma)
    )
    .unwrap();
    writeln!(output, "    \"output_rho\": {}", json_vector(f.output_rho)).unwrap();
    writeln!(output, "  }},").unwrap();
    writeln!(output, "  \"assumptions\": [\"finite-dimensional deterministic piecewise-C2 neighborhood\",\"one-way unique event\",\"fixed transversal event word under every finite-difference perturbation\",\"no simultaneous event or Zeno accumulation\",\"parameter-independent state chart\",\"Gaussian output with common R2 support\"],").unwrap();
    writeln!(output, "  \"thresholds\": {{\"normalized_transversality\":{TRANSVERSALITY_MIN:.17e},\"event_endpoint_margin_s\":{EVENT_ENDPOINT_MARGIN_S:.17e},\"J\":{J_TOLERANCE:.17e},\"event_time\":{EVENT_TIME_TOLERANCE:.17e},\"s\":{S_TOLERANCE:.17e},\"K\":{K_TOLERANCE:.17e},\"delta_g\":{METRIC_TOLERANCE:.17e},\"refinement_ratio\":{REFINEMENT_RATIO_MAX:.17e},\"covariance\":{COVARIANCE_TOLERANCE:.17e},\"nondegeneracy\":{NONDEGENERACY_MIN:.17e},\"ablation_error\":{ABLATION_ERROR_MIN:.17e},\"ablation_ratio\":{ABLATION_RATIO_MIN:.1}}},").unwrap();
    writeln!(output, "  \"event_diagnostics\": {{\"event_time_s\":{:.17e},\"endpoint_margin_s\":{:.17e},\"guard_flow_denominator_s_inv\":{:.17e},\"normalized_transversality\":{:.17e},\"fixed_event_word_all_fd_points\":true}},",
        b.flow.event_time_s, b.flow.event_time_s.min(f.horizon_s-b.flow.event_time_s), b.flow.denominator_s_inv, b.flow.normalized_transversality).unwrap();
    writeln!(output, "  \"step_refinement\": [").unwrap();
    for (index, level) in report.levels.iter().enumerate() {
        writeln!(output, "    {{\"z_step\":{:.17e},\"theta_step\":{:.17e},\"event_time_error\":{:.17e},\"J_error\":{:.17e},\"s_error\":{:.17e},\"K_error\":{:.17e},\"delta_g_error\":{:.17e}}}{}",
            level.z_step, level.theta_step, level.event_time_error, level.jacobian_error,
            level.state_sensitivity_error, level.mixed_jacobian_error,
            level.metric_derivative_error, if index == 2 { "" } else { "," }).unwrap();
    }
    writeln!(output, "  ],").unwrap();
    writeln!(output, "  \"checks\": {{").unwrap();
    writeln!(output, "    \"phi_H\": {},", json_vector(b.flow.phi_h)).unwrap();
    writeln!(output, "    \"x_minus\": {},", json_vector(b.flow.x_minus)).unwrap();
    writeln!(
        output,
        "    \"event_time_theta_s\": {:.17e},",
        b.event_time_theta_s
    )
    .unwrap();
    writeln!(
        output,
        "    \"event_time_z_s\": {},",
        json_vector(b.event_time_z_s)
    )
    .unwrap();
    writeln!(output, "    \"guard_theta\": {:.17e},", b.guard_theta).unwrap();
    writeln!(
        output,
        "    \"saltation_Xi\": {},",
        json_matrix(b.saltation)
    )
    .unwrap();
    writeln!(
        output,
        "    \"affine_jump_rho\": {},",
        json_vector(b.affine_jump)
    )
    .unwrap();
    writeln!(
        output,
        "    \"reset_sensitivity\": {},",
        json_vector(b.reset_sensitivity)
    )
    .unwrap();
    writeln!(
        output,
        "    \"event_time_sensitivity\": {},",
        json_vector(b.event_time_sensitivity)
    )
    .unwrap();
    writeln!(
        output,
        "    \"state_sensitivity\": {},",
        json_vector(b.state_sensitivity)
    )
    .unwrap();
    writeln!(
        output,
        "    \"mixed_jacobian_K\": {},",
        json_matrix(b.mixed_jacobian)
    )
    .unwrap();
    writeln!(
        output,
        "    \"terminal_fisher_G\": {},",
        json_matrix(b.terminal_fisher)
    )
    .unwrap();
    writeln!(output, "    \"D1_G\": {},", json_matrix(b.d1_fisher)).unwrap();
    writeln!(output, "    \"D2_G\": {},", json_matrix(b.d2_fisher)).unwrap();
    writeln!(
        output,
        "    \"pullback_metric_g\": {},",
        json_matrix(b.pullback_metric)
    )
    .unwrap();
    writeln!(
        output,
        "    \"tangent_term\": {},",
        json_matrix(b.tangent_term)
    )
    .unwrap();
    writeln!(output, "    \"D1_term\": {},", json_matrix(b.d1_term)).unwrap();
    writeln!(output, "    \"D2_term\": {},", json_matrix(b.d2_term)).unwrap();
    writeln!(
        output,
        "    \"metric_derivative\": {},",
        json_matrix(b.metric_derivative)
    )
    .unwrap();
    writeln!(
        output,
        "    \"determinant_J\": {:.17e},",
        report.determinant_j
    )
    .unwrap();
    writeln!(
        output,
        "    \"minimum_eigenvalue_fisher\": {:.17e},",
        report.minimum_eigenvalue_fisher
    )
    .unwrap();
    writeln!(
        output,
        "    \"minimum_eigenvalue_metric\": {:.17e},",
        report.minimum_eigenvalue_metric
    )
    .unwrap();
    writeln!(
        output,
        "    \"symmetry_error\": {:.17e},",
        report.symmetry_error
    )
    .unwrap();
    writeln!(
        output,
        "    \"affine_jump_identity_error\": {:.17e}",
        report.affine_jump_identity_error
    )
    .unwrap();
    writeln!(output, "  }},").unwrap();
    writeln!(
        output,
        "  \"refinement_ratios_finest\": {{\"event_time\":{:.17e},\"s\":{:.17e},\"K\":{:.17e},\"delta_g\":{:.17e}}},",
        report.refinement_ratios[0], report.refinement_ratios[1], report.refinement_ratios[2], report.refinement_ratios[3]
    )
    .unwrap();
    writeln!(output, "  \"nondegeneracy_norms\": {{\"saltation_correction\":{:.17e},\"event_time_state_term\":{:.17e},\"reset_parameter_term\":{:.17e},\"guard_contribution_to_K\":{:.17e},\"reset_contribution_to_K\":{:.17e}}},",
        report.nondegeneracy_norms[0], report.nondegeneracy_norms[1], report.nondegeneracy_norms[2], report.nondegeneracy_norms[3], report.nondegeneracy_norms[4]).unwrap();
    writeln!(output, "  \"ablation_scaled_errors\": {{\"reset_jacobian_only\":{:.17e},\"no_guard_parameter\":{:.17e},\"no_reset_parameter\":{:.17e},\"omit_event_time_in_state_sensitivity\":{:.17e},\"omit_K\":{:.17e},\"omit_D2G\":{:.17e}}},",
        report.ablation_errors[0], report.ablation_errors[1], report.ablation_errors[2], report.ablation_errors[3], report.ablation_errors[4], report.ablation_errors[5]).unwrap();
    writeln!(output, "  \"covariance_controls\": {{\"state_chart_saltation_error\":{:.17e},\"state_chart_mixed_error\":{:.17e},\"pullback_metric_error\":{:.17e},\"metric_derivative_error\":{:.17e},\"guard_rescale_saltation_error\":{:.17e},\"guard_rescale_affine_error\":{:.17e},\"guard_rescale_mixed_error\":{:.17e},\"guard_rescale_metric_derivative_error\":{:.17e}}},",
        report.coordinate_saltation_error, report.coordinate_mixed_error, report.coordinate_metric_error, report.coordinate_derivative_error, report.guard_scale_saltation_error, report.guard_scale_affine_error, report.guard_scale_mixed_error, report.guard_scale_derivative_error).unwrap();
    writeln!(output, "  \"fail_closed_controls\": {{\"grazing\":{{\"status\":\"{}\",\"failure_code\":\"{}\"}},\"event_word_change\":{{\"status\":\"{}\",\"failure_code\":\"{}\"}}}},",
        report.grazing_status, report.grazing_code, report.event_word_status, report.event_word_code).unwrap();
    writeln!(output, "  \"solver_and_environment\": {{\"language\":\"Rust\",\"arithmetic\":\"IEEE-754 binary64\",\"flow\":\"closed-form piecewise-affine one-event return map\"}},").unwrap();
    writeln!(output, "  \"artifact_hashes\": {{\"source_sha256\":\"{source_sha256}\",\"fixture_fingerprint_fnv1a64\":\"{:016x}\",\"receipt_sha256\":null,\"receipt_hash_policy\":\"recorded externally because self-hash is recursive\"}},", report.fixture_fingerprint).unwrap();
    writeln!(output, "  \"claim_locks\": {{\"general_hybrid_RFDE_proved\":false,\"stochastic_jump_sensitivity_proved\":false,\"real_neural_metric_verified\":false,\"functional_folding_verified\":false,\"behavioral_mediation_verified\":false,\"stage10_identified\":false}},").unwrap();
    writeln!(output, "  \"next_equation_gate\": \"CTMC_HAZARD_AND_JUMP_KERNEL_SCORE_OR_FINITE_HYBRID_RFDE_REALIZATION\"").unwrap();
    writeln!(output, "}}").unwrap();
    output
}

fn print_report(report: &Report) {
    let finest = report.levels[2];
    println!(
        "PASS event: t={:.6} s, normalized transversality={:.3e}",
        report.base.flow.event_time_s, report.base.flow.normalized_transversality
    );
    println!(
        "PASS finest FD: event_time={:.3e} J={:.3e} s={:.3e} K={:.3e} delta_g={:.3e}",
        finest.event_time_error,
        finest.jacobian_error,
        finest.state_sensitivity_error,
        finest.mixed_jacobian_error,
        finest.metric_derivative_error
    );
    println!(
        "PASS nondegeneracy: saltation={:.3e} event_time={:.3e} reset={:.3e} guard_K={:.3e} reset_K={:.3e}",
        report.nondegeneracy_norms[0],
        report.nondegeneracy_norms[1],
        report.nondegeneracy_norms[2],
        report.nondegeneracy_norms[3],
        report.nondegeneracy_norms[4]
    );
    println!(
        "PASS ablations: no_salt={:.3e} no_guard={:.3e} no_reset={:.3e} no_event_time={:.3e} omit_K={:.3e} omit_D2={:.3e}",
        report.ablation_errors[0],
        report.ablation_errors[1],
        report.ablation_errors[2],
        report.ablation_errors[3],
        report.ablation_errors[4],
        report.ablation_errors[5]
    );
    println!(
        "PASS covariance/fail-closed: coordinate={:.3e} guard_scale={:.3e} grazing={} event_word={}",
        report.coordinate_derivative_error,
        report.guard_scale_saltation_error,
        report.grazing_status,
        report.event_word_status
    );
    println!("RESULT: FORMAL_L0_HYBRID_NUMERICAL_WITNESS_PASS (synthetic fixture; biological ceiling unchanged)");
}

fn parse_arguments() -> Result<(Option<PathBuf>, String), String> {
    let mut receipt_path = None;
    let mut source_sha256 = "unrecorded".to_string();
    let arguments: Vec<String> = env::args().skip(1).collect();
    let mut index = 0;
    while index < arguments.len() {
        match arguments[index].as_str() {
            "--receipt" => {
                index += 1;
                receipt_path = Some(PathBuf::from(
                    arguments.get(index).ok_or("--receipt requires a path")?,
                ));
            }
            "--source-sha256" => {
                index += 1;
                source_sha256 = arguments
                    .get(index)
                    .ok_or("--source-sha256 requires a value")?
                    .clone();
                if source_sha256.len() != 64
                    || !source_sha256.bytes().all(|byte| byte.is_ascii_hexdigit())
                {
                    return Err("--source-sha256 must be 64 hexadecimal characters".to_string());
                }
                source_sha256.make_ascii_lowercase();
            }
            argument => return Err(format!("unknown argument: {argument}")),
        }
        index += 1;
    }
    Ok((receipt_path, source_sha256))
}

fn run() -> Result<(), String> {
    let (receipt_path, source_sha256) = parse_arguments()?;
    let report = evaluate().map_err(|failures| failures.join(","))?;
    print_report(&report);
    if let Some(path) = receipt_path {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        }
        fs::write(&path, receipt(&report, &source_sha256)).map_err(|error| error.to_string())?;
        println!("RECEIPT: {}", path.display());
    }
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("RESULT: FAIL ({error})");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixed_fixture_passes_all_predeclared_gates() {
        if let Err(failures) = evaluate() {
            panic!("{}", failures.join(","));
        }
    }

    #[test]
    fn grazing_and_event_word_changes_fail_closed() {
        let f = fixture();
        assert!(matches!(
            analytic(grazing_fixture(f), f.z, f.theta),
            Err(StopCode::GrazingOrNontransverse)
        ));
        let event_word = event_word_failure_fixture(f);
        assert!(matches!(
            analytic(event_word, event_word.z, event_word.theta),
            Err(StopCode::EventWordChange)
        ));
        let mut zero_normal = f;
        zero_normal.guard_n0 = [0.0, 0.0];
        zero_normal.guard_n1 = [0.0, 0.0];
        assert!(matches!(
            analytic(zero_normal, zero_normal.z, zero_normal.theta),
            Err(StopCode::GrazingOrNontransverse)
        ));
    }

    #[test]
    fn closed_form_base_values_are_locked() {
        let f = fixture();
        let base = analytic(f, f.z, f.theta).unwrap();
        assert!((base.flow.event_time_s - 0.8888888888888888).abs() < 1.0e-14);
        assert!(
            scaled_vector_error(base.flow.phi_h, [0.3088888888888889, 1.396111111111111]) < 1.0e-14
        );
        assert!((determinant(base.saltation) + 0.7138888888888889).abs() < 1.0e-14);
        assert!(symmetric_eigenvalues(base.pullback_metric)[0] > MIN_EIGENVALUE);
    }
}
