//! Deterministic binary64 witness for equations (21.46)--(21.53).
//!
//! This is one fixed, synthetic, feed-forward delayed-flow fixture.  It checks
//! signs, chain rules, mixed tangents, Fisher terms, and coordinate covariance.
//! It is not a general RFDE proof and is not evidence about neural tissue.

use std::env;
use std::fmt::Write as _;
use std::fs;
use std::path::PathBuf;

type Vector = [f64; 3];
type Matrix = [[f64; 3]; 3];

const REFERENCE_INTERVALS: usize = 4096;
const LEVEL_INTERVALS: [usize; 3] = [512, 1024, 2048];
const Z_STEPS: [f64; 3] = [4.0e-4, 2.0e-4, 1.0e-4];
const PARAMETER_STEPS: [f64; 3] = [4.0e-3, 2.0e-3, 1.0e-3];
const SOLVER_TOLERANCE: f64 = 1.0e-8;
const J_S_TOLERANCE: f64 = 2.0e-5;
const K_TOLERANCE: f64 = 2.0e-4;
const METRIC_TOLERANCE: f64 = 5.0e-4;
const PRIMITIVE_TOLERANCE: f64 = 2.0e-6;
const NONDEGENERACY_CUTOFF: f64 = 1.0e-5;
const ABLATION_ERROR_FLOOR: f64 = 1.0e-5;
const ABLATION_RATIO: f64 = 20.0;
const REFINEMENT_FLOOR: f64 = 1.0e-7;

#[derive(Clone, Copy)]
struct SourceEdge {
    sign: f64,
    source_tau_s: f64,
    input_amplitude: f64,
    input_frequency_hz: f64,
    input_phase: f64,
    path_length_m: f64,
    synaptic_delay_s: f64,
}

#[derive(Clone, Copy)]
struct Parameters {
    weight: [f64; 2],
    packet: [f64; 2],
    velocity_m_s: [f64; 2],
    rho: f64,
}

#[derive(Clone, Copy)]
struct Direction {
    weight: [f64; 2],
    packet: [f64; 2],
    velocity_m_s: [f64; 2],
    rho: f64,
}

#[derive(Clone, Copy)]
struct Fixture {
    horizon_s: f64,
    target_tau_s: f64,
    bias: f64,
    z: Vector,
    edges: [SourceEdge; 2],
    parameters: Parameters,
    gamma: Vector,
    sigma: Vector,
}

#[derive(Clone, Copy)]
struct Analytic {
    phi: Vector,
    jacobian: Matrix,
    state_sensitivity: Vector,
    mixed_jacobian: Matrix,
    terminal_fisher: Matrix,
    pullback_metric: Matrix,
    d1_fisher: Matrix,
    d2_fisher: Matrix,
    tangent_term: Matrix,
    indirect_fisher_term: Matrix,
    direct_fisher_term: Matrix,
    metric_derivative: Matrix,
    delta_tau_s: [f64; 2],
}

#[derive(Clone, Copy)]
struct LevelResult {
    intervals: usize,
    z_step: f64,
    parameter_step: f64,
    jacobian_error: f64,
    state_sensitivity_error: f64,
    mixed_jacobian_error: f64,
    d1_fisher_error: f64,
    d2_fisher_error: f64,
    tangent_term_error: f64,
    indirect_term_error: f64,
    direct_term_error: f64,
    metric_derivative_error: f64,
    metric_derivative_fd: Matrix,
}

struct Report {
    base: Analytic,
    levels: [LevelResult; 3],
    solver_refinement_error: f64,
    primitive_delay_error: f64,
    zero_direction_norm: f64,
    frozen_delay_norm: f64,
    zero_path_speed_norm: f64,
    rho_only_flow_norm: f64,
    no_direct_fisher_norm: f64,
    contribution_norms: [f64; 6],
    ablation_errors: [f64; 6],
    coordinate_metric_error: f64,
    coordinate_derivative_error: f64,
    line_element_error: f64,
    delta_line_element_error: f64,
    determinant_j: f64,
    minimum_eigenvalue_g: f64,
    minimum_eigenvalue_metric: f64,
    metric_condition_number: f64,
    symmetry_error: f64,
    fixture_fingerprint: u64,
}

fn fixture() -> Fixture {
    Fixture {
        horizon_s: 0.060,
        target_tau_s: 0.020,
        bias: 0.15,
        z: [0.12, -0.18, 0.24],
        edges: [
            SourceEdge {
                sign: 1.0,
                source_tau_s: 0.030,
                input_amplitude: 0.45,
                input_frequency_hz: 6.0,
                input_phase: 0.40,
                path_length_m: 0.004,
                synaptic_delay_s: 0.003,
            },
            SourceEdge {
                sign: -1.0,
                source_tau_s: 0.025,
                input_amplitude: 0.38,
                input_frequency_hz: 4.5,
                input_phase: -0.30,
                path_length_m: 0.006,
                synaptic_delay_s: 0.004,
            },
        ],
        parameters: Parameters {
            weight: [0.50, 0.42],
            packet: [0.82, 0.66],
            velocity_m_s: [0.20, 0.24],
            rho: 0.12,
        },
        gamma: [0.35, -0.25, 0.20],
        sigma: [0.60, 0.80, 0.90],
    }
}

fn combined_direction() -> Direction {
    Direction {
        weight: [0.060, -0.040],
        packet: [-0.040, 0.050],
        velocity_m_s: [0.012, -0.009],
        rho: 0.080,
    }
}

fn zero_direction() -> Direction {
    Direction {
        weight: [0.0; 2],
        packet: [0.0; 2],
        velocity_m_s: [0.0; 2],
        rho: 0.0,
    }
}

fn weight_direction() -> Direction {
    Direction {
        weight: [0.080, -0.050],
        ..zero_direction()
    }
}

fn packet_direction() -> Direction {
    Direction {
        packet: [-0.060, 0.070],
        ..zero_direction()
    }
}

fn speed_direction() -> Direction {
    Direction {
        velocity_m_s: [0.015, -0.012],
        ..zero_direction()
    }
}

fn fisher_direction() -> Direction {
    Direction {
        rho: 0.10,
        ..zero_direction()
    }
}

fn rate_gain_direction() -> Direction {
    let mut direction = combined_direction();
    direction.velocity_m_s = [0.0; 2];
    direction.rho = 0.0;
    direction
}

fn frozen_delay_direction() -> Direction {
    let mut direction = combined_direction();
    direction.velocity_m_s = [0.0; 2];
    direction
}

fn shuffled_edge_direction() -> Direction {
    let direction = combined_direction();
    Direction {
        weight: [direction.weight[1], direction.weight[0]],
        packet: [direction.packet[1], direction.packet[0]],
        velocity_m_s: [direction.velocity_m_s[1], direction.velocity_m_s[0]],
        rho: direction.rho,
    }
}

fn zeros() -> Matrix {
    [[0.0; 3]; 3]
}

fn add(left: Matrix, right: Matrix) -> Matrix {
    let mut result = zeros();
    for row in 0..3 {
        for column in 0..3 {
            result[row][column] = left[row][column] + right[row][column];
        }
    }
    result
}

fn sub(left: Matrix, right: Matrix) -> Matrix {
    let mut result = zeros();
    for row in 0..3 {
        for column in 0..3 {
            result[row][column] = left[row][column] - right[row][column];
        }
    }
    result
}

fn scale(matrix: Matrix, scalar: f64) -> Matrix {
    let mut result = zeros();
    for row in 0..3 {
        for column in 0..3 {
            result[row][column] = matrix[row][column] * scalar;
        }
    }
    result
}

fn transpose(matrix: Matrix) -> Matrix {
    let mut result = zeros();
    for row in 0..3 {
        for column in 0..3 {
            result[row][column] = matrix[column][row];
        }
    }
    result
}

fn multiply(left: Matrix, right: Matrix) -> Matrix {
    let mut result = zeros();
    for row in 0..3 {
        for column in 0..3 {
            for inner in 0..3 {
                result[row][column] += left[row][inner] * right[inner][column];
            }
        }
    }
    result
}

fn mat_vec(matrix: Matrix, vector: Vector) -> Vector {
    let mut result = [0.0; 3];
    for row in 0..3 {
        for column in 0..3 {
            result[row] += matrix[row][column] * vector[column];
        }
    }
    result
}

fn vector_dot(left: Vector, right: Vector) -> f64 {
    left.iter().zip(right.iter()).map(|(a, b)| a * b).sum()
}

fn matrix_norm(matrix: Matrix) -> f64 {
    matrix
        .iter()
        .flat_map(|row| row.iter())
        .map(|value| value * value)
        .sum::<f64>()
        .sqrt()
}

fn vector_norm(vector: Vector) -> f64 {
    vector.iter().map(|value| value * value).sum::<f64>().sqrt()
}

fn matrix_max_abs(matrix: Matrix) -> f64 {
    matrix
        .iter()
        .flat_map(|row| row.iter())
        .map(|value| value.abs())
        .fold(0.0, f64::max)
}

fn scaled_matrix_error(left: Matrix, right: Matrix, floor: f64) -> f64 {
    let mut maximum = 0.0_f64;
    for row in 0..3 {
        for column in 0..3 {
            let denominator = left[row][column]
                .abs()
                .max(right[row][column].abs())
                .max(floor);
            maximum = maximum.max((left[row][column] - right[row][column]).abs() / denominator);
        }
    }
    maximum
}

fn scaled_vector_error(left: Vector, right: Vector, floor: f64) -> f64 {
    let mut maximum = 0.0_f64;
    for index in 0..3 {
        let denominator = left[index].abs().max(right[index].abs()).max(floor);
        maximum = maximum.max((left[index] - right[index]).abs() / denominator);
    }
    maximum
}

fn determinant(matrix: Matrix) -> f64 {
    matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
        - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
        + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0])
}

fn inverse(matrix: Matrix) -> Matrix {
    let det = determinant(matrix);
    assert!(det.abs() > 1.0e-12, "rechart matrix must be invertible");
    let mut result = zeros();
    result[0][0] = matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1];
    result[0][1] = matrix[0][2] * matrix[2][1] - matrix[0][1] * matrix[2][2];
    result[0][2] = matrix[0][1] * matrix[1][2] - matrix[0][2] * matrix[1][1];
    result[1][0] = matrix[1][2] * matrix[2][0] - matrix[1][0] * matrix[2][2];
    result[1][1] = matrix[0][0] * matrix[2][2] - matrix[0][2] * matrix[2][0];
    result[1][2] = matrix[0][2] * matrix[1][0] - matrix[0][0] * matrix[1][2];
    result[2][0] = matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0];
    result[2][1] = matrix[0][1] * matrix[2][0] - matrix[0][0] * matrix[2][1];
    result[2][2] = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0];
    scale(result, 1.0 / det)
}

fn symmetric_eigenvalues(mut matrix: Matrix) -> Vector {
    for _ in 0..64 {
        let mut p = 0;
        let mut q = 1;
        let mut largest = matrix[p][q].abs();
        for row in 0..3 {
            for column in (row + 1)..3 {
                if matrix[row][column].abs() > largest {
                    p = row;
                    q = column;
                    largest = matrix[row][column].abs();
                }
            }
        }
        if largest < 1.0e-15 {
            break;
        }
        let angle = 0.5 * (2.0 * matrix[p][q]).atan2(matrix[q][q] - matrix[p][p]);
        let cosine = angle.cos();
        let sine = angle.sin();
        let app = matrix[p][p];
        let aqq = matrix[q][q];
        let apq = matrix[p][q];
        matrix[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq;
        matrix[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq;
        matrix[p][q] = 0.0;
        matrix[q][p] = 0.0;
        for index in 0..3 {
            if index != p && index != q {
                let aip = matrix[index][p];
                let aiq = matrix[index][q];
                matrix[index][p] = cosine * aip - sine * aiq;
                matrix[p][index] = matrix[index][p];
                matrix[index][q] = sine * aip + cosine * aiq;
                matrix[q][index] = matrix[index][q];
            }
        }
    }
    let mut values = [matrix[0][0], matrix[1][1], matrix[2][2]];
    values.sort_by(|left, right| left.total_cmp(right));
    values
}

fn simpson<F>(horizon: f64, intervals: usize, function: F) -> f64
where
    F: Fn(f64) -> f64,
{
    assert!(intervals > 0 && intervals % 2 == 0);
    let step = horizon / intervals as f64;
    let mut sum = function(0.0) + function(horizon);
    for index in 1..intervals {
        let coefficient = if index % 2 == 0 { 2.0 } else { 4.0 };
        sum += coefficient * function(index as f64 * step);
    }
    sum * step / 3.0
}

fn source_particular(edge: SourceEdge, time: f64) -> f64 {
    let omega = 2.0 * std::f64::consts::PI * edge.input_frequency_hz;
    let angle = omega * time + edge.input_phase;
    let omega_tau = omega * edge.source_tau_s;
    edge.input_amplitude * (angle.sin() - omega_tau * angle.cos()) / (1.0 + omega_tau * omega_tau)
}

fn source_value(edge: SourceEdge, time: f64, initial: f64) -> f64 {
    let particular_zero = source_particular(edge, 0.0);
    source_particular(edge, time) + (initial - particular_zero) * (-time / edge.source_tau_s).exp()
}

fn source_derivative(edge: SourceEdge, time: f64, initial: f64) -> f64 {
    let omega = 2.0 * std::f64::consts::PI * edge.input_frequency_hz;
    let angle = omega * time + edge.input_phase;
    let omega_tau = omega * edge.source_tau_s;
    let particular_derivative = edge.input_amplitude
        * (omega * angle.cos() + omega * omega * edge.source_tau_s * angle.sin())
        / (1.0 + omega_tau * omega_tau);
    let particular_zero = source_particular(edge, 0.0);
    particular_derivative
        - (initial - particular_zero) * (-time / edge.source_tau_s).exp() / edge.source_tau_s
}

fn source_z(edge: SourceEdge, time: f64) -> f64 {
    (-time / edge.source_tau_s).exp()
}

fn delay(edge: SourceEdge, parameters: Parameters, edge_index: usize) -> f64 {
    edge.synaptic_delay_s + edge.path_length_m / parameters.velocity_m_s[edge_index]
}

fn delta_delay(
    edge: SourceEdge,
    parameters: Parameters,
    direction: Direction,
    edge_index: usize,
    include_delay: bool,
) -> f64 {
    if include_delay {
        -edge.path_length_m * direction.velocity_m_s[edge_index]
            / parameters.velocity_m_s[edge_index].powi(2)
    } else {
        0.0
    }
}

fn h_at(fixture: Fixture, parameters: Parameters, z: Vector, time: f64) -> f64 {
    let mut value = fixture.bias;
    for edge_index in 0..2 {
        let edge = fixture.edges[edge_index];
        let delayed_time = time - delay(edge, parameters, edge_index);
        let source = source_value(edge, delayed_time, z[edge_index + 1]);
        value += edge.sign * parameters.weight[edge_index] * parameters.packet[edge_index] * source;
    }
    value
}

fn h_z_at(fixture: Fixture, parameters: Parameters, time: f64, edge_index: usize) -> f64 {
    let edge = fixture.edges[edge_index];
    let delayed_time = time - delay(edge, parameters, edge_index);
    edge.sign
        * parameters.weight[edge_index]
        * parameters.packet[edge_index]
        * source_z(edge, delayed_time)
}

fn delta_h_at(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    z: Vector,
    time: f64,
    include_delay: bool,
) -> f64 {
    let mut value = 0.0;
    for edge_index in 0..2 {
        let edge = fixture.edges[edge_index];
        let delayed_time = time - delay(edge, parameters, edge_index);
        let source = source_value(edge, delayed_time, z[edge_index + 1]);
        let source_dot = source_derivative(edge, delayed_time, z[edge_index + 1]);
        let delta_tau = delta_delay(edge, parameters, direction, edge_index, include_delay);
        value += edge.sign
            * (parameters.packet[edge_index] * source * direction.weight[edge_index]
                + parameters.weight[edge_index] * source * direction.packet[edge_index]
                - parameters.weight[edge_index]
                    * parameters.packet[edge_index]
                    * source_dot
                    * delta_tau);
    }
    value
}

fn delta_h_z_at(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    time: f64,
    edge_index: usize,
    include_delay: bool,
) -> f64 {
    let edge = fixture.edges[edge_index];
    let delayed_time = time - delay(edge, parameters, edge_index);
    let z_derivative = source_z(edge, delayed_time);
    let delta_tau = delta_delay(edge, parameters, direction, edge_index, include_delay);
    edge.sign
        * z_derivative
        * (parameters.packet[edge_index] * direction.weight[edge_index]
            + parameters.weight[edge_index] * direction.packet[edge_index]
            + parameters.weight[edge_index] * parameters.packet[edge_index] * delta_tau
                / edge.source_tau_s)
}

fn primal(fixture: Fixture, parameters: Parameters, z: Vector, intervals: usize) -> Vector {
    let decay = (-fixture.horizon_s / fixture.target_tau_s).exp();
    let target = decay * z[0]
        + simpson(fixture.horizon_s, intervals, |time| {
            let kernel =
                (-(fixture.horizon_s - time) / fixture.target_tau_s).exp() / fixture.target_tau_s;
            kernel * h_at(fixture, parameters, z, time).tanh()
        });
    [
        target,
        source_value(fixture.edges[0], fixture.horizon_s, z[1]),
        source_value(fixture.edges[1], fixture.horizon_s, z[2]),
    ]
}

fn analytic_flow(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    intervals: usize,
    include_delay: bool,
) -> (Vector, Matrix, Vector, Matrix, [f64; 2]) {
    let phi = primal(fixture, parameters, fixture.z, intervals);
    let mut jacobian = zeros();
    jacobian[0][0] = (-fixture.horizon_s / fixture.target_tau_s).exp();
    jacobian[1][1] = (-fixture.horizon_s / fixture.edges[0].source_tau_s).exp();
    jacobian[2][2] = (-fixture.horizon_s / fixture.edges[1].source_tau_s).exp();

    for edge_index in 0..2 {
        jacobian[0][edge_index + 1] = simpson(fixture.horizon_s, intervals, |time| {
            let h = h_at(fixture, parameters, fixture.z, time);
            let activation_derivative = 1.0 - h.tanh().powi(2);
            let kernel =
                (-(fixture.horizon_s - time) / fixture.target_tau_s).exp() / fixture.target_tau_s;
            kernel * activation_derivative * h_z_at(fixture, parameters, time, edge_index)
        });
    }

    let state_target = simpson(fixture.horizon_s, intervals, |time| {
        let h = h_at(fixture, parameters, fixture.z, time);
        let activation_derivative = 1.0 - h.tanh().powi(2);
        let kernel =
            (-(fixture.horizon_s - time) / fixture.target_tau_s).exp() / fixture.target_tau_s;
        kernel
            * activation_derivative
            * delta_h_at(
                fixture,
                parameters,
                direction,
                fixture.z,
                time,
                include_delay,
            )
    });
    let state_sensitivity = [state_target, 0.0, 0.0];

    let mut mixed_jacobian = zeros();
    for edge_index in 0..2 {
        mixed_jacobian[0][edge_index + 1] = simpson(fixture.horizon_s, intervals, |time| {
            let h = h_at(fixture, parameters, fixture.z, time);
            let tanh_h = h.tanh();
            let first = 1.0 - tanh_h.powi(2);
            let second = -2.0 * tanh_h * first;
            let delta_h = delta_h_at(
                fixture,
                parameters,
                direction,
                fixture.z,
                time,
                include_delay,
            );
            let h_z = h_z_at(fixture, parameters, time, edge_index);
            let delta_h_z = delta_h_z_at(
                fixture,
                parameters,
                direction,
                time,
                edge_index,
                include_delay,
            );
            let kernel =
                (-(fixture.horizon_s - time) / fixture.target_tau_s).exp() / fixture.target_tau_s;
            kernel * (second * delta_h * h_z + first * delta_h_z)
        });
    }

    let delta_tau_s = [
        delta_delay(fixture.edges[0], parameters, direction, 0, include_delay),
        delta_delay(fixture.edges[1], parameters, direction, 1, include_delay),
    ];
    (
        phi,
        jacobian,
        state_sensitivity,
        mixed_jacobian,
        delta_tau_s,
    )
}

fn output_metric(fixture: Fixture, phi: Vector, parameters: Parameters) -> Matrix {
    let mut metric = zeros();
    for index in 0..3 {
        let scale = if index == 0 {
            parameters.rho.exp()
        } else {
            1.0
        };
        let derivative = scale * (1.0 + fixture.gamma[index] * phi[index]);
        metric[index][index] = derivative.powi(2) / fixture.sigma[index].powi(2);
    }
    metric
}

fn output_metric_derivatives(
    fixture: Fixture,
    phi: Vector,
    parameters: Parameters,
    state_sensitivity: Vector,
    direction: Direction,
) -> (Matrix, Matrix) {
    let mut d1 = zeros();
    let mut d2 = zeros();
    for index in 0..3 {
        let scale_squared = if index == 0 {
            (2.0 * parameters.rho).exp()
        } else {
            1.0
        };
        d1[index][index] = 2.0
            * fixture.gamma[index]
            * scale_squared
            * (1.0 + fixture.gamma[index] * phi[index])
            * state_sensitivity[index]
            / fixture.sigma[index].powi(2);
    }
    d2[0][0] = 2.0 * direction.rho * output_metric(fixture, phi, parameters)[0][0];
    (d1, d2)
}

fn pullback(jacobian: Matrix, terminal_metric: Matrix) -> Matrix {
    multiply(multiply(transpose(jacobian), terminal_metric), jacobian)
}

fn analytic(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    intervals: usize,
    include_delay: bool,
) -> Analytic {
    let (phi, jacobian, state_sensitivity, mixed_jacobian, delta_tau_s) =
        analytic_flow(fixture, parameters, direction, intervals, include_delay);
    let terminal_fisher = output_metric(fixture, phi, parameters);
    let pullback_metric = pullback(jacobian, terminal_fisher);
    let (d1_fisher, d2_fisher) =
        output_metric_derivatives(fixture, phi, parameters, state_sensitivity, direction);
    let tangent_term = add(
        multiply(
            multiply(transpose(mixed_jacobian), terminal_fisher),
            jacobian,
        ),
        multiply(
            multiply(transpose(jacobian), terminal_fisher),
            mixed_jacobian,
        ),
    );
    let indirect_fisher_term = pullback(jacobian, d1_fisher);
    let direct_fisher_term = pullback(jacobian, d2_fisher);
    let metric_derivative = add(add(tangent_term, indirect_fisher_term), direct_fisher_term);
    Analytic {
        phi,
        jacobian,
        state_sensitivity,
        mixed_jacobian,
        terminal_fisher,
        pullback_metric,
        d1_fisher,
        d2_fisher,
        tangent_term,
        indirect_fisher_term,
        direct_fisher_term,
        metric_derivative,
        delta_tau_s,
    }
}

fn perturb_parameters(parameters: Parameters, direction: Direction, epsilon: f64) -> Parameters {
    let result = Parameters {
        weight: [
            parameters.weight[0] + epsilon * direction.weight[0],
            parameters.weight[1] + epsilon * direction.weight[1],
        ],
        packet: [
            parameters.packet[0] + epsilon * direction.packet[0],
            parameters.packet[1] + epsilon * direction.packet[1],
        ],
        velocity_m_s: [
            parameters.velocity_m_s[0] + epsilon * direction.velocity_m_s[0],
            parameters.velocity_m_s[1] + epsilon * direction.velocity_m_s[1],
        ],
        rho: parameters.rho + epsilon * direction.rho,
    };
    assert!(result.velocity_m_s.iter().all(|value| *value > 0.0));
    result
}

fn finite_jacobian(
    fixture: Fixture,
    parameters: Parameters,
    z_step: f64,
    intervals: usize,
) -> Matrix {
    let mut result = zeros();
    for column in 0..3 {
        let mut plus_z = fixture.z;
        let mut minus_z = fixture.z;
        plus_z[column] += z_step;
        minus_z[column] -= z_step;
        let plus = primal(fixture, parameters, plus_z, intervals);
        let minus = primal(fixture, parameters, minus_z, intervals);
        for row in 0..3 {
            result[row][column] = (plus[row] - minus[row]) / (2.0 * z_step);
        }
    }
    result
}

fn finite_state_sensitivity(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    parameter_step: f64,
    intervals: usize,
) -> Vector {
    let plus = primal(
        fixture,
        perturb_parameters(parameters, direction, parameter_step),
        fixture.z,
        intervals,
    );
    let minus = primal(
        fixture,
        perturb_parameters(parameters, direction, -parameter_step),
        fixture.z,
        intervals,
    );
    [
        (plus[0] - minus[0]) / (2.0 * parameter_step),
        (plus[1] - minus[1]) / (2.0 * parameter_step),
        (plus[2] - minus[2]) / (2.0 * parameter_step),
    ]
}

fn finite_mixed_jacobian(
    fixture: Fixture,
    parameters: Parameters,
    direction: Direction,
    z_step: f64,
    parameter_step: f64,
    intervals: usize,
) -> Matrix {
    let plus = finite_jacobian(
        fixture,
        perturb_parameters(parameters, direction, parameter_step),
        z_step,
        intervals,
    );
    let minus = finite_jacobian(
        fixture,
        perturb_parameters(parameters, direction, -parameter_step),
        z_step,
        intervals,
    );
    scale(sub(plus, minus), 1.0 / (2.0 * parameter_step))
}

fn finite_metric(
    fixture: Fixture,
    parameters: Parameters,
    z_step: f64,
    intervals: usize,
) -> Matrix {
    let phi = primal(fixture, parameters, fixture.z, intervals);
    let jacobian = finite_jacobian(fixture, parameters, z_step, intervals);
    pullback(jacobian, output_metric(fixture, phi, parameters))
}

fn level_result(fixture: Fixture, level: usize, direction: Direction) -> LevelResult {
    let intervals = LEVEL_INTERVALS[level];
    let z_step = Z_STEPS[level];
    let parameter_step = PARAMETER_STEPS[level];
    let parameters = fixture.parameters;
    let exact = analytic(fixture, parameters, direction, intervals, true);
    let finite_j = finite_jacobian(fixture, parameters, z_step, intervals);
    let finite_s =
        finite_state_sensitivity(fixture, parameters, direction, parameter_step, intervals);
    let finite_k = finite_mixed_jacobian(
        fixture,
        parameters,
        direction,
        z_step,
        parameter_step,
        intervals,
    );

    let plus_parameters = perturb_parameters(parameters, direction, parameter_step);
    let minus_parameters = perturb_parameters(parameters, direction, -parameter_step);
    let plus_phi = primal(fixture, plus_parameters, fixture.z, intervals);
    let minus_phi = primal(fixture, minus_parameters, fixture.z, intervals);
    let plus_j = finite_jacobian(fixture, plus_parameters, z_step, intervals);
    let minus_j = finite_jacobian(fixture, minus_parameters, z_step, intervals);
    let base_j = finite_j;
    let base_g = exact.terminal_fisher;

    let finite_d1 = scale(
        sub(
            output_metric(fixture, plus_phi, parameters),
            output_metric(fixture, minus_phi, parameters),
        ),
        1.0 / (2.0 * parameter_step),
    );
    let rho_plus = perturb_parameters(
        parameters,
        fisher_direction(),
        parameter_step * direction.rho / 0.10,
    );
    let rho_minus = perturb_parameters(
        parameters,
        fisher_direction(),
        -parameter_step * direction.rho / 0.10,
    );
    let finite_d2 = if direction.rho == 0.0 {
        zeros()
    } else {
        scale(
            sub(
                output_metric(fixture, exact.phi, rho_plus),
                output_metric(fixture, exact.phi, rho_minus),
            ),
            1.0 / (2.0 * parameter_step),
        )
    };
    let finite_tangent = scale(
        sub(pullback(plus_j, base_g), pullback(minus_j, base_g)),
        1.0 / (2.0 * parameter_step),
    );
    let finite_indirect = pullback(base_j, finite_d1);
    let finite_direct = pullback(base_j, finite_d2);
    let plus_metric = finite_metric(fixture, plus_parameters, z_step, intervals);
    let minus_metric = finite_metric(fixture, minus_parameters, z_step, intervals);
    let finite_delta_metric = scale(sub(plus_metric, minus_metric), 1.0 / (2.0 * parameter_step));

    LevelResult {
        intervals,
        z_step,
        parameter_step,
        jacobian_error: scaled_matrix_error(exact.jacobian, finite_j, 1.0e-7),
        state_sensitivity_error: scaled_vector_error(exact.state_sensitivity, finite_s, 1.0e-7),
        mixed_jacobian_error: scaled_matrix_error(exact.mixed_jacobian, finite_k, 1.0e-7),
        d1_fisher_error: scaled_matrix_error(exact.d1_fisher, finite_d1, 1.0e-6),
        d2_fisher_error: scaled_matrix_error(exact.d2_fisher, finite_d2, 1.0e-6),
        tangent_term_error: scaled_matrix_error(exact.tangent_term, finite_tangent, 1.0e-6),
        indirect_term_error: scaled_matrix_error(
            exact.indirect_fisher_term,
            finite_indirect,
            1.0e-6,
        ),
        direct_term_error: scaled_matrix_error(exact.direct_fisher_term, finite_direct, 1.0e-6),
        metric_derivative_error: scaled_matrix_error(
            exact.metric_derivative,
            finite_delta_metric,
            1.0e-6,
        ),
        metric_derivative_fd: finite_delta_metric,
    }
}

fn refinement_pass(errors: [f64; 3]) -> bool {
    for index in 1..3 {
        if errors[index - 1] > REFINEMENT_FLOOR && errors[index] > 0.55 * errors[index - 1] {
            return false;
        }
    }
    true
}

fn primitive_delay_error(fixture: Fixture) -> f64 {
    let speed = speed_direction();
    let epsilon = 1.0e-5;
    let mut maximum = 0.0_f64;
    for edge_index in 0..2 {
        let mut direction = zero_direction();
        direction.velocity_m_s[edge_index] = speed.velocity_m_s[edge_index];
        for time in [0.0, 0.013, 0.031, fixture.horizon_s] {
            let edge = fixture.edges[edge_index];
            let delayed_time = time - delay(edge, fixture.parameters, edge_index);
            let source_dot = source_derivative(edge, delayed_time, fixture.z[edge_index + 1]);
            let analytic = -edge.sign
                * fixture.parameters.weight[edge_index]
                * fixture.parameters.packet[edge_index]
                * source_dot
                * delta_delay(edge, fixture.parameters, direction, edge_index, true);
            let plus = h_at(
                fixture,
                perturb_parameters(fixture.parameters, direction, epsilon),
                fixture.z,
                time,
            );
            let minus = h_at(
                fixture,
                perturb_parameters(fixture.parameters, direction, -epsilon),
                fixture.z,
                time,
            );
            let finite = (plus - minus) / (2.0 * epsilon);
            maximum = maximum
                .max((analytic - finite).abs() / analytic.abs().max(finite.abs()).max(1.0e-7));
        }
    }
    maximum
}

fn solver_refinement_error(fixture: Fixture, direction: Direction) -> f64 {
    let medium = analytic(
        fixture,
        fixture.parameters,
        direction,
        LEVEL_INTERVALS[2],
        true,
    );
    let fine = analytic(
        fixture,
        fixture.parameters,
        direction,
        REFERENCE_INTERVALS,
        true,
    );
    scaled_vector_error(medium.phi, fine.phi, 1.0e-7)
        .max(scaled_matrix_error(medium.jacobian, fine.jacobian, 1.0e-7))
        .max(scaled_vector_error(
            medium.state_sensitivity,
            fine.state_sensitivity,
            1.0e-7,
        ))
        .max(scaled_matrix_error(
            medium.mixed_jacobian,
            fine.mixed_jacobian,
            1.0e-7,
        ))
        .max(scaled_matrix_error(
            medium.metric_derivative,
            fine.metric_derivative,
            1.0e-6,
        ))
}

fn fixture_fingerprint(fixture: Fixture) -> u64 {
    fn mix(mut hash: u64, value: f64) -> u64 {
        for byte in value.to_bits().to_le_bytes() {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3);
        }
        hash
    }
    let mut hash = 0xcbf29ce484222325;
    for value in [fixture.horizon_s, fixture.target_tau_s, fixture.bias]
        .into_iter()
        .chain(fixture.z)
        .chain(fixture.parameters.weight)
        .chain(fixture.parameters.packet)
        .chain(fixture.parameters.velocity_m_s)
        .chain([fixture.parameters.rho])
        .chain(fixture.gamma)
        .chain(fixture.sigma)
    {
        hash = mix(hash, value);
    }
    for edge in fixture.edges {
        for value in [
            edge.sign,
            edge.source_tau_s,
            edge.input_amplitude,
            edge.input_frequency_hz,
            edge.input_phase,
            edge.path_length_m,
            edge.synaptic_delay_s,
        ] {
            hash = mix(hash, value);
        }
    }
    hash
}

fn evaluate() -> Result<Report, Vec<String>> {
    let fixture = fixture();
    let direction = combined_direction();
    let base = analytic(
        fixture,
        fixture.parameters,
        direction,
        REFERENCE_INTERVALS,
        true,
    );
    let levels = [
        level_result(fixture, 0, direction),
        level_result(fixture, 1, direction),
        level_result(fixture, 2, direction),
    ];
    let solver_error = solver_refinement_error(fixture, direction);
    let primitive_error = primitive_delay_error(fixture);

    let zero = analytic(
        fixture,
        fixture.parameters,
        zero_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let speed_frozen = analytic(
        fixture,
        fixture.parameters,
        speed_direction(),
        REFERENCE_INTERVALS,
        false,
    );
    let mut zero_path_fixture = fixture;
    zero_path_fixture.edges[0].path_length_m = 0.0;
    zero_path_fixture.edges[1].path_length_m = 0.0;
    let zero_path_speed = analytic(
        zero_path_fixture,
        zero_path_fixture.parameters,
        speed_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let rho_only = analytic(
        fixture,
        fixture.parameters,
        fisher_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let weight_only = analytic(
        fixture,
        fixture.parameters,
        weight_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let packet_only = analytic(
        fixture,
        fixture.parameters,
        packet_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let speed_only = analytic(
        fixture,
        fixture.parameters,
        speed_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let contribution_norms = [
        matrix_norm(weight_only.metric_derivative),
        matrix_norm(packet_only.metric_derivative),
        matrix_norm(speed_only.metric_derivative),
        matrix_norm(base.tangent_term),
        matrix_norm(base.indirect_fisher_term),
        matrix_norm(base.direct_fisher_term),
    ];

    let finite_target = levels[2].metric_derivative_fd;
    let full_error = scaled_matrix_error(base.metric_derivative, finite_target, 1.0e-6);
    let frozen_delay = analytic(
        fixture,
        fixture.parameters,
        frozen_delay_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let rate_gain = analytic(
        fixture,
        fixture.parameters,
        rate_gain_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let shuffled = analytic(
        fixture,
        fixture.parameters,
        shuffled_edge_direction(),
        REFERENCE_INTERVALS,
        true,
    );
    let omit_k = add(base.indirect_fisher_term, base.direct_fisher_term);
    let omit_d1 = add(base.tangent_term, base.direct_fisher_term);
    let omit_d2 = add(base.tangent_term, base.indirect_fisher_term);
    let ablation_errors = [
        scaled_matrix_error(frozen_delay.metric_derivative, finite_target, 1.0e-6),
        scaled_matrix_error(rate_gain.metric_derivative, finite_target, 1.0e-6),
        scaled_matrix_error(shuffled.metric_derivative, finite_target, 1.0e-6),
        scaled_matrix_error(omit_k, finite_target, 1.0e-6),
        scaled_matrix_error(omit_d1, finite_target, 1.0e-6),
        scaled_matrix_error(omit_d2, finite_target, 1.0e-6),
    ];

    let rechart = [[1.2, 0.1, -0.05], [0.0, 0.9, 0.2], [0.15, -0.1, 1.1]];
    let rechart_inverse = inverse(rechart);
    let metric_prime = multiply(
        multiply(transpose(rechart_inverse), base.pullback_metric),
        rechart_inverse,
    );
    let derivative_prime = multiply(
        multiply(transpose(rechart_inverse), base.metric_derivative),
        rechart_inverse,
    );
    let metric_back = multiply(multiply(transpose(rechart), metric_prime), rechart);
    let derivative_back = multiply(multiply(transpose(rechart), derivative_prime), rechart);
    let displacement = [0.31, -0.22, 0.27];
    let displacement_prime = mat_vec(rechart, displacement);
    let line = vector_dot(displacement, mat_vec(base.pullback_metric, displacement));
    let line_prime = vector_dot(
        displacement_prime,
        mat_vec(metric_prime, displacement_prime),
    );
    let delta_line = vector_dot(displacement, mat_vec(base.metric_derivative, displacement));
    let delta_line_prime = vector_dot(
        displacement_prime,
        mat_vec(derivative_prime, displacement_prime),
    );

    let eigen_g = symmetric_eigenvalues(base.terminal_fisher);
    let eigen_metric = symmetric_eigenvalues(base.pullback_metric);
    let symmetry_error = matrix_max_abs(sub(
        base.metric_derivative,
        transpose(base.metric_derivative),
    ));
    let rho_only_flow_norm = vector_norm(rho_only.state_sensitivity)
        .max(matrix_norm(rho_only.mixed_jacobian))
        .max(matrix_norm(rho_only.d1_fisher));
    let no_direct_fisher_norm = matrix_norm(weight_only.d2_fisher)
        .max(matrix_norm(packet_only.d2_fisher))
        .max(matrix_norm(speed_only.d2_fisher));

    let mut failures = Vec::new();
    let mut check = |condition: bool, code: &str| {
        if !condition {
            failures.push(code.to_string());
        }
    };
    check(solver_error <= SOLVER_TOLERANCE, "SOLVER_REFINEMENT_FAIL");
    check(
        primitive_error <= PRIMITIVE_TOLERANCE,
        "MOVING_DELAY_PRIMITIVE_FAIL",
    );
    let fine = levels[2];
    check(fine.jacobian_error <= J_S_TOLERANCE, "JACOBIAN_FD_FAIL");
    check(
        fine.state_sensitivity_error <= J_S_TOLERANCE,
        "STATE_SENSITIVITY_FD_FAIL",
    );
    check(
        fine.mixed_jacobian_error <= K_TOLERANCE,
        "MIXED_JACOBIAN_FD_FAIL",
    );
    check(fine.d1_fisher_error <= J_S_TOLERANCE, "D1_FISHER_FD_FAIL");
    check(fine.d2_fisher_error <= J_S_TOLERANCE, "D2_FISHER_FD_FAIL");
    check(
        fine.tangent_term_error <= METRIC_TOLERANCE,
        "TANGENT_TERM_FD_FAIL",
    );
    check(
        fine.indirect_term_error <= METRIC_TOLERANCE,
        "INDIRECT_TERM_FD_FAIL",
    );
    check(
        fine.direct_term_error <= METRIC_TOLERANCE,
        "DIRECT_TERM_FD_FAIL",
    );
    check(
        fine.metric_derivative_error <= METRIC_TOLERANCE,
        "FULL_METRIC_DERIVATIVE_FD_FAIL",
    );
    for (name, errors) in [
        (
            "JACOBIAN_REFINEMENT_FAIL",
            levels.map(|level| level.jacobian_error),
        ),
        (
            "STATE_REFINEMENT_FAIL",
            levels.map(|level| level.state_sensitivity_error),
        ),
        (
            "MIXED_REFINEMENT_FAIL",
            levels.map(|level| level.mixed_jacobian_error),
        ),
        (
            "METRIC_REFINEMENT_FAIL",
            levels.map(|level| level.metric_derivative_error),
        ),
    ] {
        check(refinement_pass(errors), name);
    }
    check(
        matrix_norm(zero.metric_derivative) <= 1.0e-14,
        "ZERO_DIRECTION_FAIL",
    );
    check(
        matrix_norm(speed_frozen.metric_derivative) <= 1.0e-14,
        "FROZEN_DELAY_ZERO_FAIL",
    );
    check(
        matrix_norm(zero_path_speed.metric_derivative) <= 1.0e-14,
        "ZERO_PATH_SPEED_ZERO_FAIL",
    );
    check(rho_only_flow_norm <= 1.0e-14, "RHO_ONLY_FLOW_ZERO_FAIL");
    check(no_direct_fisher_norm <= 1.0e-14, "NON_RHO_D2_ZERO_FAIL");
    for (index, norm) in contribution_norms.iter().enumerate() {
        check(
            *norm > NONDEGENERACY_CUTOFF,
            &format!("NONDEGENERACY_CHANNEL_{index}_FAIL"),
        );
    }
    for (index, error) in ablation_errors.iter().enumerate() {
        check(
            *error > ABLATION_ERROR_FLOOR && *error > ABLATION_RATIO * full_error,
            &format!("ABLATION_{index}_FAIL"),
        );
    }
    check(
        determinant(base.jacobian).abs() > 1.0e-4,
        "JACOBIAN_DETERMINANT_FAIL",
    );
    check(eigen_g[0] > 0.20, "TERMINAL_FISHER_SPD_FAIL");
    check(eigen_metric[0] > 1.0e-5, "PULLBACK_METRIC_SPD_FAIL");
    check(
        eigen_metric[2] / eigen_metric[0] < 1.0e5,
        "PULLBACK_CONDITION_FAIL",
    );
    check(symmetry_error < 1.0e-10, "METRIC_DERIVATIVE_SYMMETRY_FAIL");
    check(
        scaled_matrix_error(base.pullback_metric, metric_back, 1.0e-12) < 1.0e-10,
        "METRIC_CONGRUENCE_FAIL",
    );
    check(
        scaled_matrix_error(base.metric_derivative, derivative_back, 1.0e-12) < 1.0e-10,
        "DERIVATIVE_CONGRUENCE_FAIL",
    );
    check(
        (line - line_prime).abs() < 1.0e-12,
        "LINE_ELEMENT_INVARIANCE_FAIL",
    );
    check(
        (delta_line - delta_line_prime).abs() < 1.0e-12,
        "DELTA_LINE_ELEMENT_INVARIANCE_FAIL",
    );

    if !failures.is_empty() {
        return Err(failures);
    }
    Ok(Report {
        base,
        levels,
        solver_refinement_error: solver_error,
        primitive_delay_error: primitive_error,
        zero_direction_norm: matrix_norm(zero.metric_derivative),
        frozen_delay_norm: matrix_norm(speed_frozen.metric_derivative),
        zero_path_speed_norm: matrix_norm(zero_path_speed.metric_derivative),
        rho_only_flow_norm,
        no_direct_fisher_norm,
        contribution_norms,
        ablation_errors,
        coordinate_metric_error: scaled_matrix_error(base.pullback_metric, metric_back, 1.0e-12),
        coordinate_derivative_error: scaled_matrix_error(
            base.metric_derivative,
            derivative_back,
            1.0e-12,
        ),
        line_element_error: (line - line_prime).abs(),
        delta_line_element_error: (delta_line - delta_line_prime).abs(),
        determinant_j: determinant(base.jacobian),
        minimum_eigenvalue_g: eigen_g[0],
        minimum_eigenvalue_metric: eigen_metric[0],
        metric_condition_number: eigen_metric[2] / eigen_metric[0],
        symmetry_error,
        fixture_fingerprint: fixture_fingerprint(fixture),
    })
}

fn json_vector(vector: Vector) -> String {
    format!("[{:.17e},{:.17e},{:.17e}]", vector[0], vector[1], vector[2])
}

fn json_pair(pair: [f64; 2]) -> String {
    format!("[{:.17e},{:.17e}]", pair[0], pair[1])
}

fn json_matrix(matrix: Matrix) -> String {
    format!(
        "[[{:.17e},{:.17e},{:.17e}],[{:.17e},{:.17e},{:.17e}],[{:.17e},{:.17e},{:.17e}]]",
        matrix[0][0],
        matrix[0][1],
        matrix[0][2],
        matrix[1][0],
        matrix[1][1],
        matrix[1][2],
        matrix[2][0],
        matrix[2][1],
        matrix[2][2],
    )
}

fn receipt(report: &Report, source_sha256: &str) -> String {
    let fixture = fixture();
    let direction = combined_direction();
    let mut output = String::new();
    writeln!(output, "{{").unwrap();
    writeln!(output, "  \"schema\": \"CE_NPF_NUMERICAL_WITNESS_V1\",").unwrap();
    writeln!(
        output,
        "  \"status\": \"FORMAL_L0_NUMERICAL_WITNESS_PASS\","
    )
    .unwrap();
    writeln!(output, "  \"failure_codes\": [],").unwrap();
    writeln!(
        output,
        "  \"scope\": \"deterministic_reduced_DDE_fixed_mode_synthetic_fixture\","
    )
    .unwrap();
    writeln!(output, "  \"equations_directly_exercised\": [\"21.46\",\"21.47\",\"21.48\",\"21.51\",\"21.52\",\"21.53\"],").unwrap();
    writeln!(output, "  \"equations_not_certified\": [\"21.49-21.50 general RFDE Frechet theorem\",\"21.54 empirical attribution\",\"21.55+ biological folding\",\"jump or stochastic dynamics\"],").unwrap();
    writeln!(output, "  \"parameter_channels_exercised\": [\"two signed fixed edges\",\"long-term weight\",\"mean packet/STP factor\",\"velocity-derived axonal delay\",\"terminal Fisher state dependence D1\",\"terminal Fisher direct parameter dependence D2\"],").unwrap();
    writeln!(output, "  \"parameter_channels_not_exercised\": [\"support birth/death\",\"membrane time-constant perturbation\",\"intrinsic threshold perturbation\",\"path-length perturbation\",\"effective synaptic-delay perturbation\",\"recurrent RFDE interpolation\",\"noise\"],").unwrap();
    writeln!(output, "  \"claim_ceiling\": \"BIO_EVIDENCE_L0\",").unwrap();
    writeln!(output, "  \"formal_model_status\": \"FORMAL_MODEL_V1\",").unwrap();
    writeln!(
        output,
        "  \"biological_mediation_status\": \"BIOLOGICAL_MEDIATION_UNTESTED\","
    )
    .unwrap();
    writeln!(output, "  \"real_neural_data_used\": false,").unwrap();
    writeln!(output, "  \"fixture\": {{").unwrap();
    writeln!(output, "    \"state_dimension\": 3,").unwrap();
    writeln!(output, "    \"edge_count\": 2,").unwrap();
    writeln!(output, "    \"horizon_s\": {:.17e},", fixture.horizon_s).unwrap();
    writeln!(
        output,
        "    \"target_tau_s\": {:.17e},",
        fixture.target_tau_s
    )
    .unwrap();
    writeln!(
        output,
        "    \"initial_chart_z\": {},",
        json_vector(fixture.z)
    )
    .unwrap();
    writeln!(
        output,
        "    \"edge_signs\": [{:.1},{:.1}],",
        fixture.edges[0].sign, fixture.edges[1].sign
    )
    .unwrap();
    writeln!(
        output,
        "    \"weight\": {},",
        json_pair(fixture.parameters.weight)
    )
    .unwrap();
    writeln!(
        output,
        "    \"packet_factor\": {},",
        json_pair(fixture.parameters.packet)
    )
    .unwrap();
    writeln!(
        output,
        "    \"path_length_m\": {},",
        json_pair([
            fixture.edges[0].path_length_m,
            fixture.edges[1].path_length_m
        ])
    )
    .unwrap();
    writeln!(
        output,
        "    \"velocity_m_s\": {},",
        json_pair(fixture.parameters.velocity_m_s)
    )
    .unwrap();
    writeln!(
        output,
        "    \"total_delay_s\": {},",
        json_pair([
            delay(fixture.edges[0], fixture.parameters, 0),
            delay(fixture.edges[1], fixture.parameters, 1)
        ])
    )
    .unwrap();
    writeln!(output, "    \"activation\": \"tanh\",").unwrap();
    writeln!(
        output,
        "    \"chart\": \"three terminal state coordinates\","
    )
    .unwrap();
    writeln!(
        output,
        "    \"output_family\": \"three-dimensional Gaussian with common R3 support\","
    )
    .unwrap();
    writeln!(
        output,
        "    \"direction_weight\": {},",
        json_pair(direction.weight)
    )
    .unwrap();
    writeln!(
        output,
        "    \"direction_packet\": {},",
        json_pair(direction.packet)
    )
    .unwrap();
    writeln!(
        output,
        "    \"direction_velocity_m_s\": {},",
        json_pair(direction.velocity_m_s)
    )
    .unwrap();
    writeln!(output, "    \"direction_rho\": {:.17e}", direction.rho).unwrap();
    writeln!(output, "  }},").unwrap();
    writeln!(output, "  \"assumptions\": [\"Sigma_X=0\",\"fixed contact and event mode\",\"delta A=0\",\"C1 analytic source histories\",\"parameter intervention at t=0 with fixed initial history\",\"fixed chart\",\"Gaussian common support and dominated differentiation\"],").unwrap();
    writeln!(output, "  \"solver_and_environment\": {{\"language\":\"Rust\",\"arithmetic\":\"IEEE-754 binary64\",\"integration\":\"composite Simpson on exact feed-forward variation-of-constants integral\",\"reference_intervals\":{REFERENCE_INTERVALS}}},").unwrap();
    writeln!(output, "  \"thresholds\": {{\"solver\":{SOLVER_TOLERANCE:.17e},\"J_s\":{J_S_TOLERANCE:.17e},\"K\":{K_TOLERANCE:.17e},\"metric_terms\":{METRIC_TOLERANCE:.17e},\"primitive_delay\":{PRIMITIVE_TOLERANCE:.17e},\"nondegeneracy\":{NONDEGENERACY_CUTOFF:.17e},\"ablation_ratio\":{ABLATION_RATIO:.1}}},").unwrap();
    writeln!(output, "  \"step_refinement\": [").unwrap();
    for (index, level) in report.levels.iter().enumerate() {
        writeln!(output, "    {{\"intervals\":{},\"z_step\":{:.17e},\"parameter_step\":{:.17e},\"J_error\":{:.17e},\"s_error\":{:.17e},\"K_error\":{:.17e},\"D1_error\":{:.17e},\"D2_error\":{:.17e},\"tangent_error\":{:.17e},\"indirect_error\":{:.17e},\"direct_error\":{:.17e},\"delta_g_error\":{:.17e}}}{}",
            level.intervals, level.z_step, level.parameter_step, level.jacobian_error,
            level.state_sensitivity_error, level.mixed_jacobian_error, level.d1_fisher_error,
            level.d2_fisher_error, level.tangent_term_error, level.indirect_term_error,
            level.direct_term_error, level.metric_derivative_error,
            if index + 1 == report.levels.len() { "" } else { "," }).unwrap();
    }
    writeln!(output, "  ],").unwrap();
    writeln!(output, "  \"checks\": {{").unwrap();
    writeln!(
        output,
        "    \"solver_refinement_error\": {:.17e},",
        report.solver_refinement_error
    )
    .unwrap();
    writeln!(
        output,
        "    \"primitive_delay_error\": {:.17e},",
        report.primitive_delay_error
    )
    .unwrap();
    writeln!(output, "    \"phi_H\": {},", json_vector(report.base.phi)).unwrap();
    writeln!(
        output,
        "    \"J_H\": {},",
        json_matrix(report.base.jacobian)
    )
    .unwrap();
    writeln!(
        output,
        "    \"s_H\": {},",
        json_vector(report.base.state_sensitivity)
    )
    .unwrap();
    writeln!(
        output,
        "    \"K_J_H\": {},",
        json_matrix(report.base.mixed_jacobian)
    )
    .unwrap();
    writeln!(
        output,
        "    \"G_T\": {},",
        json_matrix(report.base.terminal_fisher)
    )
    .unwrap();
    writeln!(
        output,
        "    \"g_H\": {},",
        json_matrix(report.base.pullback_metric)
    )
    .unwrap();
    writeln!(
        output,
        "    \"delta_g_H\": {},",
        json_matrix(report.base.metric_derivative)
    )
    .unwrap();
    writeln!(
        output,
        "    \"delta_tau_s\": {},",
        json_pair(report.base.delta_tau_s)
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
        "    \"minimum_eigenvalue_terminal_Fisher\": {:.17e},",
        report.minimum_eigenvalue_g
    )
    .unwrap();
    writeln!(
        output,
        "    \"minimum_eigenvalue_pullback_metric\": {:.17e},",
        report.minimum_eigenvalue_metric
    )
    .unwrap();
    writeln!(
        output,
        "    \"condition_number_g\": {:.17e},",
        report.metric_condition_number
    )
    .unwrap();
    writeln!(
        output,
        "    \"symmetry_error_delta_g\": {:.17e}",
        report.symmetry_error
    )
    .unwrap();
    writeln!(output, "  }},").unwrap();
    writeln!(output, "  \"nondegeneracy_norms\": {{\"weight\":{:.17e},\"packet_STP\":{:.17e},\"velocity_delay\":{:.17e},\"K_J_term\":{:.17e},\"D1G_term\":{:.17e},\"D2G_term\":{:.17e}}},",
        report.contribution_norms[0], report.contribution_norms[1], report.contribution_norms[2],
        report.contribution_norms[3], report.contribution_norms[4], report.contribution_norms[5]).unwrap();
    writeln!(output, "  \"controls\": {{").unwrap();
    writeln!(
        output,
        "    \"zero_direction_norm\": {:.17e},",
        report.zero_direction_norm
    )
    .unwrap();
    writeln!(
        output,
        "    \"frozen_delay_speed_norm\": {:.17e},",
        report.frozen_delay_norm
    )
    .unwrap();
    writeln!(
        output,
        "    \"zero_path_speed_norm\": {:.17e},",
        report.zero_path_speed_norm
    )
    .unwrap();
    writeln!(
        output,
        "    \"rho_only_flow_norm\": {:.17e},",
        report.rho_only_flow_norm
    )
    .unwrap();
    writeln!(
        output,
        "    \"non_rho_D2_norm\": {:.17e},",
        report.no_direct_fisher_norm
    )
    .unwrap();
    writeln!(output, "    \"ablation_scaled_errors\": {{\"frozen_delay\":{:.17e},\"rate_gain_only\":{:.17e},\"shuffled_edge\":{:.17e},\"omit_K_J\":{:.17e},\"omit_D1G\":{:.17e},\"omit_D2G\":{:.17e}}},",
        report.ablation_errors[0], report.ablation_errors[1], report.ablation_errors[2],
        report.ablation_errors[3], report.ablation_errors[4], report.ablation_errors[5]).unwrap();
    writeln!(
        output,
        "    \"coordinate_metric_error\": {:.17e},",
        report.coordinate_metric_error
    )
    .unwrap();
    writeln!(
        output,
        "    \"coordinate_derivative_error\": {:.17e},",
        report.coordinate_derivative_error
    )
    .unwrap();
    writeln!(
        output,
        "    \"line_element_error\": {:.17e},",
        report.line_element_error
    )
    .unwrap();
    writeln!(
        output,
        "    \"delta_line_element_error\": {:.17e}",
        report.delta_line_element_error
    )
    .unwrap();
    writeln!(output, "  }},").unwrap();
    writeln!(output, "  \"artifact_hashes\": {{\"source_sha256\":\"{source_sha256}\",\"fixture_fingerprint_fnv1a64\":\"{:016x}\",\"receipt_sha256\":null,\"receipt_hash_policy\":\"recorded externally because self-hash is recursive\"}},", report.fixture_fingerprint).unwrap();
    writeln!(output, "  \"claim_locks\": {{\"general_RFDE_proved\":false,\"real_neural_metric_verified\":false,\"conduction_velocity_causal_effect_verified\":false,\"functional_folding_verified\":false,\"behavioral_mediation_verified\":false,\"stage10_identified\":false}},").unwrap();
    writeln!(
        output,
        "  \"next_gate\": \"SOURCE_LOCKED_LONGITUDINAL_INTERVENTION_CONTRACT_REQUIRED\""
    )
    .unwrap();
    writeln!(output, "}}").unwrap();
    output
}

fn print_report(report: &Report) {
    println!(
        "PASS solver refinement: {:.3e}",
        report.solver_refinement_error
    );
    println!(
        "PASS moving-delay primitive: {:.3e}",
        report.primitive_delay_error
    );
    for level in report.levels {
        println!(
            "PASS FD n={} hz={:.1e} ha={:.1e}: J={:.3e} s={:.3e} K={:.3e} delta_g={:.3e}",
            level.intervals,
            level.z_step,
            level.parameter_step,
            level.jacobian_error,
            level.state_sensitivity_error,
            level.mixed_jacobian_error,
            level.metric_derivative_error,
        );
    }
    println!(
        "PASS nondegeneracy: weight={:.3e} packet={:.3e} speed={:.3e} K={:.3e} D1={:.3e} D2={:.3e}",
        report.contribution_norms[0],
        report.contribution_norms[1],
        report.contribution_norms[2],
        report.contribution_norms[3],
        report.contribution_norms[4],
        report.contribution_norms[5],
    );
    println!(
        "PASS ablations: frozen={:.3e} rate_gain={:.3e} shuffled={:.3e} omitK={:.3e} omitD1={:.3e} omitD2={:.3e}",
        report.ablation_errors[0],
        report.ablation_errors[1],
        report.ablation_errors[2],
        report.ablation_errors[3],
        report.ablation_errors[4],
        report.ablation_errors[5],
    );
    println!(
        "PASS SPD/covariance: detJ={:.3e} lambda_min_g={:.3e} cond_g={:.3e} congruence={:.3e}",
        report.determinant_j,
        report.minimum_eigenvalue_metric,
        report.metric_condition_number,
        report.coordinate_derivative_error,
    );
    println!(
        "RESULT: FORMAL_L0_NUMERICAL_WITNESS_PASS (synthetic fixed-mode fixture; biological ceiling unchanged)"
    );
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
    fn zero_and_frozen_delay_controls_are_exactly_inactive() {
        let fixture = fixture();
        let zero = analytic(
            fixture,
            fixture.parameters,
            zero_direction(),
            REFERENCE_INTERVALS,
            true,
        );
        let frozen = analytic(
            fixture,
            fixture.parameters,
            speed_direction(),
            REFERENCE_INTERVALS,
            false,
        );
        assert_eq!(matrix_norm(zero.metric_derivative), 0.0);
        assert_eq!(matrix_norm(frozen.metric_derivative), 0.0);
    }

    #[test]
    fn terminal_fisher_is_spd_and_pullback_is_not_diagonal_shortcut() {
        let fixture = fixture();
        let result = analytic(
            fixture,
            fixture.parameters,
            combined_direction(),
            REFERENCE_INTERVALS,
            true,
        );
        assert!(symmetric_eigenvalues(result.terminal_fisher)[0] > 0.0);
        assert!(symmetric_eigenvalues(result.pullback_metric)[0] > 0.0);
        assert!(result.pullback_metric[0][1].abs() > NONDEGENERACY_CUTOFF);
        assert!(result.pullback_metric[0][2].abs() > NONDEGENERACY_CUTOFF);
    }
}
