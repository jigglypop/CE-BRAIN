//! Binary64 witness for the marked-CTMC formulas (21.54k)--(21.54s).
//!
//! A synthetic one-jump process separates the metric coordinate z from
//! the slow deformation coordinate theta. Exact path, terminal-state,
//! and noisy-output Fisher information are compared, and the slow
//! derivative of the marginal output metric is checked independently.
//! This is a formal fixture, not a calibrated model of synaptic turnover
//! and not biological evidence.

const Z0: f64 = 0.2;
const THETA0: f64 = 0.3;
const HORIZON: f64 = 1.4;
const LAMBDA0: f64 = 0.8;
const LOG_HAZARD_Z: f64 = 0.6;
const LOG_HAZARD_THETA: f64 = 0.3;
const LOGIT_MARK_INTERCEPT: f64 = -0.25;
const LOGIT_MARK_Z: f64 = 0.6;
const LOGIT_MARK_THETA: f64 = 0.7;
const EMISSION_ONE: [f64; 3] = [0.10, 0.85, 0.35];

const ALGEBRA_TOLERANCE: f64 = 2.0e-13;
const SCORE_FD_TOLERANCE: f64 = 2.0e-10;
const METRIC_FD_TOLERANCE: f64 = 2.0e-10;
const ABLATION_SEPARATION_MIN: f64 = 1.0e-3;
const PROBABILITY_MARGIN: f64 = 1.0e-12;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum StopCode {
    CommonPathSupportChanged,
    NonPositiveRateOrProbability,
    NonFinite,
}

impl StopCode {
    fn as_str(self) -> &'static str {
        match self {
            Self::CommonPathSupportChanged => "STOP_COMMON_PATH_SUPPORT_CHANGED",
            Self::NonPositiveRateOrProbability => "STOP_NONPOSITIVE_RATE_OR_PROBABILITY",
            Self::NonFinite => "STOP_NONFINITE_MODEL",
        }
    }
}

#[derive(Clone, Copy)]
struct Model {
    lambda: f64,
    exposure: f64,
    mark_p: f64,
    survival: f64,
    event: f64,
    event_z: f64,
    event_theta: f64,
    event_z_theta: f64,
    mark_z: f64,
    mark_theta: f64,
    mark_z_theta: f64,
    weights: [f64; 3],
    weights_z: [f64; 3],
    weights_theta: [f64; 3],
    weights_z_theta: [f64; 3],
}

#[derive(Clone, Copy)]
struct PathMoments {
    probability: [f64; 3],
    first: [f64; 3],
    second: [f64; 3],
}

#[derive(Clone, Copy)]
struct OutputMoments {
    probability: [f64; 2],
    first: [f64; 2],
    second: [f64; 2],
}

#[derive(Clone, Copy)]
struct OutputGeometry {
    probability_one: f64,
    probability_z: f64,
    probability_theta: f64,
    probability_z_theta: f64,
    fisher: f64,
    fisher_theta: f64,
}

#[derive(Clone, Copy)]
enum Mark {
    Persistent,
    Eliminated,
}

#[derive(Clone, Copy)]
enum Record {
    Censored,
    Event { time: f64, mark: Mark },
}

fn logistic(x: f64) -> f64 {
    if x >= 0.0 {
        1.0 / (1.0 + (-x).exp())
    } else {
        let e = x.exp();
        e / (1.0 + e)
    }
}

fn model(z: f64, theta: f64) -> Result<Model, StopCode> {
    let lambda = LAMBDA0 * (LOG_HAZARD_Z * z + LOG_HAZARD_THETA * theta).exp();
    let exposure = lambda * HORIZON;
    let survival = (-exposure).exp();
    let event = 1.0 - survival;
    let mark_p = logistic(LOGIT_MARK_INTERCEPT + LOGIT_MARK_Z * z + LOGIT_MARK_THETA * theta);

    let finite = [lambda, exposure, survival, event, mark_p]
        .iter()
        .all(|value| value.is_finite());
    if !finite {
        return Err(StopCode::NonFinite);
    }
    if lambda <= 0.0
        || survival <= PROBABILITY_MARGIN
        || event <= PROBABILITY_MARGIN
        || mark_p <= PROBABILITY_MARGIN
        || mark_p >= 1.0 - PROBABILITY_MARGIN
    {
        return Err(StopCode::NonPositiveRateOrProbability);
    }

    let event_z = LOG_HAZARD_Z * exposure * survival;
    let event_theta = LOG_HAZARD_THETA * exposure * survival;
    let event_z_theta = LOG_HAZARD_Z * LOG_HAZARD_THETA * exposure * survival * (1.0 - exposure);
    let mark_variance = mark_p * (1.0 - mark_p);
    let mark_z = LOGIT_MARK_Z * mark_variance;
    let mark_theta = LOGIT_MARK_THETA * mark_variance;
    let mark_z_theta = LOGIT_MARK_Z * LOGIT_MARK_THETA * mark_variance * (1.0 - 2.0 * mark_p);

    let weights = [survival, event * mark_p, event * (1.0 - mark_p)];
    let weights_z = [
        -event_z,
        event_z * mark_p + event * mark_z,
        event_z * (1.0 - mark_p) - event * mark_z,
    ];
    let weights_theta = [
        -event_theta,
        event_theta * mark_p + event * mark_theta,
        event_theta * (1.0 - mark_p) - event * mark_theta,
    ];
    let weights_z_theta = [
        -event_z_theta,
        event_z_theta * mark_p + event_z * mark_theta + event_theta * mark_z + event * mark_z_theta,
        event_z_theta * (1.0 - mark_p)
            - event_z * mark_theta
            - event_theta * mark_z
            - event * mark_z_theta,
    ];

    Ok(Model {
        lambda,
        exposure,
        mark_p,
        survival,
        event,
        event_z,
        event_theta,
        event_z_theta,
        mark_z,
        mark_theta,
        mark_z_theta,
        weights,
        weights_z,
        weights_theta,
        weights_z_theta,
    })
}

fn path_moments(m: Model) -> PathMoments {
    // With u=lambda*t, these are the integrals of
    // exp(-u), exp(-u)(1-u), and exp(-u)(1-u)^2 on [0,L].
    let a0 = m.event;
    let a1 = m.exposure * m.survival;
    let a2 = 1.0 - (1.0 + m.exposure * m.exposure) * m.survival;
    let persistent_score = LOGIT_MARK_Z * (1.0 - m.mark_p);
    let eliminated_score = -LOGIT_MARK_Z * m.mark_p;

    PathMoments {
        probability: m.weights,
        first: [
            -LOG_HAZARD_Z * m.exposure * m.survival,
            m.mark_p * (LOG_HAZARD_Z * a1 + persistent_score * a0),
            (1.0 - m.mark_p) * (LOG_HAZARD_Z * a1 + eliminated_score * a0),
        ],
        second: [
            LOG_HAZARD_Z.powi(2) * m.exposure.powi(2) * m.survival,
            m.mark_p
                * (LOG_HAZARD_Z.powi(2) * a2
                    + 2.0 * LOG_HAZARD_Z * persistent_score * a1
                    + persistent_score.powi(2) * a0),
            (1.0 - m.mark_p)
                * (LOG_HAZARD_Z.powi(2) * a2
                    + 2.0 * LOG_HAZARD_Z * eliminated_score * a1
                    + eliminated_score.powi(2) * a0),
        ],
    }
}

fn path_fisher(m: Model) -> f64 {
    m.event * (LOG_HAZARD_Z.powi(2) + LOGIT_MARK_Z.powi(2) * m.mark_p * (1.0 - m.mark_p))
}

fn expected_negative_path_hessian(m: Model) -> f64 {
    let censored_hazard = LOG_HAZARD_Z.powi(2) * m.exposure * m.survival;
    let event_hazard = LOG_HAZARD_Z.powi(2) * (1.0 - (m.exposure + 1.0) * m.survival);
    let mark = m.event * LOGIT_MARK_Z.powi(2) * m.mark_p * (1.0 - m.mark_p);
    censored_hazard + event_hazard + mark
}

fn path_fisher_theta(m: Model) -> f64 {
    let bracket = LOG_HAZARD_Z.powi(2) + LOGIT_MARK_Z.powi(2) * m.mark_p * (1.0 - m.mark_p);
    m.event_theta * bracket + m.event * LOGIT_MARK_Z.powi(2) * m.mark_theta * (1.0 - 2.0 * m.mark_p)
}

fn terminal_fisher(m: Model) -> f64 {
    (0..3)
        .map(|state| m.weights_z[state].powi(2) / m.weights[state])
        .sum()
}

fn output_moments(path: PathMoments) -> OutputMoments {
    let mut result = OutputMoments {
        probability: [0.0; 2],
        first: [0.0; 2],
        second: [0.0; 2],
    };
    for outcome in 0..2 {
        for state in 0..3 {
            let emission = if outcome == 1 {
                EMISSION_ONE[state]
            } else {
                1.0 - EMISSION_ONE[state]
            };
            result.probability[outcome] += emission * path.probability[state];
            result.first[outcome] += emission * path.first[state];
            result.second[outcome] += emission * path.second[state];
        }
    }
    result
}

fn output_geometry(m: Model) -> OutputGeometry {
    let delta = EMISSION_ONE[1] - EMISSION_ONE[2];
    let marked_emission = EMISSION_ONE[2] + delta * m.mark_p;
    let probability_one = EMISSION_ONE[0] + m.event * (marked_emission - EMISSION_ONE[0]);
    let probability_z =
        m.event_z * (marked_emission - EMISSION_ONE[0]) + m.event * delta * m.mark_z;
    let probability_theta =
        m.event_theta * (marked_emission - EMISSION_ONE[0]) + m.event * delta * m.mark_theta;
    let probability_z_theta = m.event_z_theta * (marked_emission - EMISSION_ONE[0])
        + delta * (m.event_z * m.mark_theta + m.event_theta * m.mark_z + m.event * m.mark_z_theta);
    let denominator = probability_one * (1.0 - probability_one);
    let fisher = probability_z.powi(2) / denominator;
    let fisher_theta = 2.0 * probability_z * probability_z_theta / denominator
        - probability_z.powi(2) * probability_theta * (1.0 - 2.0 * probability_one)
            / denominator.powi(2);
    OutputGeometry {
        probability_one,
        probability_z,
        probability_theta,
        probability_z_theta,
        fisher,
        fisher_theta,
    }
}

fn output_fisher_from_moments(output: OutputMoments) -> f64 {
    (0..2)
        .map(|outcome| output.first[outcome].powi(2) / output.probability[outcome])
        .sum()
}

fn missing_information(output: OutputMoments) -> f64 {
    (0..2)
        .map(|outcome| {
            output.second[outcome] - output.first[outcome].powi(2) / output.probability[outcome]
        })
        .sum()
}

fn log_path_likelihood(z: f64, theta: f64, record: Record) -> Result<f64, StopCode> {
    let m = model(z, theta)?;
    Ok(match record {
        Record::Censored => -m.lambda * HORIZON,
        Record::Event { time, mark } => {
            let mark_probability = match mark {
                Mark::Persistent => m.mark_p,
                Mark::Eliminated => 1.0 - m.mark_p,
            };
            m.lambda.ln() - m.lambda * time + mark_probability.ln()
        }
    })
}

fn analytic_path_score(m: Model, record: Record) -> f64 {
    match record {
        Record::Censored => -LOG_HAZARD_Z * m.exposure,
        Record::Event { time, mark } => {
            let hazard = LOG_HAZARD_Z * (1.0 - m.lambda * time);
            let mark_score = match mark {
                Mark::Persistent => LOGIT_MARK_Z * (1.0 - m.mark_p),
                Mark::Eliminated => -LOGIT_MARK_Z * m.mark_p,
            };
            hazard + mark_score
        }
    }
}

fn five_point_first<F>(x: f64, h: f64, f: F) -> f64
where
    F: Fn(f64) -> f64,
{
    (f(x - 2.0 * h) - 8.0 * f(x - h) + 8.0 * f(x + h) - f(x + 2.0 * h)) / (12.0 * h)
}

fn five_point_second<F>(x: f64, h: f64, f: F) -> f64
where
    F: Fn(f64) -> f64,
{
    (-f(x + 2.0 * h) + 16.0 * f(x + h) - 30.0 * f(x) + 16.0 * f(x - h) - f(x - 2.0 * h))
        / (12.0 * h * h)
}

fn marginal_log_probability(z: f64, theta: f64, outcome: usize) -> f64 {
    let geometry = output_geometry(model(z, theta).expect("regular fixture"));
    if outcome == 1 {
        geometry.probability_one.ln()
    } else {
        (1.0 - geometry.probability_one).ln()
    }
}

fn marginal_score_z(geometry: OutputGeometry, outcome: usize) -> f64 {
    if outcome == 1 {
        geometry.probability_z / geometry.probability_one
    } else {
        -geometry.probability_z / (1.0 - geometry.probability_one)
    }
}

fn marginal_score_theta(geometry: OutputGeometry, outcome: usize) -> f64 {
    if outcome == 1 {
        geometry.probability_theta / geometry.probability_one
    } else {
        -geometry.probability_theta / (1.0 - geometry.probability_one)
    }
}

fn marginal_mixed_score(geometry: OutputGeometry, outcome: usize) -> f64 {
    if outcome == 1 {
        geometry.probability_z_theta / geometry.probability_one
            - geometry.probability_z * geometry.probability_theta / geometry.probability_one.powi(2)
    } else {
        -geometry.probability_z_theta / (1.0 - geometry.probability_one)
            - geometry.probability_z * geometry.probability_theta
                / (1.0 - geometry.probability_one).powi(2)
    }
}

fn posterior_mixed_score(m: Model, outcome: usize) -> f64 {
    let mut normalizer = 0.0;
    let mut expected_a = 0.0;
    let mut expected_b = 0.0;
    let mut expected_ab = 0.0;
    let mut expected_da = 0.0;
    for state in 0..3 {
        let emission = if outcome == 1 {
            EMISSION_ONE[state]
        } else {
            1.0 - EMISSION_ONE[state]
        };
        let joint = m.weights[state] * emission;
        let a = m.weights_z[state] / m.weights[state];
        let b = m.weights_theta[state] / m.weights[state];
        let da = m.weights_z_theta[state] / m.weights[state] - a * b;
        normalizer += joint;
        expected_a += joint * a;
        expected_b += joint * b;
        expected_ab += joint * a * b;
        expected_da += joint * da;
    }
    expected_a /= normalizer;
    expected_b /= normalizer;
    expected_ab /= normalizer;
    expected_da /= normalizer;
    expected_da + expected_ab - expected_a * expected_b
}

fn derivative_from_score_identity(geometry: OutputGeometry) -> (f64, f64) {
    let probabilities = [1.0 - geometry.probability_one, geometry.probability_one];
    let mut full = 0.0;
    let mut without_moving_measure = 0.0;
    for outcome in 0..2 {
        let u = marginal_score_z(geometry, outcome);
        let v = marginal_score_theta(geometry, outcome);
        let c = marginal_mixed_score(geometry, outcome);
        without_moving_measure += probabilities[outcome] * 2.0 * u * c;
        full += probabilities[outcome] * (2.0 * u * c + u * u * v);
    }
    (full, without_moving_measure)
}

fn no_kernel_path_fisher(m: Model) -> f64 {
    m.event * LOG_HAZARD_Z.powi(2)
}

fn no_kernel_output_fisher(m: Model) -> f64 {
    let delta = EMISSION_ONE[1] - EMISSION_ONE[2];
    let marked_emission = EMISSION_ONE[2] + delta * m.mark_p;
    let probability_one = EMISSION_ONE[0] + m.event * (marked_emission - EMISSION_ONE[0]);
    let probability_z = m.event_z * (marked_emission - EMISSION_ONE[0]);
    probability_z.powi(2) / (probability_one * (1.0 - probability_one))
}

fn wrong_score_means(m: Model) -> (f64, f64) {
    // Removing the compensator gives zero score to censoring and +a_z at an event.
    let omitted_survival = m.event * LOG_HAZARD_Z;
    // Reversing its sign adds a second compensator contribution.
    let reversed_survival = 2.0 * m.event * LOG_HAZARD_Z;
    (omitted_survival, reversed_survival)
}

fn support_mask(pi: f64) -> u8 {
    let mut mask = 0b001; // the no-jump path
    if pi > 0.0 {
        mask |= 0b010;
    }
    if pi < 1.0 {
        mask |= 0b100;
    }
    mask
}

fn bad_mark_probability(theta: f64) -> f64 {
    let positive_part = (theta - THETA0).max(0.0);
    positive_part / (1.0 + positive_part)
}

fn check_bad_support_stencil(theta: f64, h: f64) -> Result<(), StopCode> {
    let masks = [
        support_mask(bad_mark_probability(theta - 2.0 * h)),
        support_mask(bad_mark_probability(theta - h)),
        support_mask(bad_mark_probability(theta)),
        support_mask(bad_mark_probability(theta + h)),
        support_mask(bad_mark_probability(theta + 2.0 * h)),
    ];
    if masks.iter().any(|mask| *mask != masks[0]) {
        Err(StopCode::CommonPathSupportChanged)
    } else {
        Ok(())
    }
}

fn max_abs(values: &[f64]) -> f64 {
    values.iter().fold(0.0, |acc, value| acc.max(value.abs()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn complete_path_score_and_fisher_close() {
        let m = model(Z0, THETA0).expect("regular fixture");
        let records = [
            Record::Censored,
            Record::Event {
                time: 0.45 * HORIZON,
                mark: Mark::Persistent,
            },
            Record::Event {
                time: 0.72 * HORIZON,
                mark: Mark::Eliminated,
            },
        ];
        let h = 1.0e-3;
        let mut score_errors = Vec::new();
        for record in records {
            let finite_difference = five_point_first(Z0, h, |z| {
                log_path_likelihood(z, THETA0, record).expect("common support")
            });
            score_errors.push(finite_difference - analytic_path_score(m, record));
        }
        assert!(max_abs(&score_errors) < SCORE_FD_TOLERANCE);

        let moments = path_moments(m);
        let mean_score: f64 = moments.first.iter().sum();
        let second_moment: f64 = moments.second.iter().sum();
        assert!(mean_score.abs() < ALGEBRA_TOLERANCE);
        assert!((second_moment - path_fisher(m)).abs() < ALGEBRA_TOLERANCE);
        assert!((expected_negative_path_hessian(m) - path_fisher(m)).abs() < ALGEBRA_TOLERANCE);

        let censored_negative_hessian = -five_point_second(Z0, h, |z| {
            log_path_likelihood(z, THETA0, Record::Censored).expect("common support")
        });
        assert!((censored_negative_hessian - LOG_HAZARD_Z.powi(2) * m.exposure).abs() < 2.0e-8);
    }

    #[test]
    fn marginal_score_and_missing_information_close() {
        let m = model(Z0, THETA0).expect("regular fixture");
        let path = path_moments(m);
        let output = output_moments(path);
        let geometry = output_geometry(m);
        let h = 1.0e-3;

        assert!((output.probability.iter().sum::<f64>() - 1.0).abs() < ALGEBRA_TOLERANCE);
        assert!(output.first.iter().sum::<f64>().abs() < ALGEBRA_TOLERANCE);
        for outcome in 0..2 {
            let fd = five_point_first(Z0, h, |z| marginal_log_probability(z, THETA0, outcome));
            let posterior_score = output.first[outcome] / output.probability[outcome];
            assert!((fd - posterior_score).abs() < SCORE_FD_TOLERANCE);
        }

        let marginal = output_fisher_from_moments(output);
        let missing = missing_information(output);
        assert!((marginal - geometry.fisher).abs() < ALGEBRA_TOLERANCE);
        assert!((path_fisher(m) - marginal - missing).abs() < ALGEBRA_TOLERANCE);
        assert!(missing > 0.0);
        assert!(terminal_fisher(m) > marginal);
        assert!(path_fisher(m) > terminal_fisher(m));

        let average_conditional_emission_fisher = 0.0;
        assert_eq!(average_conditional_emission_fisher, 0.0);
        assert!(marginal > 0.1);
    }

    #[test]
    fn slow_metric_derivative_and_posterior_identity_close() {
        let m = model(Z0, THETA0).expect("regular fixture");
        let geometry = output_geometry(m);
        let h = 1.0e-2;
        let path_fd = five_point_first(THETA0, h, |theta| {
            path_fisher(model(Z0, theta).expect("common support"))
        });
        let output_fd = five_point_first(THETA0, h, |theta| {
            output_geometry(model(Z0, theta).expect("common support")).fisher
        });
        let missing_fd = five_point_first(THETA0, h, |theta| {
            let mm = model(Z0, theta).expect("common support");
            path_fisher(mm) - output_geometry(mm).fisher
        });
        assert!((path_fd - path_fisher_theta(m)).abs() < METRIC_FD_TOLERANCE);
        assert!((output_fd - geometry.fisher_theta).abs() < METRIC_FD_TOLERANCE);
        assert!(
            (missing_fd - (path_fisher_theta(m) - geometry.fisher_theta)).abs()
                < METRIC_FD_TOLERANCE
        );

        for outcome in 0..2 {
            assert!(
                (posterior_mixed_score(m, outcome) - marginal_mixed_score(geometry, outcome)).abs()
                    < ALGEBRA_TOLERANCE
            );
        }
        let (from_identity, without_moving_measure) = derivative_from_score_identity(geometry);
        assert!((from_identity - geometry.fisher_theta).abs() < ALGEBRA_TOLERANCE);
        assert!((without_moving_measure - geometry.fisher_theta).abs() > ABLATION_SEPARATION_MIN);
    }

    #[test]
    fn ablations_and_support_change_fail_closed() {
        let m = model(Z0, THETA0).expect("regular fixture");
        let geometry = output_geometry(m);
        let no_kernel_path = no_kernel_path_fisher(m);
        let no_kernel_output = no_kernel_output_fisher(m);
        let (omitted_survival, reversed_survival) = wrong_score_means(m);

        assert!((path_fisher(m) - no_kernel_path) > ABLATION_SEPARATION_MIN);
        assert!((geometry.fisher - no_kernel_output) > ABLATION_SEPARATION_MIN);
        assert!(omitted_survival > ABLATION_SEPARATION_MIN);
        assert!(reversed_survival > omitted_survival);

        let stop = check_bad_support_stencil(THETA0, 1.0e-2)
            .expect_err("support-changing stencil must stop");
        assert_eq!(stop, StopCode::CommonPathSupportChanged);
        assert_eq!(stop.as_str(), "STOP_COMMON_PATH_SUPPORT_CHANGED");
    }

    #[test]
    fn report_fixture_values() {
        let m = model(Z0, THETA0).expect("regular fixture");
        let path = path_moments(m);
        let output = output_moments(path);
        let geometry = output_geometry(m);
        let missing = missing_information(output);
        let no_kernel_path = no_kernel_path_fisher(m);
        let no_kernel_output = no_kernel_output_fisher(m);
        let (omitted_survival, reversed_survival) = wrong_score_means(m);
        let stop = check_bad_support_stencil(THETA0, 1.0e-2).expect_err("expected stop");

        println!(
            concat!(
                "status=FORMAL_L0_CTMC_MARGINAL_FISHER_WITNESS_PASS ",
                "lambda={:.17e} exposure={:.17e} mark_p={:.17e} ",
                "weights=[{:.17e},{:.17e},{:.17e}] ",
                "path_fisher={:.17e} terminal_fisher={:.17e} ",
                "output_p1={:.17e} output_fisher={:.17e} missing={:.17e} ",
                "path_fisher_theta={:.17e} output_fisher_theta={:.17e} ",
                "missing_theta={:.17e} no_kernel_path={:.17e} ",
                "no_kernel_output={:.17e} omit_survival_mean={:.17e} ",
                "reverse_survival_mean={:.17e} stop={}"
            ),
            m.lambda,
            m.exposure,
            m.mark_p,
            m.weights[0],
            m.weights[1],
            m.weights[2],
            path_fisher(m),
            terminal_fisher(m),
            geometry.probability_one,
            geometry.fisher,
            missing,
            path_fisher_theta(m),
            geometry.fisher_theta,
            path_fisher_theta(m) - geometry.fisher_theta,
            no_kernel_path,
            no_kernel_output,
            omitted_survival,
            reversed_survival,
            stop.as_str()
        );
    }
}
