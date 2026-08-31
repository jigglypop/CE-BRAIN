//! Locked whole-cell predictive comparison for the Loewenstein 2015 table.
//!
//! The production endpoint is the next-session recataloguing of an
//! author-catalogued lateral protrusion, with filopodia not separated.
//! It is not mature-spine survival, synaptic-contact truth, or evidence
//! for a neural Riemannian metric. The implementation has a self-test
//! mode that structurally rejects a real-data path.

use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::f64::consts::{LN_2, PI, SQRT_2};
use std::fmt::Write as FmtWrite;
use std::fs;
use std::fs::OpenOptions;
use std::io::Write as IoWrite;
use std::path::{Path, PathBuf};

const EXPECTED_DATA_BYTES: usize = 569_938;
const EXPECTED_DATA_SHA256: &str =
    "2f6343606f62abb07b82491a71f0e4a4a898923d2bcf86aa4be8d596276d0062";
const EXPECTED_DICTIONARY_BYTES: usize = 4_850;
const EXPECTED_DICTIONARY_SHA256: &str =
    "995bdb601f6ff71cd5877486dfdd0576db576c15effcc8c52db560eb523d9657";
const EXPECTED_SOURCE_MANIFEST_SHA256: &str =
    "8209a09886b9322a02308f1dceff8d3805462c715135f79e28e1ab1e166b0630";
const EXPECTED_PREFLIGHT_AUDITOR_SHA256: &str =
    "a1b68ad6820055ba305058d7b5f646626df2842dd628a2401a95f785b4f600cc";
const EXPECTED_PREFLIGHT_RECEIPT_SHA256: &str =
    "2ce71a85cd25c5da3d26c74f14aeb6c2d23daafa7fe3485b77567ddce619f517";
const EXPECTED_ROWS: usize = 8_699;
const EXPECTED_CELLS: usize = 8;
const EXPECTED_DENDRITES: usize = 48;
const EXPECTED_PROTRUSION_IDS: usize = 3_688;
const EXPECTED_COMPARISON_ROWS: usize = 2_723;
const EXPECTED_COMPARISON_EVENTS: usize = 1_459;
const EXPECTED_ROWSET_SHA256: &str =
    "127bf184fe88cd04c727f39c719e7ee0931c6bd1264338bb1b9b30dfff38fcd4";
const EXPECTED_AGE_ROWS: [usize; 4] = [1_861, 557, 219, 86];
const EXPECTED_AGE_EVENTS: [usize; 4] = [1_122, 249, 66, 22];
const EXPECTED_CELL_ROWS: [usize; 8] = [529, 151, 404, 433, 419, 401, 353, 33];
const EXPECTED_CELL_EVENTS: [usize; 8] = [321, 72, 201, 231, 229, 202, 185, 18];
const EXPECTED_MODEL_FEATURE_ORDER: &str = "V0:intercept;V1:intercept,age_4d,age_8d,age_12d;V1Z:intercept,age_4d,age_8d,age_12d,z_offset_standardized;V2:intercept,age_4d,age_8d,age_12d,z_offset_standardized,log_intensity_standardized,shape_standardized,log_distance_standardized";
const EXPECTED_TOLERANCE_PROFILE: &str = "mode_score=1e-10;mode_step=1e-10;mode_iters=50;optimizer_internal_gradient=1e-8;optimizer_gate_gradient=1e-6;optimizer_iters=400;optimizer_evals=5000;armijo=1e-4;line_shrink=0.5;multistart_objective=1e-8;boundary_gain=1e-8;parameter_order=1e-3;cv_order=1e-5;cell_quadrature=1e-6;hessian_condition=1e10;beta_guard=20;sigma=[1e-6,10];sign_zero=1e-12;gain_epsilon=ln1.01;cell_guard=ln1.05;synthetic=C2015.21";

const LOG_EXPOSURE_DAYS: f64 = 1.386_294_361_119_890_6;
const FEATURE_SD_MIN: f64 = 1.0e-12;
const MODE_SCORE_TOL: f64 = 1.0e-10;
const MODE_STEP_TOL: f64 = 1.0e-10;
const MODE_MAX_ITERS: usize = 50;
const OPT_GRAD_TOL: f64 = 1.0e-6;
const OPT_INTERNAL_GRAD_TOL: f64 = 1.0e-8;
const OPT_MAX_ITERS: usize = 400;
const OPT_MAX_EVALS: usize = 5_000;
const ARMIJO_C1: f64 = 1.0e-4;
const LINE_SHRINK: f64 = 0.5;
const MULTISTART_OBJECTIVE_TOL: f64 = 1.0e-8;
const BOUNDARY_GAIN_TOL: f64 = 1.0e-8;
const PARAMETER_ORDER_TOL: f64 = 1.0e-3;
const CV_ORDER_TOL: f64 = 1.0e-5;
const CELL_QUADRATURE_TOL: f64 = 1.0e-6;
const HESSIAN_CONDITION_MAX: f64 = 1.0e10;
const BETA_GUARD: f64 = 20.0;
const SIGMA_LOWER: f64 = 1.0e-6;
const SIGMA_UPPER: f64 = 10.0;
const SIGN_ZERO_TOL: f64 = 1.0e-12;
const GAIN_EPSILON: f64 = 0.009_950_330_853_168_092;
const CELL_GUARD_KAPPA: f64 = 0.048_790_164_169_432_05;
const SYN_GH_WEIGHT_SUM_TOL: f64 = 2.0e-13;
const SYN_GH_MOMENT_TOL: f64 = 5.0e-11;
const SYN_GH_SYMMETRY_TOL: f64 = 2.0e-13;
const SYN_GAUSSIAN_LOG_TOL: f64 = 2.0e-12;
const SYN_ROW_DERIVATIVE_TOL: f64 = 2.0e-8;
const SYN_GRADIENT_SCALED_TOL: f64 = 2.0e-6;
const SYN_MODE_TOL: f64 = 2.0e-12;
const SYN_MODE_SCORE_SCALED_TOL: f64 = 2.0e-7;
const SYN_MODE_CURVATURE_SCALED_TOL: f64 = 2.0e-6;
const SYN_ONE_DENDRITE_TOL: f64 = 2.0e-9;
const SYN_TWO_DENDRITE_TOL: f64 = 2.0e-8;
const SYN_WRONG_ROWWISE_MIN: f64 = 1.0e-4;
const SYN_OPTIMIZER_PARAMETER_TOL: f64 = 2.0e-6;
const SYN_OPTIMIZER_SPREAD_TOL: f64 = 1.0e-10;
const SYN_HESSIAN_EIGEN_TOL: f64 = 2.0e-12;
const FIT_START_MARKER_BYTES: &[u8] = b"ce_npf_loewenstein_2015_fit_started_v1\n";

type AppResult<T> = Result<T, String>;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
struct EntityKey {
    cell: u8,
    dendrite: u16,
    protrusion: u32,
}

#[derive(Clone, Debug)]
struct RawRow {
    key: EntityKey,
    session: u8,
    intensity: f64,
    lambda1: f64,
    lambda2: f64,
    distance: f64,
    z_offset: f64,
}

#[derive(Clone, Debug)]
struct Observation {
    key: EntityKey,
    session: u8,
    age_bin: u8,
    event: u8,
    log_intensity: f64,
    shape: f64,
    log_distance: f64,
    z_offset: f64,
}

#[derive(Clone, Debug)]
struct Dataset {
    rows: Vec<Observation>,
    rowset_sha256: String,
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct DatasetSummary {
    rows: usize,
    events: usize,
    age_rows: [usize; 4],
    age_events: [usize; 4],
    cell_rows: [usize; 8],
    cell_events: [usize; 8],
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
enum ModelKind {
    V0,
    V1,
    V1Z,
    V2,
}

impl ModelKind {
    const ALL: [Self; 4] = [Self::V0, Self::V1, Self::V1Z, Self::V2];

    fn name(self) -> &'static str {
        match self {
            Self::V0 => "V0",
            Self::V1 => "V1",
            Self::V1Z => "V1Z",
            Self::V2 => "V2",
        }
    }

    fn dimension(self) -> usize {
        match self {
            Self::V0 => 1,
            Self::V1 => 4,
            Self::V1Z => 5,
            Self::V2 => 8,
        }
    }

    fn feature_names(self) -> &'static [&'static str] {
        match self {
            Self::V0 => &["intercept"],
            Self::V1 => &["intercept", "age_4d", "age_8d", "age_12d"],
            Self::V1Z => &[
                "intercept",
                "age_4d",
                "age_8d",
                "age_12d",
                "z_offset_standardized",
            ],
            Self::V2 => &[
                "intercept",
                "age_4d",
                "age_8d",
                "age_12d",
                "z_offset_standardized",
                "log_intensity_standardized",
                "shape_standardized",
                "log_distance_standardized",
            ],
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
enum VarianceFace {
    None,
    Cell,
    Dendrite,
    Both,
}

impl VarianceFace {
    const ALL: [Self; 4] = [Self::None, Self::Cell, Self::Dendrite, Self::Both];

    fn name(self) -> &'static str {
        match self {
            Self::None => "00",
            Self::Cell => "U0",
            Self::Dendrite => "0V",
            Self::Both => "UV",
        }
    }

    fn cell_active(self) -> bool {
        matches!(self, Self::Cell | Self::Both)
    }

    fn dendrite_active(self) -> bool {
        matches!(self, Self::Dendrite | Self::Both)
    }

    fn active_count(self) -> usize {
        self.cell_active() as usize + self.dendrite_active() as usize
    }
}

#[derive(Clone, Debug)]
struct Scaler {
    mean: [f64; 4],
    sd: [f64; 4],
}

#[derive(Clone, Debug)]
struct ModelRow {
    event: u8,
    x: Vec<f64>,
}

#[derive(Clone, Debug)]
struct ModelDendrite {
    id: u16,
    rows: Vec<ModelRow>,
}

#[derive(Clone, Debug)]
struct ModelCell {
    id: u8,
    dendrites: Vec<ModelDendrite>,
    row_count: usize,
}

#[derive(Clone, Debug)]
struct FoldDesign {
    heldout_cell: u8,
    model: ModelKind,
    scaler: Scaler,
    training_rowset_sha256: String,
    training_design_sha256: String,
    heldout_rowset_sha256: String,
    design_sha256: String,
    training: Vec<ModelCell>,
    heldout: ModelCell,
    training_rows: usize,
}

#[derive(Clone, Debug)]
struct Quadrature {
    order: usize,
    nodes: Vec<f64>,
    weights: Vec<f64>,
}

#[derive(Clone, Debug)]
struct Eval {
    objective: f64,
    gradient: Vec<f64>,
    log_likelihood: f64,
}

#[derive(Clone, Debug)]
struct Optimized {
    parameters: Vec<f64>,
    objective: f64,
    log_likelihood: f64,
    gradient: Vec<f64>,
    gradient_inf: f64,
    projected_gradient_inf: f64,
    iterations: usize,
    evaluations: usize,
}

#[derive(Clone, Debug)]
struct FaceFit {
    face: VarianceFace,
    order: usize,
    optimum: Optimized,
    converged_starts: usize,
    best_three_spread: f64,
    solutions: Vec<Optimized>,
}

#[derive(Clone, Debug)]
struct FaceDiagnostic {
    face: VarianceFace,
    order: usize,
    parameters: Vec<f64>,
    objective: f64,
    log_likelihood: f64,
    converged_starts: usize,
    best_three_spread: f64,
    iterations: usize,
    evaluations: usize,
    gradient: Vec<f64>,
    gradient_inf: f64,
    projected_gradient_inf: f64,
}

#[derive(Clone, Debug)]
struct FoldModelFit {
    heldout_cell: u8,
    model: ModelKind,
    face_q15: VarianceFace,
    face_q25: VarianceFace,
    face: VarianceFace,
    parameters_q15: Vec<f64>,
    parameters_q25: Vec<f64>,
    parameters_final: Vec<f64>,
    train_log_likelihood_q15: f64,
    train_log_likelihood_q25: f64,
    train_log_likelihood_final: f64,
    heldout_log_likelihood_q15: f64,
    heldout_log_likelihood_q25: f64,
    heldout_log_likelihood_final: f64,
    heldout_log_likelihood_audit: f64,
    final_order: usize,
    audit_order: usize,
    q15_converged_starts: usize,
    q25_converged_starts: usize,
    q15_best_three_spread: f64,
    q25_best_three_spread: f64,
    q15_iterations: usize,
    q25_iterations: usize,
    q15_evaluations: usize,
    q25_evaluations: usize,
    gradient_q25: Vec<f64>,
    gradient_inf_q25: f64,
    projected_gradient_inf_q25: f64,
    hessian_condition_q25: f64,
    parameter_order_delta: f64,
    initial_q25_q35_cell_delta: f64,
    fallback_parameter_delta: Option<f64>,
    quadrature_cell_delta: f64,
    gradient_final: Vec<f64>,
    gradient_inf_final: f64,
    projected_gradient_inf_final: f64,
    training_rows: usize,
    heldout_rows: usize,
    scaler: Scaler,
    training_rowset_sha256: String,
    training_design_sha256: String,
    heldout_rowset_sha256: String,
    design_sha256: String,
    face_diagnostics_q15: Vec<FaceDiagnostic>,
    face_diagnostics_q25: Vec<FaceDiagnostic>,
    face_diagnostics_fallback: Vec<FaceDiagnostic>,
}

#[derive(Clone, Debug)]
struct ComparisonDecision {
    name: &'static str,
    reduced: ModelKind,
    augmented: ModelKind,
    pooled_delta: f64,
    macro_delta: f64,
    cell_deltas: [f64; 8],
    positive_cells: usize,
    negative_cells: usize,
    decision: &'static str,
    gain_cell_guard_fail: bool,
    gain_pooled_margin_fail: bool,
    gain_macro_margin_fail: bool,
    gain_sign_count_fail: bool,
    loss_cell_guard_fail: bool,
    loss_pooled_margin_fail: bool,
    loss_macro_margin_fail: bool,
    loss_sign_count_fail: bool,
}

#[derive(Clone, Debug)]
struct FitReport {
    folds: Vec<FoldModelFit>,
    comparison_rows: usize,
    cell_rows: [usize; 8],
    pooled_scores_q15: [f64; 4],
    pooled_scores_q25: [f64; 4],
    pooled_scores: [f64; 4],
    macro_scores: [f64; 4],
    per_cell_scores: [[f64; 8]; 4],
    comparisons: Vec<ComparisonDecision>,
}

#[derive(Clone, Debug)]
struct InnerResult {
    log_integral: f64,
    beta_score: Vec<f64>,
    log_sigma_v_score: f64,
    u_score: f64,
    u_second: f64,
}

#[derive(Clone, Debug)]
struct OuterPoint {
    log_integrand: f64,
    derivative: f64,
    second: f64,
    beta_score: Vec<f64>,
    log_sigma_v_score: f64,
}

#[derive(Clone, Debug)]
struct CellIntegral {
    log_likelihood: f64,
    beta_score: Vec<f64>,
    log_sigma_u_score: f64,
    log_sigma_v_score: f64,
}

#[derive(Clone, Debug)]
struct RowLikelihood {
    log_value: f64,
    score: f64,
    second: f64,
}

// Minimal dependency-free SHA-256 used for source and rowset commitments.
#[derive(Clone)]
struct Sha256 {
    state: [u32; 8],
    buffer: [u8; 64],
    buffer_len: usize,
    bit_len: u64,
}

impl Sha256 {
    fn new() -> Self {
        Self {
            state: [
                0x6a09e667,
                0xbb67ae85,
                0x3c6ef372,
                0xa54ff53a,
                0x510e527f,
                0x9b05688c,
                0x1f83d9ab,
                0x5be0cd19,
            ],
            buffer: [0; 64],
            buffer_len: 0,
            bit_len: 0,
        }
    }

    fn update(&mut self, mut bytes: &[u8]) {
        while !bytes.is_empty() {
            let take = (64 - self.buffer_len).min(bytes.len());
            self.buffer[self.buffer_len..self.buffer_len + take].copy_from_slice(&bytes[..take]);
            self.buffer_len += take;
            bytes = &bytes[take..];
            if self.buffer_len == 64 {
                let block = self.buffer;
                self.compress(&block);
                self.bit_len = self.bit_len.wrapping_add(512);
                self.buffer_len = 0;
            }
        }
    }

    fn finalize(mut self) -> [u8; 32] {
        self.bit_len = self.bit_len.wrapping_add((self.buffer_len as u64) * 8);
        self.buffer[self.buffer_len] = 0x80;
        self.buffer_len += 1;
        if self.buffer_len > 56 {
            for byte in &mut self.buffer[self.buffer_len..] {
                *byte = 0;
            }
            let block = self.buffer;
            self.compress(&block);
            self.buffer = [0; 64];
        } else {
            for byte in &mut self.buffer[self.buffer_len..56] {
                *byte = 0;
            }
        }
        self.buffer[56..64].copy_from_slice(&self.bit_len.to_be_bytes());
        let block = self.buffer;
        self.compress(&block);
        let mut output = [0u8; 32];
        for (index, value) in self.state.iter().enumerate() {
            output[index * 4..index * 4 + 4].copy_from_slice(&value.to_be_bytes());
        }
        output
    }

    fn compress(&mut self, block: &[u8; 64]) {
        const K: [u32; 64] = [
            0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
            0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
            0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
            0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
            0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
            0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
            0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
            0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
            0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
            0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
            0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
        ];
        let mut w = [0u32; 64];
        for index in 0..16 {
            w[index] = u32::from_be_bytes([
                block[index * 4],
                block[index * 4 + 1],
                block[index * 4 + 2],
                block[index * 4 + 3],
            ]);
        }
        for index in 16..64 {
            let s0 = w[index - 15].rotate_right(7)
                ^ w[index - 15].rotate_right(18)
                ^ (w[index - 15] >> 3);
            let s1 = w[index - 2].rotate_right(17)
                ^ w[index - 2].rotate_right(19)
                ^ (w[index - 2] >> 10);
            w[index] = w[index - 16]
                .wrapping_add(s0)
                .wrapping_add(w[index - 7])
                .wrapping_add(s1);
        }
        let mut a = self.state[0];
        let mut b = self.state[1];
        let mut c = self.state[2];
        let mut d = self.state[3];
        let mut e = self.state[4];
        let mut f = self.state[5];
        let mut g = self.state[6];
        let mut h = self.state[7];
        for index in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let choose = (e & f) ^ ((!e) & g);
            let temp1 = h
                .wrapping_add(s1)
                .wrapping_add(choose)
                .wrapping_add(K[index])
                .wrapping_add(w[index]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let majority = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(majority);
            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }
        self.state[0] = self.state[0].wrapping_add(a);
        self.state[1] = self.state[1].wrapping_add(b);
        self.state[2] = self.state[2].wrapping_add(c);
        self.state[3] = self.state[3].wrapping_add(d);
        self.state[4] = self.state[4].wrapping_add(e);
        self.state[5] = self.state[5].wrapping_add(f);
        self.state[6] = self.state[6].wrapping_add(g);
        self.state[7] = self.state[7].wrapping_add(h);
    }
}

fn sha256_hex(bytes: &[u8]) -> String {
    let mut hash = Sha256::new();
    hash.update(bytes);
    let digest = hash.finalize();
    let mut output = String::with_capacity(64);
    for byte in digest {
        write!(&mut output, "{byte:02x}").unwrap();
    }
    output
}

fn ensure_finite(value: f64, context: &str) -> AppResult<f64> {
    if value.is_finite() {
        Ok(value)
    } else {
        Err(format!("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:{context}"))
    }
}

fn log_sum_exp(values: &[f64]) -> AppResult<f64> {
    if values.is_empty() {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:empty_logsumexp".to_string());
    }
    let maximum = values.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    if !maximum.is_finite() {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:logsumexp_max".to_string());
    }
    let sum = values.iter().map(|value| (*value - maximum).exp()).sum::<f64>();
    ensure_finite(maximum + sum.ln(), "logsumexp")
}

fn row_likelihood(event: u8, eta: f64) -> AppResult<RowLikelihood> {
    if event > 1 || !eta.is_finite() {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:row_input".to_string());
    }
    let xi = LOG_EXPOSURE_DAYS + eta;
    let lambda = if xi > 700.0 {
        f64::INFINITY
    } else {
        xi.exp()
    };
    if event == 0 {
        if !lambda.is_finite() {
            return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:no_event_overflow".to_string());
        }
        return Ok(RowLikelihood {
            log_value: -lambda,
            score: -lambda,
            second: -lambda,
        });
    }
    if lambda == 0.0 {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:event_underflow".to_string());
    }
    if !lambda.is_finite() {
        return Ok(RowLikelihood {
            log_value: 0.0,
            score: 0.0,
            second: 0.0,
        });
    }
    let log_value = if lambda <= LN_2 {
        (-(-lambda).exp_m1()).ln()
    } else {
        (-(-lambda).exp()).ln_1p()
    };
    let (score, second) = if lambda < 1.0e-3 {
        (
            1.0 - 0.5 * lambda + lambda * lambda / 12.0,
            -0.5 * lambda + lambda * lambda / 6.0,
        )
    } else {
        let q = (-lambda).exp();
        let denominator = 1.0 - q;
        (
            lambda * q / denominator,
            lambda * q * (1.0 - lambda - q) / (denominator * denominator),
        )
    };
    ensure_finite(log_value, "event_log")?;
    ensure_finite(score, "event_score")?;
    ensure_finite(second, "event_second")?;
    Ok(RowLikelihood {
        log_value,
        score,
        second,
    })
}

fn dot(left: &[f64], right: &[f64]) -> f64 {
    left.iter().zip(right).map(|(a, b)| a * b).sum()
}

fn inf_norm(values: &[f64]) -> f64 {
    values.iter().map(|value| value.abs()).fold(0.0, f64::max)
}

fn normal_log_density(value: f64, sigma: f64) -> AppResult<f64> {
    if !(sigma > 0.0) || !sigma.is_finite() {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:normal_sigma".to_string());
    }
    let ratio = value / sigma;
    ensure_finite(-0.5 * ratio * ratio - sigma.ln() - 0.5 * (2.0 * PI).ln(), "normal")
}

fn jacobi_eigen(mut matrix: Vec<Vec<f64>>) -> AppResult<(Vec<f64>, Vec<Vec<f64>>)> {
    let n = matrix.len();
    if n == 0 || matrix.iter().any(|row| row.len() != n) {
        return Err("STOP_GH_SELF_TEST:jacobi_shape".to_string());
    }
    let mut vectors = vec![vec![0.0; n]; n];
    for index in 0..n {
        vectors[index][index] = 1.0;
    }
    let tolerance = 2.0e-15;
    let max_rotations = 200 * n * n;
    for _ in 0..max_rotations {
        let mut p = 0usize;
        let mut q = 1usize.min(n - 1);
        let mut maximum = 0.0;
        for row in 0..n {
            for column in row + 1..n {
                let value = matrix[row][column].abs();
                if value > maximum {
                    maximum = value;
                    p = row;
                    q = column;
                }
            }
        }
        if maximum <= tolerance {
            let eigenvalues = (0..n).map(|index| matrix[index][index]).collect();
            return Ok((eigenvalues, vectors));
        }
        let app = matrix[p][p];
        let aqq = matrix[q][q];
        let apq = matrix[p][q];
        let angle = 0.5 * (2.0 * apq).atan2(aqq - app);
        let cosine = angle.cos();
        let sine = angle.sin();
        for k in 0..n {
            if k != p && k != q {
                let akp = matrix[k][p];
                let akq = matrix[k][q];
                let new_kp = cosine * akp - sine * akq;
                let new_kq = sine * akp + cosine * akq;
                matrix[k][p] = new_kp;
                matrix[p][k] = new_kp;
                matrix[k][q] = new_kq;
                matrix[q][k] = new_kq;
            }
        }
        matrix[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq
            + sine * sine * aqq;
        matrix[q][q] = sine * sine * app + 2.0 * sine * cosine * apq
            + cosine * cosine * aqq;
        matrix[p][q] = 0.0;
        matrix[q][p] = 0.0;
        for row in 0..n {
            let vip = vectors[row][p];
            let viq = vectors[row][q];
            vectors[row][p] = cosine * vip - sine * viq;
            vectors[row][q] = sine * vip + cosine * viq;
        }
    }
    Err("STOP_GH_SELF_TEST:jacobi_nonconvergence".to_string())
}

impl Quadrature {
    fn gauss_hermite(order: usize) -> AppResult<Self> {
        if order < 2 {
            return Err("STOP_GH_SELF_TEST:order".to_string());
        }
        let mut jacobi = vec![vec![0.0; order]; order];
        for index in 0..order - 1 {
            let value = (((index + 1) as f64) / 2.0).sqrt();
            jacobi[index][index + 1] = value;
            jacobi[index + 1][index] = value;
        }
        let (eigenvalues, eigenvectors) = jacobi_eigen(jacobi)?;
        let mut pairs = (0..order)
            .map(|index| {
                let node = eigenvalues[index];
                let weight = PI.sqrt() * eigenvectors[0][index] * eigenvectors[0][index];
                (node, weight)
            })
            .collect::<Vec<_>>();
        pairs.sort_by(|left, right| left.0.total_cmp(&right.0));
        let nodes = pairs.iter().map(|pair| pair.0).collect::<Vec<_>>();
        let weights = pairs.iter().map(|pair| pair.1).collect::<Vec<_>>();
        if weights.iter().any(|weight| !weight.is_finite() || *weight <= 0.0) {
            return Err("STOP_GH_SELF_TEST:weight".to_string());
        }
        let quadrature = Self {
            order,
            nodes,
            weights,
        };
        quadrature.self_check()?;
        Ok(quadrature)
    }

    fn self_check(&self) -> AppResult<()> {
        let raw_sum = self.weights.iter().sum::<f64>();
        if (raw_sum - PI.sqrt()).abs() > SYN_GH_WEIGHT_SUM_TOL {
            return Err(format!("STOP_GH_SELF_TEST:weight_sum:{raw_sum:.17e}"));
        }
        let normal_weights = self
            .weights
            .iter()
            .map(|weight| weight / PI.sqrt())
            .collect::<Vec<_>>();
        let moments = [0usize, 1, 2, 3, 4, 6];
        let expected = [1.0, 0.0, 1.0, 0.0, 3.0, 15.0];
        for (power, target) in moments.into_iter().zip(expected) {
            let observed = normal_weights
                .iter()
                .zip(&self.nodes)
                .map(|(weight, node)| weight * (SQRT_2 * node).powi(power as i32))
                .sum::<f64>();
            if (observed - target).abs() > SYN_GH_MOMENT_TOL {
                return Err(format!(
                    "STOP_GH_SELF_TEST:moment_{power}:{observed:.17e}:{target:.17e}"
                ));
            }
        }
        for index in 0..self.order {
            let mirror = self.order - 1 - index;
            if (self.nodes[index] + self.nodes[mirror]).abs() > SYN_GH_SYMMETRY_TOL
                || (self.weights[index] - self.weights[mirror]).abs() > SYN_GH_SYMMETRY_TOL
            {
                return Err("STOP_GH_SELF_TEST:symmetry".to_string());
            }
        }
        Ok(())
    }

    fn fingerprint(&self) -> String {
        let mut bytes = Vec::new();
        for (node, weight) in self.nodes.iter().zip(&self.weights) {
            bytes.extend_from_slice(format!("{node:.17e}|{weight:.17e}\n").as_bytes());
        }
        sha256_hex(&bytes)
    }
}

fn parse_u8(value: &str, name: &str) -> AppResult<u8> {
    value
        .parse::<u8>()
        .map_err(|_| format!("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:{name}:{value}"))
}

fn parse_u16(value: &str, name: &str) -> AppResult<u16> {
    value
        .parse::<u16>()
        .map_err(|_| format!("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:{name}:{value}"))
}

fn parse_u32(value: &str, name: &str) -> AppResult<u32> {
    value
        .parse::<u32>()
        .map_err(|_| format!("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:{name}:{value}"))
}

fn parse_f64(value: &str, name: &str) -> AppResult<f64> {
    let parsed = value
        .parse::<f64>()
        .map_err(|_| format!("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:{name}:{value}"))?;
    if parsed.is_finite() {
        Ok(parsed)
    } else {
        Err(format!("STOP_FEATURE_DOMAIN_OR_RANK:{name}:nonfinite"))
    }
}

fn parse_raw_rows(bytes: &[u8], enforce_source_lock: bool) -> AppResult<Vec<RawRow>> {
    if enforce_source_lock {
        if bytes.len() != EXPECTED_DATA_BYTES || sha256_hex(bytes) != EXPECTED_DATA_SHA256 {
            return Err("STOP_SOURCE_CONTENT_MISMATCH".to_string());
        }
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| "STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:utf8".to_string())?;
    let mut rows = Vec::new();
    for (line_index, source_line) in text.lines().enumerate() {
        let line = source_line.trim_end_matches('\r');
        if line.trim().is_empty() {
            continue;
        }
        let fields = line.split(',').collect::<Vec<_>>();
        if fields.len() != 13 {
            return Err(format!(
                "STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:columns:{}:{}",
                line_index + 1,
                fields.len()
            ));
        }
        let cell = parse_u8(fields[0], "cell")?;
        let dendrite = parse_u16(fields[1], "dendrite")?;
        let protrusion = parse_u32(fields[2], "protrusion")?;
        let session = parse_u8(fields[3], "session")?;
        if cell == 0 || dendrite == 0 || protrusion == 0 || !(1..=6).contains(&session) {
            return Err("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:index_domain".to_string());
        }
        let _spine_x = parse_f64(fields[8], "spine_x")?;
        let _spine_y = parse_f64(fields[9], "spine_y")?;
        let _dendrite_x = parse_f64(fields[10], "dendrite_x")?;
        let _dendrite_y = parse_f64(fields[11], "dendrite_y")?;
        rows.push(RawRow {
            key: EntityKey {
                cell,
                dendrite,
                protrusion,
            },
            session,
            intensity: parse_f64(fields[4], "intensity")?,
            lambda1: parse_f64(fields[5], "lambda1")?,
            lambda2: parse_f64(fields[6], "lambda2")?,
            distance: parse_f64(fields[7], "distance")?,
            z_offset: parse_f64(fields[12], "z_offset")?,
        });
    }
    if enforce_source_lock && rows.len() != EXPECTED_ROWS {
        return Err(format!(
            "STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:rows:{}",
            rows.len()
        ));
    }
    Ok(rows)
}

fn build_dataset(raw_rows: &[RawRow], enforce_source_lock: bool) -> AppResult<Dataset> {
    let mut keys = BTreeSet::new();
    let mut cells = BTreeSet::new();
    let mut dendrites = BTreeSet::new();
    let mut groups: BTreeMap<EntityKey, Vec<&RawRow>> = BTreeMap::new();
    for row in raw_rows {
        if !keys.insert((row.key, row.session)) {
            return Err("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:duplicate_key".to_string());
        }
        cells.insert(row.key.cell);
        dendrites.insert((row.key.cell, row.key.dendrite));
        groups.entry(row.key).or_default().push(row);
    }
    if enforce_source_lock
        && (cells.len() != EXPECTED_CELLS
            || dendrites.len() != EXPECTED_DENDRITES
            || groups.len() != EXPECTED_PROTRUSION_IDS)
    {
        return Err("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:entity_counts".to_string());
    }
    let mut observations = Vec::new();
    for (key, group) in &mut groups {
        group.sort_by_key(|row| row.session);
        let sessions = group.iter().map(|row| row.session).collect::<Vec<_>>();
        for pair in sessions.windows(2) {
            if pair[1] != pair[0] + 1 {
                return Err("STOP_SOURCE_SCHEMA_OR_COUNT_MISMATCH:presence_gap".to_string());
            }
        }
        let first = sessions[0];
        if first == 1 {
            continue;
        }
        for row in group.iter().copied() {
            if row.session >= 6 {
                continue;
            }
            if row.intensity <= 0.0 || row.distance <= 0.0 {
                return Err("STOP_FEATURE_DOMAIN_OR_RANK:nonpositive_log_input".to_string());
            }
            let shape_denominator = row.lambda1 + row.lambda2;
            if shape_denominator <= 0.0 {
                return Err("STOP_FEATURE_DOMAIN_OR_RANK:shape_denominator".to_string());
            }
            let event = (!sessions.contains(&(row.session + 1))) as u8;
            let observation = Observation {
                key: *key,
                session: row.session,
                age_bin: row.session - first,
                event,
                log_intensity: row.intensity.ln(),
                shape: (row.lambda1 - row.lambda2) / shape_denominator,
                log_distance: row.distance.ln(),
                z_offset: row.z_offset,
            };
            if observation.age_bin > 3
                || ![
                    observation.log_intensity,
                    observation.shape,
                    observation.log_distance,
                    observation.z_offset,
                ]
                .iter()
                .all(|value| value.is_finite())
            {
                return Err("STOP_FEATURE_DOMAIN_OR_RANK:observation".to_string());
            }
            observations.push(observation);
        }
    }
    observations.sort_by_key(|row| {
        (
            row.key.cell,
            row.key.dendrite,
            row.key.protrusion,
            row.session,
        )
    });
    let mut canonical = String::new();
    for row in &observations {
        writeln!(
            &mut canonical,
            "{}|{}|{}|{}|{}",
            row.key.cell, row.key.dendrite, row.key.protrusion, row.session, row.event
        )
        .unwrap();
    }
    let rowset_sha256 = sha256_hex(canonical.as_bytes());
    if enforce_source_lock {
        let event_count = observations.iter().map(|row| row.event as usize).sum::<usize>();
        let mut age_rows = [0usize; 4];
        let mut age_events = [0usize; 4];
        let mut cell_rows = [0usize; 8];
        let mut cell_events = [0usize; 8];
        for row in &observations {
            age_rows[row.age_bin as usize] += 1;
            age_events[row.age_bin as usize] += row.event as usize;
            cell_rows[(row.key.cell - 1) as usize] += 1;
            cell_events[(row.key.cell - 1) as usize] += row.event as usize;
        }
        if observations.len() != EXPECTED_COMPARISON_ROWS
            || event_count != EXPECTED_COMPARISON_EVENTS
            || rowset_sha256 != EXPECTED_ROWSET_SHA256
            || age_rows != EXPECTED_AGE_ROWS
            || age_events != EXPECTED_AGE_EVENTS
            || cell_rows != EXPECTED_CELL_ROWS
            || cell_events != EXPECTED_CELL_EVENTS
        {
            return Err("STOP_ROWSET_MISMATCH".to_string());
        }
    }
    Ok(Dataset {
        rows: observations,
        rowset_sha256,
    })
}

fn summarize_dataset(dataset: &Dataset) -> AppResult<DatasetSummary> {
    let mut summary = DatasetSummary {
        rows: dataset.rows.len(),
        events: 0,
        age_rows: [0; 4],
        age_events: [0; 4],
        cell_rows: [0; 8],
        cell_events: [0; 8],
    };
    for row in &dataset.rows {
        if row.age_bin > 3 || !(1..=8).contains(&row.key.cell) || row.event > 1 {
            return Err("STOP_ROWSET_MISMATCH:summary_domain".to_string());
        }
        let age = row.age_bin as usize;
        let cell = (row.key.cell - 1) as usize;
        let event = row.event as usize;
        summary.events += event;
        summary.age_rows[age] += 1;
        summary.age_events[age] += event;
        summary.cell_rows[cell] += 1;
        summary.cell_events[cell] += event;
    }
    let row_refs = dataset.rows.iter().collect::<Vec<_>>();
    if observation_rowset_hash(&row_refs) != dataset.rowset_sha256 {
        return Err("STOP_ROWSET_MISMATCH:summary_hash".to_string());
    }
    Ok(summary)
}

fn sample_scaler(rows: &[&Observation]) -> AppResult<Scaler> {
    if rows.len() < 2 {
        return Err("STOP_FEATURE_DOMAIN_OR_RANK:scaler_rows".to_string());
    }
    let mut mean = [0.0; 4];
    for row in rows {
        let values = [row.log_intensity, row.shape, row.log_distance, row.z_offset];
        for index in 0..4 {
            mean[index] += values[index];
        }
    }
    for value in &mut mean {
        *value /= rows.len() as f64;
    }
    let mut variance = [0.0; 4];
    for row in rows {
        let values = [row.log_intensity, row.shape, row.log_distance, row.z_offset];
        for index in 0..4 {
            variance[index] += (values[index] - mean[index]).powi(2);
        }
    }
    let mut sd = [0.0; 4];
    for index in 0..4 {
        sd[index] = (variance[index] / ((rows.len() - 1) as f64)).sqrt();
        if !sd[index].is_finite() || sd[index] <= FEATURE_SD_MIN {
            return Err(format!("STOP_FEATURE_DOMAIN_OR_RANK:sd:{index}"));
        }
    }
    Ok(Scaler { mean, sd })
}

fn design_vector(row: &Observation, model: ModelKind, scaler: &Scaler) -> Vec<f64> {
    let mut design = Vec::with_capacity(model.dimension());
    design.push(1.0);
    if model != ModelKind::V0 {
        design.push((row.age_bin == 1) as u8 as f64);
        design.push((row.age_bin == 2) as u8 as f64);
        design.push((row.age_bin == 3) as u8 as f64);
    }
    if matches!(model, ModelKind::V1Z | ModelKind::V2) {
        design.push((row.z_offset - scaler.mean[3]) / scaler.sd[3]);
    }
    if model == ModelKind::V2 {
        design.push((row.log_intensity - scaler.mean[0]) / scaler.sd[0]);
        design.push((row.shape - scaler.mean[1]) / scaler.sd[1]);
        design.push((row.log_distance - scaler.mean[2]) / scaler.sd[2]);
    }
    design
}

fn matrix_rank(mut matrix: Vec<Vec<f64>>, tolerance: f64) -> usize {
    if matrix.is_empty() {
        return 0;
    }
    let rows = matrix.len();
    let columns = matrix[0].len();
    let mut rank = 0usize;
    for column in 0..columns {
        let mut pivot = rank;
        for row in rank..rows {
            if matrix[row][column].abs() > matrix[pivot][column].abs() {
                pivot = row;
            }
        }
        if matrix[pivot][column].abs() <= tolerance {
            continue;
        }
        matrix.swap(rank, pivot);
        let divisor = matrix[rank][column];
        for entry in column..columns {
            matrix[rank][entry] /= divisor;
        }
        for row in 0..rows {
            if row == rank {
                continue;
            }
            let multiplier = matrix[row][column];
            for entry in column..columns {
                matrix[row][entry] -= multiplier * matrix[rank][entry];
            }
        }
        rank += 1;
        if rank == rows {
            break;
        }
    }
    rank
}

fn group_model_cells(
    rows: &[&Observation],
    model: ModelKind,
    scaler: &Scaler,
) -> AppResult<Vec<ModelCell>> {
    let mut cells: BTreeMap<u8, BTreeMap<u16, Vec<ModelRow>>> = BTreeMap::new();
    for row in rows {
        cells
            .entry(row.key.cell)
            .or_default()
            .entry(row.key.dendrite)
            .or_default()
            .push(ModelRow {
                event: row.event,
                x: design_vector(row, model, scaler),
            });
    }
    let output = cells
        .into_iter()
        .map(|(cell_id, dendrite_map)| {
            let dendrites = dendrite_map
                .into_iter()
                .map(|(id, rows)| ModelDendrite { id, rows })
                .collect::<Vec<_>>();
            let row_count = dendrites.iter().map(|dendrite| dendrite.rows.len()).sum();
            ModelCell {
                id: cell_id,
                dendrites,
                row_count,
            }
        })
        .collect::<Vec<_>>();
    if output.iter().any(|cell| cell.row_count == 0 || cell.dendrites.is_empty()) {
        return Err("STOP_FOLD_PARTITION_MISMATCH:empty_cell".to_string());
    }
    Ok(output)
}

fn observation_rowset_hash(rows: &[&Observation]) -> String {
    let mut canonical = String::new();
    for row in rows {
        writeln!(
            &mut canonical,
            "{}|{}|{}|{}|{}",
            row.key.cell, row.key.dendrite, row.key.protrusion, row.session, row.event
        )
        .unwrap();
    }
    sha256_hex(canonical.as_bytes())
}

fn fold_design_hash(
    training_rows: &[&Observation],
    heldout_rows: &[&Observation],
    model: ModelKind,
    scaler: &Scaler,
) -> String {
    let mut canonical = String::new();
    writeln!(&mut canonical, "model={}", model.name()).unwrap();
    for (role, rows) in [("train", training_rows), ("heldout", heldout_rows)] {
        for row in rows {
            let design = design_vector(row, model, scaler);
            write!(
                &mut canonical,
                "{role}|{}|{}|{}|{}|{}",
                row.key.cell, row.key.dendrite, row.key.protrusion, row.session, row.event
            )
            .unwrap();
            for value in design {
                write!(&mut canonical, "|{value:.17e}").unwrap();
            }
            canonical.push('\n');
        }
    }
    sha256_hex(canonical.as_bytes())
}

fn training_design_hash(
    training_rows: &[&Observation],
    model: ModelKind,
    scaler: &Scaler,
) -> String {
    let mut canonical = String::new();
    writeln!(&mut canonical, "model={}", model.name()).unwrap();
    for row in training_rows {
        let design = design_vector(row, model, scaler);
        write!(
            &mut canonical,
            "train|{}|{}|{}|{}|{}",
            row.key.cell, row.key.dendrite, row.key.protrusion, row.session, row.event
        )
        .unwrap();
        for value in design {
            write!(&mut canonical, "|{value:.17e}").unwrap();
        }
        canonical.push('\n');
    }
    sha256_hex(canonical.as_bytes())
}

fn build_fold_design(
    dataset: &Dataset,
    heldout_cell: u8,
    model: ModelKind,
    enforce_source_lock: bool,
) -> AppResult<FoldDesign> {
    if enforce_source_lock && !(1..=8).contains(&heldout_cell) {
        return Err("STOP_FOLD_PARTITION_MISMATCH:heldout_id".to_string());
    }
    let training_rows = dataset
        .rows
        .iter()
        .filter(|row| row.key.cell != heldout_cell)
        .collect::<Vec<_>>();
    let heldout_rows = dataset
        .rows
        .iter()
        .filter(|row| row.key.cell == heldout_cell)
        .collect::<Vec<_>>();
    let bad_production_counts = enforce_source_lock
        && (training_rows.len() + heldout_rows.len() != EXPECTED_COMPARISON_ROWS
            || heldout_rows.len() != EXPECTED_CELL_ROWS[(heldout_cell - 1) as usize]);
    if bad_production_counts || training_rows.is_empty() || heldout_rows.is_empty() {
        return Err("STOP_FOLD_PARTITION_MISMATCH:counts".to_string());
    }
    let scaler = sample_scaler(&training_rows)?;
    let mut age_support = [[0usize; 2]; 4];
    for row in &training_rows {
        age_support[row.age_bin as usize][row.event as usize] += 1;
    }
    if age_support
        .iter()
        .any(|support| support[0] == 0 || support[1] == 0)
    {
        return Err("STOP_DESIGN_OR_SEPARATION_FAIL:age_support".to_string());
    }
    let design_matrix = training_rows
        .iter()
        .map(|row| design_vector(row, model, &scaler))
        .collect::<Vec<_>>();
    if matrix_rank(design_matrix.clone(), 1.0e-10) != model.dimension() {
        return Err("STOP_DESIGN_OR_SEPARATION_FAIL:rank".to_string());
    }
    let training_rowset_sha256 = observation_rowset_hash(&training_rows);
    let training_design_sha256 = training_design_hash(&training_rows, model, &scaler);
    let heldout_rowset_sha256 = observation_rowset_hash(&heldout_rows);
    let design_sha256 = fold_design_hash(&training_rows, &heldout_rows, model, &scaler);
    let training = group_model_cells(&training_rows, model, &scaler)?;
    let mut heldout_grouped = group_model_cells(&heldout_rows, model, &scaler)?;
    if heldout_grouped.len() != 1 || heldout_grouped[0].id != heldout_cell {
        return Err("STOP_FOLD_PARTITION_MISMATCH:heldout_group".to_string());
    }
    let heldout = heldout_grouped.remove(0);
    Ok(FoldDesign {
        heldout_cell,
        model,
        scaler,
        training_rowset_sha256,
        training_design_sha256,
        heldout_rowset_sha256,
        design_sha256,
        training,
        heldout,
        training_rows: training_rows.len(),
    })
}

fn parameter_parts<'a>(
    parameters: &'a [f64],
    model: ModelKind,
    face: VarianceFace,
) -> AppResult<(&'a [f64], f64, f64)> {
    let beta_dimension = model.dimension();
    let expected = beta_dimension + face.active_count();
    if parameters.len() != expected {
        return Err("STOP_MODEL_ROWSET_MISMATCH:parameter_dimension".to_string());
    }
    let beta = &parameters[..beta_dimension];
    let mut index = beta_dimension;
    let sigma_u = if face.cell_active() {
        let sigma = parameters[index].exp();
        index += 1;
        sigma
    } else {
        0.0
    };
    let sigma_v = if face.dendrite_active() {
        parameters[index].exp()
    } else {
        0.0
    };
    if beta.iter().any(|value| !value.is_finite())
        || !sigma_u.is_finite()
        || !sigma_v.is_finite()
    {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:parameters".to_string());
    }
    Ok((beta, sigma_u, sigma_v))
}

fn find_concave_mode<F>(mut function: F, context: &str) -> AppResult<(f64, f64)>
where
    F: FnMut(f64) -> AppResult<(f64, f64, f64)>,
{
    let mut point = 0.0;
    let mut last_relative_step = 0.0;
    for _ in 0..MODE_MAX_ITERS {
        let (value, derivative, second) = function(point)?;
        if !value.is_finite() || !derivative.is_finite() || !second.is_finite() || second >= 0.0 {
            return Err(format!("STOP_AGHQ_MODE_FAILURE:{context}:curvature"));
        }
        if derivative.abs() <= MODE_SCORE_TOL && last_relative_step <= MODE_STEP_TOL {
            let scale = (-second).recip().sqrt();
            if !scale.is_finite() || scale <= 0.0 {
                return Err(format!("STOP_AGHQ_MODE_FAILURE:{context}:scale"));
            }
            return Ok((point, scale));
        }
        let mut step = -derivative / second;
        let step_guard = 20.0 * (1.0 + point.abs());
        step = step.clamp(-step_guard, step_guard);
        let mut accepted = false;
        let mut candidate = point + step;
        for _ in 0..80 {
            let (candidate_value, candidate_derivative, candidate_second) = function(candidate)?;
            if candidate_value.is_finite()
                && candidate_derivative.is_finite()
                && candidate_second < 0.0
                && (candidate_value >= value || candidate_derivative.abs() < derivative.abs())
            {
                accepted = true;
                break;
            }
            step *= LINE_SHRINK;
            candidate = point + step;
        }
        if !accepted {
            return Err(format!("STOP_AGHQ_MODE_FAILURE:{context}:line_search"));
        }
        let relative_step = step.abs() / (1.0 + point.abs());
        point = candidate;
        last_relative_step = relative_step;
        if relative_step <= MODE_STEP_TOL {
            let (_, final_derivative, final_second) = function(point)?;
            if final_derivative.abs() <= MODE_SCORE_TOL && final_second < 0.0 {
                let scale = (-final_second).recip().sqrt();
                if !scale.is_finite() || scale <= 0.0 {
                    return Err(format!("STOP_AGHQ_MODE_FAILURE:{context}:scale"));
                }
                return Ok((point, scale));
            }
        }
    }
    let (_, derivative, second) = function(point)?;
    Err(format!(
        "STOP_AGHQ_MODE_FAILURE:{context}:iterations:point={point:.17e}:score={derivative:.17e}:curvature={second:.17e}:last_step={last_relative_step:.17e}"
    ))
}

fn conditional_at(
    dendrite: &ModelDendrite,
    beta: &[f64],
    u: f64,
    v: f64,
    sigma_v: f64,
) -> AppResult<(f64, f64, f64, Vec<f64>, f64, f64, f64)> {
    let mut log_value = if sigma_v > 0.0 {
        normal_log_density(v, sigma_v)?
    } else {
        0.0
    };
    let mut derivative_v = if sigma_v > 0.0 {
        -v / (sigma_v * sigma_v)
    } else {
        0.0
    };
    let mut second_v = if sigma_v > 0.0 {
        -1.0 / (sigma_v * sigma_v)
    } else {
        0.0
    };
    let mut beta_score = vec![0.0; beta.len()];
    let mut sum_score = 0.0;
    let mut sum_second = 0.0;
    for row in &dendrite.rows {
        let likelihood = row_likelihood(row.event, dot(beta, &row.x) + u + v)?;
        log_value += likelihood.log_value;
        derivative_v += likelihood.score;
        second_v += likelihood.second;
        sum_score += likelihood.score;
        sum_second += likelihood.second;
        for index in 0..beta.len() {
            beta_score[index] += likelihood.score * row.x[index];
        }
    }
    let log_sigma_score = if sigma_v > 0.0 {
        -1.0 + (v / sigma_v).powi(2)
    } else {
        0.0
    };
    for (value, name) in [
        (log_value, "conditional_log"),
        (derivative_v, "conditional_derivative"),
        (second_v, "conditional_second"),
        (log_sigma_score, "conditional_sigma_score"),
        (sum_score, "conditional_sum_score"),
        (sum_second, "conditional_sum_second"),
    ] {
        ensure_finite(value, name)?;
    }
    Ok((
        log_value,
        derivative_v,
        second_v,
        beta_score,
        log_sigma_score,
        sum_score,
        sum_second,
    ))
}

fn inner_integral(
    dendrite: &ModelDendrite,
    beta: &[f64],
    u: f64,
    sigma_v: f64,
    quadrature: &Quadrature,
) -> AppResult<InnerResult> {
    if sigma_v == 0.0 {
        let (log_integral, _, _, beta_score, _, u_score, u_second) =
            conditional_at(dendrite, beta, u, 0.0, 0.0)?;
        return Ok(InnerResult {
            log_integral,
            beta_score,
            log_sigma_v_score: 0.0,
            u_score,
            u_second,
        });
    }
    let (mode, scale) = find_concave_mode(
        |v| {
            let (log_value, derivative, second, _, _, _, _) =
                conditional_at(dendrite, beta, u, v, sigma_v)?;
            Ok((log_value, derivative, second))
        },
        "inner",
    )?;
    let log_jacobian = (SQRT_2 * scale).ln();
    let mut log_terms = Vec::with_capacity(quadrature.order);
    let mut beta_scores = Vec::with_capacity(quadrature.order);
    let mut sigma_scores = Vec::with_capacity(quadrature.order);
    let mut u_scores = Vec::with_capacity(quadrature.order);
    let mut u_seconds = Vec::with_capacity(quadrature.order);
    for (node, weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
        let v = mode + SQRT_2 * scale * node;
        let (log_value, _, _, beta_score, sigma_score, u_score, u_second) =
            conditional_at(dendrite, beta, u, v, sigma_v)?;
        log_terms.push(weight.ln() + log_value + node * node + log_jacobian);
        beta_scores.push(beta_score);
        sigma_scores.push(sigma_score);
        u_scores.push(u_score);
        u_seconds.push(u_second);
    }
    let log_integral = log_sum_exp(&log_terms)?;
    let posterior = log_terms
        .iter()
        .map(|term| (*term - log_integral).exp())
        .collect::<Vec<_>>();
    let mut beta_score = vec![0.0; beta.len()];
    let mut log_sigma_v_score = 0.0;
    let mut u_score = 0.0;
    let mut expected_u_second = 0.0;
    let mut expected_u_score_squared = 0.0;
    for index in 0..posterior.len() {
        let probability = posterior[index];
        for beta_index in 0..beta.len() {
            beta_score[beta_index] += probability * beta_scores[index][beta_index];
        }
        log_sigma_v_score += probability * sigma_scores[index];
        u_score += probability * u_scores[index];
        expected_u_second += probability * u_seconds[index];
        expected_u_score_squared += probability * u_scores[index] * u_scores[index];
    }
    let u_second = expected_u_second + expected_u_score_squared - u_score * u_score;
    if !u_second.is_finite() {
        return Err("STOP_NONFINITE_LIKELIHOOD_OR_GRADIENT:inner_u_second".to_string());
    }
    Ok(InnerResult {
        log_integral,
        beta_score,
        log_sigma_v_score,
        u_score,
        u_second,
    })
}

fn outer_point(
    cell: &ModelCell,
    beta: &[f64],
    u: f64,
    sigma_u: f64,
    sigma_v: f64,
    quadrature: &Quadrature,
) -> AppResult<OuterPoint> {
    let mut log_integrand = if sigma_u > 0.0 {
        normal_log_density(u, sigma_u)?
    } else {
        0.0
    };
    let mut derivative = if sigma_u > 0.0 {
        -u / (sigma_u * sigma_u)
    } else {
        0.0
    };
    let mut second = if sigma_u > 0.0 {
        -1.0 / (sigma_u * sigma_u)
    } else {
        0.0
    };
    let mut beta_score = vec![0.0; beta.len()];
    let mut log_sigma_v_score = 0.0;
    for dendrite in &cell.dendrites {
        let inner = inner_integral(dendrite, beta, u, sigma_v, quadrature)?;
        log_integrand += inner.log_integral;
        derivative += inner.u_score;
        second += inner.u_second;
        log_sigma_v_score += inner.log_sigma_v_score;
        for index in 0..beta.len() {
            beta_score[index] += inner.beta_score[index];
        }
    }
    for (value, name) in [
        (log_integrand, "outer_log"),
        (derivative, "outer_derivative"),
        (second, "outer_second"),
        (log_sigma_v_score, "outer_sigma_v"),
    ] {
        ensure_finite(value, name)?;
    }
    Ok(OuterPoint {
        log_integrand,
        derivative,
        second,
        beta_score,
        log_sigma_v_score,
    })
}

fn cell_integral(
    cell: &ModelCell,
    beta: &[f64],
    sigma_u: f64,
    sigma_v: f64,
    quadrature: &Quadrature,
) -> AppResult<CellIntegral> {
    if sigma_u == 0.0 {
        let point = outer_point(cell, beta, 0.0, 0.0, sigma_v, quadrature)?;
        return Ok(CellIntegral {
            log_likelihood: point.log_integrand,
            beta_score: point.beta_score,
            log_sigma_u_score: 0.0,
            log_sigma_v_score: point.log_sigma_v_score,
        });
    }
    let (mode, scale) = find_concave_mode(
        |u| {
            let point = outer_point(cell, beta, u, sigma_u, sigma_v, quadrature)?;
            Ok((point.log_integrand, point.derivative, point.second))
        },
        "outer",
    )?;
    let log_jacobian = (SQRT_2 * scale).ln();
    let mut log_terms = Vec::with_capacity(quadrature.order);
    let mut beta_scores = Vec::with_capacity(quadrature.order);
    let mut sigma_u_scores = Vec::with_capacity(quadrature.order);
    let mut sigma_v_scores = Vec::with_capacity(quadrature.order);
    for (node, weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
        let u = mode + SQRT_2 * scale * node;
        let point = outer_point(cell, beta, u, sigma_u, sigma_v, quadrature)?;
        log_terms.push(weight.ln() + point.log_integrand + node * node + log_jacobian);
        beta_scores.push(point.beta_score);
        sigma_u_scores.push(-1.0 + (u / sigma_u).powi(2));
        sigma_v_scores.push(point.log_sigma_v_score);
    }
    let log_likelihood = log_sum_exp(&log_terms)?;
    let posterior = log_terms
        .iter()
        .map(|term| (*term - log_likelihood).exp())
        .collect::<Vec<_>>();
    let mut beta_score = vec![0.0; beta.len()];
    let mut log_sigma_u_score = 0.0;
    let mut log_sigma_v_score = 0.0;
    for index in 0..posterior.len() {
        let probability = posterior[index];
        for beta_index in 0..beta.len() {
            beta_score[beta_index] += probability * beta_scores[index][beta_index];
        }
        log_sigma_u_score += probability * sigma_u_scores[index];
        log_sigma_v_score += probability * sigma_v_scores[index];
    }
    Ok(CellIntegral {
        log_likelihood,
        beta_score,
        log_sigma_u_score,
        log_sigma_v_score,
    })
}

fn evaluate_training(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    quadrature: &Quadrature,
) -> AppResult<Eval> {
    let (beta, sigma_u, sigma_v) = parameter_parts(parameters, design.model, face)?;
    let mut log_likelihood = 0.0;
    let mut gradient = vec![0.0; parameters.len()];
    for cell in &design.training {
        let integral = cell_integral(cell, beta, sigma_u, sigma_v, quadrature)?;
        log_likelihood += integral.log_likelihood;
        for index in 0..beta.len() {
            gradient[index] += integral.beta_score[index];
        }
        let mut index = beta.len();
        if face.cell_active() {
            gradient[index] += integral.log_sigma_u_score;
            index += 1;
        }
        if face.dendrite_active() {
            gradient[index] += integral.log_sigma_v_score;
        }
    }
    let denominator = design.training_rows as f64;
    let objective = -log_likelihood / denominator;
    for value in &mut gradient {
        *value = -*value / denominator;
        ensure_finite(*value, "training_gradient")?;
    }
    ensure_finite(objective, "training_objective")?;
    Ok(Eval {
        objective,
        gradient,
        log_likelihood,
    })
}

fn heldout_log_likelihood(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    quadrature: &Quadrature,
) -> AppResult<f64> {
    let (beta, sigma_u, sigma_v) = parameter_parts(parameters, design.model, face)?;
    Ok(cell_integral(&design.heldout, beta, sigma_u, sigma_v, quadrature)?.log_likelihood)
}

fn parameter_bounds(model: ModelKind, face: VarianceFace) -> Vec<(f64, f64)> {
    let mut bounds = vec![(-BETA_GUARD, BETA_GUARD); model.dimension()];
    for _ in 0..face.active_count() {
        bounds.push((SIGMA_LOWER.ln(), SIGMA_UPPER.ln()));
    }
    bounds
}

fn project_parameters(parameters: &mut [f64], bounds: &[(f64, f64)]) {
    for (value, (lower, upper)) in parameters.iter_mut().zip(bounds) {
        *value = value.clamp(*lower, *upper);
    }
}

fn projected_gradient(
    parameters: &[f64],
    gradient: &[f64],
    bounds: &[(f64, f64)],
) -> Vec<f64> {
    parameters
        .iter()
        .zip(gradient)
        .zip(bounds)
        .map(|((parameter, derivative), (lower, upper))| {
            if (*parameter <= *lower + 1.0e-13 && *derivative > 0.0)
                || (*parameter >= *upper - 1.0e-13 && *derivative < 0.0)
            {
                0.0
            } else {
                *derivative
            }
        })
        .collect()
}

fn identity_matrix(dimension: usize) -> Vec<Vec<f64>> {
    let mut matrix = vec![vec![0.0; dimension]; dimension];
    for index in 0..dimension {
        matrix[index][index] = 1.0;
    }
    matrix
}

fn matrix_vector(matrix: &[Vec<f64>], vector: &[f64]) -> Vec<f64> {
    matrix.iter().map(|row| dot(row, vector)).collect()
}

fn bounded_bfgs<F>(
    start: &[f64],
    bounds: &[(f64, f64)],
    mut evaluate: F,
) -> AppResult<Optimized>
where
    F: FnMut(&[f64]) -> AppResult<Eval>,
{
    if start.len() != bounds.len() || start.is_empty() {
        return Err("STOP_OPTIMIZER_NONCONVERGENCE:dimension".to_string());
    }
    let dimension = start.len();
    let mut parameters = start.to_vec();
    project_parameters(&mut parameters, bounds);
    let mut current = evaluate(&parameters)?;
    let mut evaluations = 1usize;
    let mut inverse_hessian = identity_matrix(dimension);

    for iteration in 0..=OPT_MAX_ITERS {
        let projected = projected_gradient(&parameters, &current.gradient, bounds);
        let projected_gradient_inf = inf_norm(&projected);
        if projected_gradient_inf <= OPT_INTERNAL_GRAD_TOL {
            let gradient_inf = inf_norm(&current.gradient);
            return Ok(Optimized {
                parameters,
                objective: current.objective,
                log_likelihood: current.log_likelihood,
                gradient: current.gradient,
                gradient_inf,
                projected_gradient_inf,
                iterations: iteration,
                evaluations,
            });
        }
        if iteration == OPT_MAX_ITERS || evaluations >= OPT_MAX_EVALS {
            break;
        }

        let mut direction = matrix_vector(&inverse_hessian, &projected)
            .into_iter()
            .map(|value| -value)
            .collect::<Vec<_>>();
        if dot(&projected, &direction)
            >= -1.0e-14 * (1.0 + projected_gradient_inf * projected_gradient_inf)
        {
            direction = projected.iter().map(|value| -value).collect();
            inverse_hessian = identity_matrix(dimension);
        }

        let mut step = 1.0;
        let mut accepted: Option<(Vec<f64>, Eval)> = None;
        for _ in 0..80 {
            if evaluations >= OPT_MAX_EVALS {
                break;
            }
            let mut candidate = parameters
                .iter()
                .zip(&direction)
                .map(|(parameter, delta)| parameter + step * delta)
                .collect::<Vec<_>>();
            project_parameters(&mut candidate, bounds);
            let displacement = candidate
                .iter()
                .zip(&parameters)
                .map(|(new, old)| new - old)
                .collect::<Vec<_>>();
            let directional_derivative = dot(&current.gradient, &displacement);
            if inf_norm(&displacement) <= 1.0e-15 || directional_derivative >= 0.0 {
                step *= LINE_SHRINK;
                continue;
            }
            let candidate_eval = evaluate(&candidate)?;
            evaluations += 1;
            if candidate_eval.objective
                <= current.objective + ARMIJO_C1 * directional_derivative
            {
                accepted = Some((candidate, candidate_eval));
                break;
            }
            step *= LINE_SHRINK;
        }
        let (candidate, candidate_eval) = accepted.ok_or_else(|| {
            format!(
                "STOP_OPTIMIZER_NONCONVERGENCE:line_search:iter={iteration}:projected_grad={projected_gradient_inf:.17e}"
            )
        })?;

        let displacement = candidate
            .iter()
            .zip(&parameters)
            .map(|(new, old)| new - old)
            .collect::<Vec<_>>();
        let gradient_change = candidate_eval
            .gradient
            .iter()
            .zip(&current.gradient)
            .map(|(new, old)| new - old)
            .collect::<Vec<_>>();
        let curvature = dot(&displacement, &gradient_change);
        let curvature_guard =
            1.0e-12 * inf_norm(&displacement).max(1.0) * inf_norm(&gradient_change).max(1.0);
        if curvature > curvature_guard {
            let h_y = matrix_vector(&inverse_hessian, &gradient_change);
            let y_h_y = dot(&gradient_change, &h_y);
            let coefficient = (curvature + y_h_y) / (curvature * curvature);
            for row in 0..dimension {
                for column in 0..dimension {
                    inverse_hessian[row][column] +=
                        coefficient * displacement[row] * displacement[column]
                            - (h_y[row] * displacement[column]
                                + displacement[row] * h_y[column])
                                / curvature;
                }
            }
        } else {
            inverse_hessian = identity_matrix(dimension);
        }
        parameters = candidate;
        current = candidate_eval;
    }
    let projected = projected_gradient(&parameters, &current.gradient, bounds);
    Err(format!(
        "STOP_OPTIMIZER_NONCONVERGENCE:limit:evals={evaluations}:grad={:.17e}",
        inf_norm(&projected)
    ))
}

fn optimize_training(
    design: &FoldDesign,
    face: VarianceFace,
    start: &[f64],
    quadrature: &Quadrature,
) -> AppResult<Optimized> {
    let bounds = parameter_bounds(design.model, face);
    bounded_bfgs(start, &bounds, |parameters| {
        evaluate_training(design, face, parameters, quadrature)
    })
}

fn training_event_fraction(design: &FoldDesign) -> AppResult<f64> {
    let mut rows = 0usize;
    let mut events = 0usize;
    for cell in &design.training {
        for dendrite in &cell.dendrites {
            for row in &dendrite.rows {
                rows += 1;
                events += row.event as usize;
            }
        }
    }
    if rows != design.training_rows || events == 0 || events >= rows {
        return Err("STOP_DESIGN_OR_SEPARATION_FAIL:training_event_fraction".to_string());
    }
    Ok(events as f64 / rows as f64)
}

fn canonical_starts(design: &FoldDesign, face: VarianceFace) -> AppResult<Vec<Vec<f64>>> {
    let event_fraction = training_event_fraction(design)?;
    let baseline = (-(1.0 - event_fraction).ln() / 4.0).ln();
    if !baseline.is_finite() {
        return Err("STOP_DESIGN_OR_SEPARATION_FAIL:baseline_start".to_string());
    }
    let intercept_offsets = [0.0, -0.5, 0.5, 0.0];
    let sigma_pairs: [(f64, f64); 4] =
        [(0.1, 0.1), (0.5, 0.5), (1.5, 0.25), (0.25, 1.5)];
    let mut starts = Vec::new();
    for start_index in 0..4 {
        let mut parameters = vec![0.0; design.model.dimension() + face.active_count()];
        parameters[0] = baseline + intercept_offsets[start_index];
        if start_index == 3 {
            for index in 1..design.model.dimension() {
                parameters[index] = if index % 2 == 1 { 0.05 } else { -0.05 };
            }
        }
        let mut index = design.model.dimension();
        if face.cell_active() {
            parameters[index] = sigma_pairs[start_index].0.ln();
            index += 1;
        }
        if face.dendrite_active() {
            parameters[index] = sigma_pairs[start_index].1.ln();
        }
        starts.push(parameters);
    }
    Ok(starts)
}

fn fit_face(
    design: &FoldDesign,
    face: VarianceFace,
    quadrature: &Quadrature,
    starts: Vec<Vec<f64>>,
) -> AppResult<FaceFit> {
    if starts.len() < 3 {
        return Err(format!(
            "STOP_OPTIMIZER_NONCONVERGENCE:{}:{}:insufficient_starts",
            design.model.name(),
            face.name()
        ));
    }
    let mut solutions = Vec::new();
    let mut errors = Vec::new();
    for start in starts {
        match optimize_training(design, face, &start, quadrature) {
            Ok(solution) => solutions.push(solution),
            Err(error) => errors.push(error),
        }
    }
    if solutions.len() < 3 {
        return Err(format!(
            "STOP_OPTIMIZER_NONCONVERGENCE:{}:{}:q{}:converged={}:errors={}",
            design.model.name(),
            face.name(),
            quadrature.order,
            solutions.len(),
            errors.join("|")
        ));
    }
    solutions.sort_by(|left, right| {
        left.objective
            .total_cmp(&right.objective)
            .then_with(|| {
                for (a, b) in left.parameters.iter().zip(&right.parameters) {
                    let ordering = a.total_cmp(b);
                    if !ordering.is_eq() {
                        return ordering;
                    }
                }
                left.parameters.len().cmp(&right.parameters.len())
            })
    });
    let best_three_spread = solutions[2].objective - solutions[0].objective;
    if best_three_spread > MULTISTART_OBJECTIVE_TOL {
        return Err(format!(
            "STOP_MULTISTART_DISAGREEMENT:{}:{}:q{}:{best_three_spread:.17e}",
            design.model.name(),
            face.name(),
            quadrature.order
        ));
    }
    Ok(FaceFit {
        face,
        order: quadrature.order,
        optimum: solutions[0].clone(),
        converged_starts: solutions.len(),
        best_three_spread,
        solutions,
    })
}

fn fit_all_faces(
    design: &FoldDesign,
    quadrature: &Quadrature,
    preceding: Option<&[FaceFit]>,
) -> AppResult<Vec<FaceFit>> {
    let mut fits = Vec::new();
    for face in VarianceFace::ALL {
        let starts = if let Some(previous) = preceding {
            let prior_face = previous
                .iter()
                .find(|fit| fit.face == face)
                .ok_or_else(|| "STOP_MODEL_ROWSET_MISMATCH:missing_preceding_face".to_string())?;
            prior_face
                .solutions
                .iter()
                .map(|solution| solution.parameters.clone())
                .collect()
        } else {
            canonical_starts(design, face)?
        };
        fits.push(fit_face(design, face, quadrature, starts)?);
    }
    Ok(fits)
}

fn face_diagnostics(fits: &[FaceFit]) -> Vec<FaceDiagnostic> {
    fits.iter()
        .map(|fit| FaceDiagnostic {
            face: fit.face,
            order: fit.order,
            parameters: fit.optimum.parameters.clone(),
            objective: fit.optimum.objective,
            log_likelihood: fit.optimum.log_likelihood,
            converged_starts: fit.converged_starts,
            best_three_spread: fit.best_three_spread,
            iterations: fit.optimum.iterations,
            evaluations: fit.optimum.evaluations,
            gradient: fit.optimum.gradient.clone(),
            gradient_inf: fit.optimum.gradient_inf,
            projected_gradient_inf: fit.optimum.projected_gradient_inf,
        })
        .collect()
}

fn lower_guard_reduction(fit: &FaceFit) -> Option<VarianceFace> {
    let beta_dimension = fit.optimum.parameters.len() - fit.face.active_count();
    let mut index = beta_dimension;
    let cell_at_lower = if fit.face.cell_active() {
        let at_lower =
            fit.optimum.parameters[index] <= SIGMA_LOWER.ln() + 1.0e-9;
        index += 1;
        at_lower
    } else {
        false
    };
    let dendrite_at_lower = if fit.face.dendrite_active() {
        fit.optimum.parameters[index] <= SIGMA_LOWER.ln() + 1.0e-9
    } else {
        false
    };
    match (fit.face, cell_at_lower, dendrite_at_lower) {
        (_, false, false) => None,
        (VarianceFace::Cell, true, _) | (VarianceFace::Dendrite, _, true) => {
            Some(VarianceFace::None)
        }
        (VarianceFace::Both, true, true) => Some(VarianceFace::None),
        (VarianceFace::Both, true, false) => Some(VarianceFace::Dendrite),
        (VarianceFace::Both, false, true) => Some(VarianceFace::Cell),
        _ => None,
    }
}

fn select_face(fits: &[FaceFit]) -> AppResult<FaceFit> {
    if fits.len() != VarianceFace::ALL.len() {
        return Err("STOP_MODEL_ROWSET_MISMATCH:face_count".to_string());
    }
    let order = fits[0].order;
    if order == 0 || fits.iter().any(|fit| fit.order != order) {
        return Err("STOP_MODEL_ROWSET_MISMATCH:face_order".to_string());
    }
    for fit in fits {
        if let Some(reduced_face) = lower_guard_reduction(fit) {
            let reduced = fits
                .iter()
                .find(|candidate| candidate.face == reduced_face)
                .ok_or_else(|| "STOP_MODEL_ROWSET_MISMATCH:lower_reduced_face".to_string())?;
            let discrepancy = (fit.optimum.objective - reduced.optimum.objective).abs();
            if discrepancy > BOUNDARY_GAIN_TOL {
                return Err(format!(
                    "STOP_QUADRATURE_NONCONVERGENCE:lower_guard_face_mismatch:{}:{}:{discrepancy:.17e}",
                    fit.face.name(),
                    reduced_face.name()
                ));
            }
        }
    }
    let admissible = fits
        .iter()
        .filter(|fit| lower_guard_reduction(fit).is_none())
        .collect::<Vec<_>>();
    let best_objective = admissible
        .iter()
        .map(|fit| fit.optimum.objective)
        .fold(f64::INFINITY, f64::min);
    let mut eligible = admissible
        .iter()
        .filter(|fit| fit.optimum.objective - best_objective <= BOUNDARY_GAIN_TOL)
        .map(|fit| (*fit).clone())
        .collect::<Vec<_>>();
    eligible.sort_by_key(|fit| (fit.face.active_count(), fit.face));
    eligible
        .into_iter()
        .next()
        .ok_or_else(|| "STOP_OPTIMIZER_NONCONVERGENCE:no_face".to_string())
}

fn validate_face_transition(
    preceding: &FaceFit,
    current: &FaceFit,
    current_faces: &[FaceFit],
) -> AppResult<()> {
    if preceding.face == current.face {
        return Ok(());
    }
    if current.face.active_count() >= preceding.face.active_count() {
        return Err(format!(
            "STOP_QUADRATURE_NONCONVERGENCE:face_change:{}:{}",
            preceding.face.name(),
            current.face.name()
        ));
    }
    let old_face_at_current_order = current_faces
        .iter()
        .find(|fit| fit.face == preceding.face)
        .ok_or_else(|| "STOP_MODEL_ROWSET_MISMATCH:transition_face".to_string())?;
    let simplicity_cost =
        current.optimum.objective - old_face_at_current_order.optimum.objective;
    if simplicity_cost > BOUNDARY_GAIN_TOL {
        return Err(format!(
            "STOP_QUADRATURE_NONCONVERGENCE:face_simplicity_cost:{simplicity_cost:.17e}"
        ));
    }
    Ok(())
}

fn semantic_parameter(
    parameters: &[f64],
    model: ModelKind,
    face: VarianceFace,
    cell_sigma: bool,
) -> Option<f64> {
    let mut index = model.dimension();
    if face.cell_active() {
        if cell_sigma {
            return Some(parameters[index]);
        }
        index += 1;
    }
    if face.dendrite_active() && !cell_sigma {
        return Some(parameters[index]);
    }
    None
}

fn parameter_order_delta(
    earlier: &FaceFit,
    later: &FaceFit,
    model: ModelKind,
) -> AppResult<f64> {
    let mut maximum = 0.0f64;
    for index in 0..model.dimension() {
        let delta = (later.optimum.parameters[index] - earlier.optimum.parameters[index]).abs()
            / (1.0 + later.optimum.parameters[index].abs());
        maximum = maximum.max(delta);
    }
    for cell_sigma in [true, false] {
        if let Some(later_value) =
            semantic_parameter(&later.optimum.parameters, model, later.face, cell_sigma)
        {
            let earlier_value =
                semantic_parameter(&earlier.optimum.parameters, model, earlier.face, cell_sigma)
                    .ok_or_else(|| {
                        "STOP_QUADRATURE_NONCONVERGENCE:variance_parameter_added".to_string()
                    })?;
            let delta = (later_value - earlier_value).abs() / (1.0 + later_value.abs());
            maximum = maximum.max(delta);
        }
    }
    Ok(maximum)
}

fn five_point_hessian_condition(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    quadrature: &Quadrature,
) -> AppResult<f64> {
    let bounds = parameter_bounds(design.model, face);
    let dimension = parameters.len();
    let mut hessian = vec![vec![0.0; dimension]; dimension];
    for column in 0..dimension {
        let distance = (parameters[column] - bounds[column].0)
            .min(bounds[column].1 - parameters[column]);
        let step = (1.0e-4 * (1.0 + parameters[column].abs())).min(0.2 * distance);
        if !step.is_finite() || step <= 1.0e-8 {
            return Err(format!(
                "STOP_HESSIAN_ILL_CONDITIONED:finite_difference_boundary:{column}"
            ));
        }
        let mut gradients = Vec::new();
        for multiplier in [-2.0, -1.0, 1.0, 2.0] {
            let mut shifted = parameters.to_vec();
            shifted[column] += multiplier * step;
            gradients.push(evaluate_training(design, face, &shifted, quadrature)?.gradient);
        }
        for row in 0..dimension {
            hessian[row][column] = (gradients[0][row] - 8.0 * gradients[1][row]
                + 8.0 * gradients[2][row]
                - gradients[3][row])
                / (12.0 * step);
        }
    }
    for row in 0..dimension {
        for column in row + 1..dimension {
            let symmetric = 0.5 * (hessian[row][column] + hessian[column][row]);
            hessian[row][column] = symmetric;
            hessian[column][row] = symmetric;
        }
    }
    let (eigenvalues, _) = jacobi_eigen(hessian)
        .map_err(|error| format!("STOP_HESSIAN_ILL_CONDITIONED:{error}"))?;
    let minimum = eigenvalues.iter().copied().fold(f64::INFINITY, f64::min);
    let maximum = eigenvalues
        .iter()
        .copied()
        .fold(f64::NEG_INFINITY, f64::max);
    if !minimum.is_finite() || !maximum.is_finite() || minimum <= 0.0 {
        return Err(format!(
            "STOP_HESSIAN_ILL_CONDITIONED:eigenvalues:{minimum:.17e}:{maximum:.17e}"
        ));
    }
    let condition = maximum / minimum;
    if !condition.is_finite() || condition > HESSIAN_CONDITION_MAX {
        return Err(format!(
            "STOP_HESSIAN_ILL_CONDITIONED:condition:{condition:.17e}"
        ));
    }
    Ok(condition)
}

fn guard_selected_optimum(
    design: &FoldDesign,
    fit: &FaceFit,
    quadrature: &Quadrature,
) -> AppResult<()> {
    for (index, beta) in fit.optimum.parameters[..design.model.dimension()]
        .iter()
        .enumerate()
    {
        if beta.abs() >= BETA_GUARD - 1.0e-7 {
            return Err(format!(
                "STOP_DESIGN_OR_SEPARATION_FAIL:beta_guard:{index}:{beta:.17e}"
            ));
        }
    }
    let evaluation =
        evaluate_training(design, fit.face, &fit.optimum.parameters, quadrature)?;
    for index in design.model.dimension()..fit.optimum.parameters.len() {
        if fit.optimum.parameters[index] >= SIGMA_UPPER.ln() - 1.0e-7
            && evaluation.gradient[index] < 0.0
        {
            return Err(format!(
                "STOP_FRAILTY_UNIDENTIFIED:upper_raw_objective_gradient:{index}:{:.17e}",
                evaluation.gradient[index]
            ));
        }
    }
    let raw_gradient_inf = inf_norm(&evaluation.gradient);
    if raw_gradient_inf > OPT_GRAD_TOL {
        return Err(format!(
            "STOP_OPTIMIZER_NONCONVERGENCE:selected_raw_gradient:expected=raw_gradient_inf<={OPT_GRAD_TOL:.17e}:observed={raw_gradient_inf:.17e}"
        ));
    }
    Ok(())
}

fn all_cell_log_likelihoods(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    quadrature: &Quadrature,
) -> AppResult<BTreeMap<u8, (usize, f64)>> {
    let (beta, sigma_u, sigma_v) = parameter_parts(parameters, design.model, face)?;
    let mut output = BTreeMap::new();
    for cell in design.training.iter().chain(std::iter::once(&design.heldout)) {
        let value = cell_integral(cell, beta, sigma_u, sigma_v, quadrature)?.log_likelihood;
        if output.insert(cell.id, (cell.row_count, value)).is_some() {
            return Err("STOP_FOLD_PARTITION_MISMATCH:duplicate_cell_integral".to_string());
        }
    }
    Ok(output)
}

fn quadrature_cell_delta(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    lower: &Quadrature,
    higher: &Quadrature,
) -> AppResult<f64> {
    let lower_values = all_cell_log_likelihoods(design, face, parameters, lower)?;
    let higher_values = all_cell_log_likelihoods(design, face, parameters, higher)?;
    if lower_values.keys().collect::<Vec<_>>() != higher_values.keys().collect::<Vec<_>>() {
        return Err("STOP_FOLD_PARTITION_MISMATCH:quadrature_cells".to_string());
    }
    let mut maximum = 0.0f64;
    for (cell, (row_count, lower_value)) in lower_values {
        let (_, higher_value) = higher_values
            .get(&cell)
            .ok_or_else(|| "STOP_FOLD_PARTITION_MISMATCH:quadrature_cell_missing".to_string())?;
        let delta = (higher_value - lower_value).abs() / row_count.max(1) as f64;
        maximum = maximum.max(delta);
    }
    Ok(maximum)
}

fn fit_fold_model(
    design: &FoldDesign,
    q15: &Quadrature,
    q25: &Quadrature,
    q35: &Quadrature,
    q45: &Quadrature,
) -> AppResult<FoldModelFit> {
    fit_fold_model_internal(design, q15, q25, q35, q45, false)
}

fn fit_fold_model_internal(
    design: &FoldDesign,
    q15: &Quadrature,
    q25: &Quadrature,
    q35: &Quadrature,
    q45: &Quadrature,
    force_fallback_for_self_test: bool,
) -> AppResult<FoldModelFit> {
    let faces_q15 = fit_all_faces(design, q15, None)?;
    let diagnostics_q15 = face_diagnostics(&faces_q15);
    let selected_q15 = select_face(&faces_q15)?;
    guard_selected_optimum(design, &selected_q15, q15)?;

    let faces_q25 = fit_all_faces(design, q25, Some(&faces_q15))?;
    let diagnostics_q25 = face_diagnostics(&faces_q25);
    let selected_q25 = select_face(&faces_q25)?;
    validate_face_transition(&selected_q15, &selected_q25, &faces_q25)?;
    guard_selected_optimum(design, &selected_q25, q25)?;

    let order_delta = parameter_order_delta(&selected_q15, &selected_q25, design.model)?;
    if order_delta > PARAMETER_ORDER_TOL {
        return Err(format!(
            "STOP_QUADRATURE_NONCONVERGENCE:parameter_delta:{order_delta:.17e}"
        ));
    }
    if selected_q25.optimum.gradient_inf > OPT_GRAD_TOL {
        return Err(format!(
            "STOP_OPTIMIZER_NONCONVERGENCE:q25_gradient:{:.17e}",
            selected_q25.optimum.gradient_inf
        ));
    }
    let hessian_condition = five_point_hessian_condition(
        design,
        selected_q25.face,
        &selected_q25.optimum.parameters,
        q25,
    )?;
    let heldout_q15 = heldout_log_likelihood(
        design,
        selected_q15.face,
        &selected_q15.optimum.parameters,
        q15,
    )?;
    let heldout_q25 = heldout_log_likelihood(
        design,
        selected_q25.face,
        &selected_q25.optimum.parameters,
        q25,
    )?;

    let fixed_q35_delta = quadrature_cell_delta(
        design,
        selected_q25.face,
        &selected_q25.optimum.parameters,
        q25,
        q35,
    )?;
    let (
        final_face,
        final_parameters,
        final_train_log_likelihood,
        final_heldout_log_likelihood,
        audit_heldout_log_likelihood,
        final_order,
        audit_order,
        final_cell_delta,
        fallback_delta,
        final_gradient,
        final_gradient_inf,
        final_projected_gradient_inf,
        fallback_diagnostics,
    ) = if fixed_q35_delta <= CELL_QUADRATURE_TOL && !force_fallback_for_self_test {
        let audit_heldout = heldout_log_likelihood(
            design,
            selected_q25.face,
            &selected_q25.optimum.parameters,
            q35,
        )?;
        (
            selected_q25.face,
            selected_q25.optimum.parameters.clone(),
            selected_q25.optimum.log_likelihood,
            heldout_q25,
            audit_heldout,
            25,
            35,
            fixed_q35_delta,
            None,
            selected_q25.optimum.gradient.clone(),
            selected_q25.optimum.gradient_inf,
            selected_q25.optimum.projected_gradient_inf,
            Vec::new(),
        )
    } else {
        let faces_q35 = fit_all_faces(design, q35, Some(&faces_q25))?;
        let diagnostics_q35 = face_diagnostics(&faces_q35);
        let selected_q35 = select_face(&faces_q35)?;
        validate_face_transition(&selected_q25, &selected_q35, &faces_q35)?;
        guard_selected_optimum(design, &selected_q35, q35)?;
        let fallback_parameter_delta =
            parameter_order_delta(&selected_q25, &selected_q35, design.model)?;
        if fallback_parameter_delta > PARAMETER_ORDER_TOL {
            return Err(format!(
                "STOP_QUADRATURE_NONCONVERGENCE:q35_parameter_delta:{fallback_parameter_delta:.17e}"
            ));
        }
        let q45_delta = quadrature_cell_delta(
            design,
            selected_q35.face,
            &selected_q35.optimum.parameters,
            q35,
            q45,
        )?;
        if q45_delta > CELL_QUADRATURE_TOL {
            return Err(format!(
                "STOP_QUADRATURE_NONCONVERGENCE:q45_cell_delta:{q45_delta:.17e}"
            ));
        }
        let heldout_q35 = heldout_log_likelihood(
            design,
            selected_q35.face,
            &selected_q35.optimum.parameters,
            q35,
        )?;
        let heldout_q45 = heldout_log_likelihood(
            design,
            selected_q35.face,
            &selected_q35.optimum.parameters,
            q45,
        )?;
        (
            selected_q35.face,
            selected_q35.optimum.parameters.clone(),
            selected_q35.optimum.log_likelihood,
            heldout_q35,
            heldout_q45,
            35,
            45,
            q45_delta,
            Some(fallback_parameter_delta),
            selected_q35.optimum.gradient.clone(),
            selected_q35.optimum.gradient_inf,
            selected_q35.optimum.projected_gradient_inf,
            diagnostics_q35,
        )
    };

    Ok(FoldModelFit {
        heldout_cell: design.heldout_cell,
        model: design.model,
        face_q15: selected_q15.face,
        face_q25: selected_q25.face,
        face: final_face,
        parameters_q15: selected_q15.optimum.parameters,
        parameters_q25: selected_q25.optimum.parameters,
        parameters_final: final_parameters,
        train_log_likelihood_q15: selected_q15.optimum.log_likelihood,
        train_log_likelihood_q25: selected_q25.optimum.log_likelihood,
        train_log_likelihood_final: final_train_log_likelihood,
        heldout_log_likelihood_q15: heldout_q15,
        heldout_log_likelihood_q25: heldout_q25,
        heldout_log_likelihood_final: final_heldout_log_likelihood,
        heldout_log_likelihood_audit: audit_heldout_log_likelihood,
        final_order,
        audit_order,
        q15_converged_starts: selected_q15.converged_starts,
        q25_converged_starts: selected_q25.converged_starts,
        q15_best_three_spread: selected_q15.best_three_spread,
        q25_best_three_spread: selected_q25.best_three_spread,
        q15_iterations: selected_q15.optimum.iterations,
        q25_iterations: selected_q25.optimum.iterations,
        q15_evaluations: selected_q15.optimum.evaluations,
        q25_evaluations: selected_q25.optimum.evaluations,
        gradient_q25: selected_q25.optimum.gradient.clone(),
        gradient_inf_q25: selected_q25.optimum.gradient_inf,
        projected_gradient_inf_q25: selected_q25.optimum.projected_gradient_inf,
        hessian_condition_q25: hessian_condition,
        parameter_order_delta: order_delta,
        initial_q25_q35_cell_delta: fixed_q35_delta,
        fallback_parameter_delta: fallback_delta,
        quadrature_cell_delta: final_cell_delta,
        gradient_final: final_gradient,
        gradient_inf_final: final_gradient_inf,
        projected_gradient_inf_final: final_projected_gradient_inf,
        training_rows: design.training_rows,
        heldout_rows: design.heldout.row_count,
        scaler: design.scaler.clone(),
        training_rowset_sha256: design.training_rowset_sha256.clone(),
        training_design_sha256: design.training_design_sha256.clone(),
        heldout_rowset_sha256: design.heldout_rowset_sha256.clone(),
        design_sha256: design.design_sha256.clone(),
        face_diagnostics_q15: diagnostics_q15,
        face_diagnostics_q25: diagnostics_q25,
        face_diagnostics_fallback: fallback_diagnostics,
    })
}

fn model_index(model: ModelKind) -> usize {
    match model {
        ModelKind::V0 => 0,
        ModelKind::V1 => 1,
        ModelKind::V1Z => 2,
        ModelKind::V2 => 3,
    }
}

fn make_comparison(
    name: &'static str,
    reduced: ModelKind,
    augmented: ModelKind,
    pooled_scores: &[f64; 4],
    macro_scores: &[f64; 4],
    per_cell_scores: &[[f64; 8]; 4],
) -> ComparisonDecision {
    let reduced_index = model_index(reduced);
    let augmented_index = model_index(augmented);
    let pooled_delta = pooled_scores[reduced_index] - pooled_scores[augmented_index];
    let macro_delta = macro_scores[reduced_index] - macro_scores[augmented_index];
    let mut cell_deltas = [0.0; 8];
    let mut positive_cells = 0usize;
    let mut negative_cells = 0usize;
    for cell in 0..8 {
        let delta = per_cell_scores[reduced_index][cell]
            - per_cell_scores[augmented_index][cell];
        cell_deltas[cell] = delta;
        if delta > SIGN_ZERO_TOL {
            positive_cells += 1;
        } else if delta < -SIGN_ZERO_TOL {
            negative_cells += 1;
        }
    }
    let gain_cell_guard = cell_deltas
        .iter()
        .all(|delta| *delta >= -CELL_GUARD_KAPPA);
    let loss_cell_guard = cell_deltas
        .iter()
        .all(|delta| *delta <= CELL_GUARD_KAPPA);
    let gain = pooled_delta >= GAIN_EPSILON
        && macro_delta >= GAIN_EPSILON / 2.0
        && positive_cells >= 6
        && gain_cell_guard;
    let loss = pooled_delta <= -GAIN_EPSILON
        && macro_delta <= -GAIN_EPSILON / 2.0
        && negative_cells >= 6
        && loss_cell_guard;
    let decision = if gain {
        "ROBUST_DESCRIPTIVE_GAIN"
    } else if loss {
        "ROBUST_DESCRIPTIVE_LOSS"
    } else {
        "DESCRIPTIVE_TIE_OR_MIXED"
    };
    ComparisonDecision {
        name,
        reduced,
        augmented,
        pooled_delta,
        macro_delta,
        cell_deltas,
        positive_cells,
        negative_cells,
        decision,
        gain_cell_guard_fail: !gain_cell_guard,
        gain_pooled_margin_fail: pooled_delta < GAIN_EPSILON,
        gain_macro_margin_fail: macro_delta < GAIN_EPSILON / 2.0,
        gain_sign_count_fail: positive_cells < 6,
        loss_cell_guard_fail: !loss_cell_guard,
        loss_pooled_margin_fail: pooled_delta > -GAIN_EPSILON,
        loss_macro_margin_fail: macro_delta > -GAIN_EPSILON / 2.0,
        loss_sign_count_fail: negative_cells < 6,
    }
}

fn dataset_denominators(
    dataset: &Dataset,
    enforce_source_lock: bool,
) -> AppResult<(usize, [usize; 8])> {
    let mut cell_rows = [0usize; 8];
    for row in &dataset.rows {
        if !(1..=8).contains(&row.key.cell) {
            return Err("STOP_FOLD_PARTITION_MISMATCH:cell_domain".to_string());
        }
        cell_rows[(row.key.cell - 1) as usize] += 1;
    }
    let comparison_rows = cell_rows.iter().sum::<usize>();
    if comparison_rows != dataset.rows.len() || cell_rows.contains(&0) {
        return Err("STOP_FOLD_PARTITION_MISMATCH:denominators".to_string());
    }
    if enforce_source_lock
        && (comparison_rows != EXPECTED_COMPARISON_ROWS || cell_rows != EXPECTED_CELL_ROWS)
    {
        return Err("STOP_FOLD_PARTITION_MISMATCH:production_denominators".to_string());
    }
    Ok((comparison_rows, cell_rows))
}

fn aggregate_fit_report(
    folds: Vec<FoldModelFit>,
    comparison_rows: usize,
    cell_rows: [usize; 8],
) -> AppResult<FitReport> {
    if folds.len() != 32
        || comparison_rows == 0
        || cell_rows.contains(&0)
        || cell_rows.iter().sum::<usize>() != comparison_rows
    {
        return Err("STOP_FOLD_PARTITION_MISMATCH:fit_count_or_denominator".to_string());
    }
    let mut fold_keys = BTreeSet::new();
    for fold in &folds {
        if !(1..=8).contains(&fold.heldout_cell)
            || !fold_keys.insert((fold.heldout_cell, fold.model))
            || fold.heldout_rows != cell_rows[(fold.heldout_cell - 1) as usize]
        {
            return Err("STOP_FOLD_PARTITION_MISMATCH:fold_identity_or_rows".to_string());
        }
    }
    if fold_keys.len() != 32 {
        return Err("STOP_FOLD_PARTITION_MISMATCH:fold_key_completeness".to_string());
    }
    let mut pooled_scores_q15 = [0.0; 4];
    let mut pooled_scores_q25 = [0.0; 4];
    let mut pooled_scores = [0.0; 4];
    let mut macro_scores = [0.0; 4];
    let mut per_cell_scores = [[0.0; 8]; 4];
    for model in ModelKind::ALL {
        let model_folds = folds
            .iter()
            .filter(|fold| fold.model == model)
            .collect::<Vec<_>>();
        if model_folds.len() != 8 {
            return Err("STOP_FOLD_PARTITION_MISMATCH:model_fold_count".to_string());
        }
        let q15_score = -model_folds
            .iter()
            .map(|fold| fold.heldout_log_likelihood_q15)
            .sum::<f64>()
            / comparison_rows as f64;
        let q25_score = -model_folds
            .iter()
            .map(|fold| fold.heldout_log_likelihood_q25)
            .sum::<f64>()
            / comparison_rows as f64;
        if (q25_score - q15_score).abs() > CV_ORDER_TOL {
            let observed = (q25_score - q15_score).abs();
            return Err(format!(
                "STOP_QUADRATURE_NONCONVERGENCE:{}:q15_q25_cv:expected=abs_delta<={CV_ORDER_TOL:.17e}:observed={observed:.17e}",
                model.name(),
            ));
        }
        let final_score = -model_folds
            .iter()
            .map(|fold| fold.heldout_log_likelihood_final)
            .sum::<f64>()
            / comparison_rows as f64;
        let index = model_index(model);
        pooled_scores_q15[index] = q15_score;
        pooled_scores_q25[index] = q25_score;
        pooled_scores[index] = final_score;
        for fold in model_folds {
            let cell_index = (fold.heldout_cell - 1) as usize;
            per_cell_scores[index][cell_index] =
                -fold.heldout_log_likelihood_final / cell_rows[cell_index] as f64;
        }
        macro_scores[index] = per_cell_scores[index].iter().sum::<f64>() / 8.0;
    }
    let comparisons = vec![
        make_comparison(
            "V1_MINUS_V0",
            ModelKind::V0,
            ModelKind::V1,
            &pooled_scores,
            &macro_scores,
            &per_cell_scores,
        ),
        make_comparison(
            "V1Z_MINUS_V1",
            ModelKind::V1,
            ModelKind::V1Z,
            &pooled_scores,
            &macro_scores,
            &per_cell_scores,
        ),
        make_comparison(
            "V2_MINUS_V1Z",
            ModelKind::V1Z,
            ModelKind::V2,
            &pooled_scores,
            &macro_scores,
            &per_cell_scores,
        ),
    ];
    Ok(FitReport {
        folds,
        comparison_rows,
        cell_rows,
        pooled_scores_q15,
        pooled_scores_q25,
        pooled_scores,
        macro_scores,
        per_cell_scores,
        comparisons,
    })
}

fn fit_dataset_with_fitter<F>(
    dataset: &Dataset,
    enforce_source_lock: bool,
    mut fitter: F,
) -> AppResult<FitReport>
where
    F: FnMut(&FoldDesign) -> AppResult<FoldModelFit>,
{
    let (comparison_rows, cell_rows) = dataset_denominators(dataset, enforce_source_lock)?;
    let mut folds = Vec::with_capacity(32);
    for heldout_cell in 1u8..=8 {
        for model in ModelKind::ALL {
            let design = build_fold_design(dataset, heldout_cell, model, enforce_source_lock)?;
            let fit = fitter(&design)?;
            if fit.heldout_cell != design.heldout_cell
                || fit.model != design.model
                || fit.training_rows != design.training_rows
                || fit.heldout_rows != design.heldout.row_count
                || fit.training_rowset_sha256 != design.training_rowset_sha256
                || fit.training_design_sha256 != design.training_design_sha256
                || fit.heldout_rowset_sha256 != design.heldout_rowset_sha256
                || fit.design_sha256 != design.design_sha256
            {
                return Err("STOP_MODEL_ROWSET_MISMATCH:fitter_identity".to_string());
            }
            folds.push(fit);
        }
    }
    aggregate_fit_report(folds, comparison_rows, cell_rows)
}

fn fit_dataset(dataset: &Dataset) -> AppResult<FitReport> {
    let q15 = Quadrature::gauss_hermite(15)?;
    let q25 = Quadrature::gauss_hermite(25)?;
    let q35 = Quadrature::gauss_hermite(35)?;
    let q45 = Quadrature::gauss_hermite(45)?;
    fit_dataset_with_fitter(dataset, true, |design| {
        fit_fold_model(design, &q15, &q25, &q35, &q45)
    })
}

const EXECUTION_LOCK_KEYS: [&str; 29] = [
    "schema_version",
    "real_data_fit_authorized",
    "comparison_contract_sha256",
    "rust_source_sha256",
    "wrapper_sha256",
    "source_manifest_sha256",
    "preflight_auditor_sha256",
    "preflight_receipt_sha256",
    "preflight_decision",
    "raw_csv_sha256",
    "raw_csv_bytes",
    "dictionary_sha256",
    "dictionary_bytes",
    "rowset_sha256",
    "comparison_rows",
    "comparison_events",
    "age_rows",
    "age_events",
    "cell_rows",
    "cell_events",
    "model_feature_order",
    "numerical_tolerance_profile",
    "self_test_core_sha256",
    "rustc_version",
    "rustc_verbose_sha256",
    "rustc_host",
    "rustc_executable_sha256",
    "compile_flags",
    "runtime_threads",
];

const EXPECTED_COMPILE_FLAGS: &str = "--edition=2021 -C opt-level=3 -C debuginfo=0 -C overflow-checks=yes -C target-feature=-fma -C codegen-units=1";
const EXPECTED_RUSTC_VERSION: &str = "rustc 1.95.0 (59807616e 2026-04-14)";
const EXPECTED_RUSTC_HOST: &str = "x86_64-pc-windows-msvc";

#[derive(Clone, Debug)]
struct ExecutionLock {
    sha256: String,
    values: BTreeMap<String, String>,
}

impl ExecutionLock {
    fn value(&self, key: &str) -> AppResult<&str> {
        self.values
            .get(key)
            .map(String::as_str)
            .ok_or_else(|| format!("STOP_CONTRACT_SCHEMA_MISMATCH:missing:{key}"))
    }
}

fn is_lower_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn parse_strict_lock(bytes: &[u8], expected_sha256: Option<&str>) -> AppResult<ExecutionLock> {
    let observed_sha256 = sha256_hex(bytes);
    if let Some(expected) = expected_sha256 {
        if !is_lower_sha256(expected) || observed_sha256 != expected {
            return Err(format!(
                "STOP_EXECUTION_CONTRACT_HASH_MISMATCH:expected={expected}:observed={observed_sha256}"
            ));
        }
    }
    if bytes.starts_with(&[0xef, 0xbb, 0xbf])
        || bytes.contains(&b'\r')
        || !bytes.ends_with(b"\n")
        || bytes.ends_with(b"\n\n")
    {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:encoding_or_newline".to_string());
    }
    let text = std::str::from_utf8(bytes)
        .map_err(|_| "STOP_CONTRACT_SCHEMA_MISMATCH:utf8".to_string())?;
    let lines = text.strip_suffix('\n').unwrap().split('\n').collect::<Vec<_>>();
    if lines.first().copied() != Some("key\tvalue") || lines.len() != EXECUTION_LOCK_KEYS.len() + 1
    {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:header_or_row_count".to_string());
    }
    let mut values = BTreeMap::new();
    for (index, expected_key) in EXECUTION_LOCK_KEYS.iter().enumerate() {
        let fields = lines[index + 1].split('\t').collect::<Vec<_>>();
        if fields.len() != 2
            || fields[0] != *expected_key
            || fields[1].is_empty()
            || values
                .insert(fields[0].to_string(), fields[1].to_string())
                .is_some()
        {
            return Err(format!(
                "STOP_CONTRACT_SCHEMA_MISMATCH:row:{}:expected={expected_key}",
                index + 2
            ));
        }
    }
    Ok(ExecutionLock {
        sha256: observed_sha256,
        values,
    })
}

fn validate_execution_lock(lock: &ExecutionLock, require_authorized: bool) -> AppResult<()> {
    let expected_values = [
        (
            "schema_version",
            "ce_npf_loewenstein_2015_v0_v2_execution_lock_v1",
        ),
        ("source_manifest_sha256", EXPECTED_SOURCE_MANIFEST_SHA256),
        (
            "preflight_auditor_sha256",
            EXPECTED_PREFLIGHT_AUDITOR_SHA256,
        ),
        (
            "preflight_receipt_sha256",
            EXPECTED_PREFLIGHT_RECEIPT_SHA256,
        ),
        ("preflight_decision", "PARTIAL_MODEL_ELIGIBILITY"),
        ("raw_csv_sha256", EXPECTED_DATA_SHA256),
        ("dictionary_sha256", EXPECTED_DICTIONARY_SHA256),
        ("rowset_sha256", EXPECTED_ROWSET_SHA256),
        ("comparison_rows", "2723"),
        ("comparison_events", "1459"),
        ("age_rows", "1861,557,219,86"),
        ("age_events", "1122,249,66,22"),
        ("cell_rows", "529,151,404,433,419,401,353,33"),
        ("cell_events", "321,72,201,231,229,202,185,18"),
        ("model_feature_order", EXPECTED_MODEL_FEATURE_ORDER),
        ("numerical_tolerance_profile", EXPECTED_TOLERANCE_PROFILE),
        ("rustc_version", EXPECTED_RUSTC_VERSION),
        ("rustc_host", EXPECTED_RUSTC_HOST),
        ("compile_flags", EXPECTED_COMPILE_FLAGS),
        ("runtime_threads", "1"),
    ];
    for (key, expected) in expected_values {
        let observed = lock.value(key)?;
        if observed != expected {
            return Err(format!(
                "STOP_CONTRACT_SCHEMA_MISMATCH:{key}:expected={expected}:observed={observed}"
            ));
        }
    }
    if lock.value("raw_csv_bytes")? != EXPECTED_DATA_BYTES.to_string() {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:raw_csv_bytes".to_string());
    }
    if lock.value("dictionary_bytes")? != EXPECTED_DICTIONARY_BYTES.to_string() {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:dictionary_bytes".to_string());
    }
    for key in [
        "comparison_contract_sha256",
        "rust_source_sha256",
        "wrapper_sha256",
        "self_test_core_sha256",
        "rustc_verbose_sha256",
        "rustc_executable_sha256",
    ] {
        if !is_lower_sha256(lock.value(key)?) {
            return Err(format!("STOP_CONTRACT_SCHEMA_MISMATCH:{key}:sha256"));
        }
    }
    let authorization = lock.value("real_data_fit_authorized")?;
    if authorization != "true" && authorization != "false" {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:authorization_boolean".to_string());
    }
    if require_authorized && authorization != "true" {
        return Err("STOP_REAL_DATA_NOT_AUTHORIZED:execution_lock_false".to_string());
    }
    Ok(())
}

fn json_escape(value: &str) -> String {
    let mut output = String::new();
    for character in value.chars() {
        match character {
            '"' => output.push_str("\\\""),
            '\\' => output.push_str("\\\\"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            value if value <= '\u{001f}' => {
                write!(&mut output, "\\u{:04x}", value as u32).unwrap();
            }
            value => output.push(value),
        }
    }
    output
}

fn json_string(value: &str) -> String {
    format!("\"{}\"", json_escape(value))
}

fn json_float(value: f64) -> AppResult<String> {
    if !value.is_finite() {
        return Err("STOP_RECEIPT_NONDETERMINISTIC:nonfinite_float".to_string());
    }
    let normalized = if value == 0.0 { 0.0 } else { value };
    Ok(format!("{normalized:.17e}"))
}

fn json_float_array(values: &[f64]) -> AppResult<String> {
    let mut output = String::from("[");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        output.push_str(&json_float(*value)?);
    }
    output.push(']');
    Ok(output)
}

fn json_optional_float(value: Option<f64>) -> AppResult<String> {
    match value {
        Some(value) => json_float(value),
        None => Ok("null".to_string()),
    }
}

fn json_optional_bool(value: Option<bool>) -> &'static str {
    match value {
        Some(true) => "true",
        Some(false) => "false",
        None => "null",
    }
}

fn json_string_array(values: &[&str]) -> String {
    let mut output = String::from("[");
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        output.push_str(&json_string(value));
    }
    output.push(']');
    output
}

fn diagnostic_lower_guard_reduction(
    diagnostic: &FaceDiagnostic,
    model: ModelKind,
) -> Option<VarianceFace> {
    let mut index = model.dimension();
    let cell_at_lower = if diagnostic.face.cell_active() {
        let at_lower = diagnostic.parameters[index] <= SIGMA_LOWER.ln() + 1.0e-9;
        index += 1;
        at_lower
    } else {
        false
    };
    let dendrite_at_lower = if diagnostic.face.dendrite_active() {
        diagnostic.parameters[index] <= SIGMA_LOWER.ln() + 1.0e-9
    } else {
        false
    };
    match (diagnostic.face, cell_at_lower, dendrite_at_lower) {
        (_, false, false) => None,
        (VarianceFace::Cell, true, _) | (VarianceFace::Dendrite, _, true) => {
            Some(VarianceFace::None)
        }
        (VarianceFace::Both, true, true) => Some(VarianceFace::None),
        (VarianceFace::Both, true, false) => Some(VarianceFace::Dendrite),
        (VarianceFace::Both, false, true) => Some(VarianceFace::Cell),
        _ => None,
    }
}

fn render_face_diagnostics(
    diagnostics: &[FaceDiagnostic],
    selected: VarianceFace,
    model: ModelKind,
) -> AppResult<String> {
    let mut output = String::from("[");
    for (index, diagnostic) in diagnostics.iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        let reduced_to = diagnostic_lower_guard_reduction(diagnostic, model)
            .map(|face| json_string(face.name()))
            .unwrap_or_else(|| "null".to_string());
        write!(
            &mut output,
            "{{\"face\":{},\"order\":{},\"selected\":{},\"parameters\":{},\"objective\":{},\"normalized_objective\":{},\"train_log_likelihood\":{},\"converged_starts\":{},\"best_three_objective_spread\":{},\"iterations\":{},\"evaluations\":{},\"score_quadrature_gradient\":{},\"score_quadrature_gradient_inf\":{},\"projected_gradient_inf_internal\":{},\"lower_guard_reduced_to\":{}}}",
            json_string(diagnostic.face.name()),
            diagnostic.order,
            diagnostic.face == selected,
            json_float_array(&diagnostic.parameters)?,
            json_float(diagnostic.objective)?,
            json_float(diagnostic.objective)?,
            json_float(diagnostic.log_likelihood)?,
            diagnostic.converged_starts,
            json_float(diagnostic.best_three_spread)?,
            diagnostic.iterations,
            diagnostic.evaluations,
            json_float_array(&diagnostic.gradient)?,
            json_float(diagnostic.gradient_inf)?,
            json_float(diagnostic.projected_gradient_inf)?,
            reduced_to
        )
        .unwrap();
    }
    output.push(']');
    Ok(output)
}

fn render_core_receipt(
    dataset: &Dataset,
    report: &FitReport,
    lock: &ExecutionLock,
    self_test_metrics: &SelfTestMetrics,
    observed_self_test_sha256: &str,
) -> AppResult<String> {
    if !self_test_metrics_all_pass(self_test_metrics) {
        return Err("STOP_GH_SELF_TEST:production_receipt_metrics".to_string());
    }
    if !is_lower_sha256(observed_self_test_sha256)
        || lock.value("self_test_core_sha256")? != observed_self_test_sha256
    {
        return Err(format!(
            "STOP_SELF_TEST_CORE_HASH_MISMATCH:expected={}:observed={observed_self_test_sha256}",
            lock.value("self_test_core_sha256")?
        ));
    }
    let dataset_summary = summarize_dataset(dataset)?;
    if report.comparison_rows != dataset_summary.rows
        || report.cell_rows != dataset_summary.cell_rows
        || report.folds.len() != 32
        || report.folds.iter().any(|fold| {
            let cell = (fold.heldout_cell.saturating_sub(1)) as usize;
            !(1..=8).contains(&fold.heldout_cell)
                || fold.heldout_rows != dataset_summary.cell_rows[cell]
                || fold.training_rows + fold.heldout_rows != dataset_summary.rows
        })
    {
        return Err("STOP_MODEL_ROWSET_MISMATCH:receipt_consistency".to_string());
    }
    let q15 = Quadrature::gauss_hermite(15)?;
    let q25 = Quadrature::gauss_hermite(25)?;
    let q35 = Quadrature::gauss_hermite(35)?;
    let q45 = Quadrature::gauss_hermite(45)?;
    let mut output = String::new();
    output.push_str("{\n");
    writeln!(
        &mut output,
        "  \"schema_version\":{},",
        json_string("ce_npf_loewenstein_2015_v0_v2_core_receipt_v3")
    )
    .unwrap();
    output.push_str("  \"status\":\"PASS\",\n");
    writeln!(
        &mut output,
        "  \"decision_scope\":{},",
        json_string("WITHIN_PIPELINE_DESCRIPTIVE_PREDICTION_ONLY")
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"claim_ceiling\":{},",
        json_string("BIO_EVIDENCE_L0")
    )
    .unwrap();
    output.push_str("  \"catalogued_protrusion_predictive_comparison_executed\":true,\n");
    output.push_str("  \"latent_contact_hypothesis_tested\":false,\n");
    output.push_str("  \"conducting_state_tested\":false,\n");
    output.push_str("  \"riemannian_folding_tested\":false,\n");
    output.push_str("  \"heldout_random_effect_conditioning\":false,\n");
    output.push_str("  \"animal_heldout\":false,\n");
    writeln!(
        &mut output,
        "  \"execution_lock_sha256\":{},",
        json_string(&lock.sha256)
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"comparison_contract_sha256\":{},",
        json_string(lock.value("comparison_contract_sha256")?)
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"rust_source_sha256\":{},",
        json_string(lock.value("rust_source_sha256")?)
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"wrapper_sha256\":{},",
        json_string(lock.value("wrapper_sha256")?)
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"self_test_core_sha256_expected\":{},",
        json_string(lock.value("self_test_core_sha256")?)
    )
    .unwrap();
    writeln!(
        &mut output,
        "  \"self_test_core_sha256_observed\":{},",
        json_string(observed_self_test_sha256)
    )
    .unwrap();
    output.push_str("  \"self_test_core_sha256_match\":true,\n");
    writeln!(
        &mut output,
        "  \"self_test_evidence\":{},",
        render_self_test_evidence(self_test_metrics)?
    )
    .unwrap();
    output.push_str("  \"source\":{\n");
    writeln!(
        &mut output,
        "    \"raw_csv_sha256\":{},",
        json_string(EXPECTED_DATA_SHA256)
    )
    .unwrap();
    writeln!(&mut output, "    \"raw_csv_bytes\":{},", EXPECTED_DATA_BYTES).unwrap();
    writeln!(
        &mut output,
        "    \"dictionary_sha256\":{},",
        json_string(EXPECTED_DICTIONARY_SHA256)
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"dictionary_bytes\":{},",
        EXPECTED_DICTIONARY_BYTES
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"source_manifest_sha256\":{},",
        json_string(EXPECTED_SOURCE_MANIFEST_SHA256)
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"preflight_auditor_sha256\":{},",
        json_string(EXPECTED_PREFLIGHT_AUDITOR_SHA256)
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"preflight_receipt_sha256\":{}",
        json_string(EXPECTED_PREFLIGHT_RECEIPT_SHA256)
    )
    .unwrap();
    output.push_str("  },\n");
    output.push_str("  \"rowset\":{\n");
    writeln!(
        &mut output,
        "    \"sha256\":{},",
        json_string(&dataset.rowset_sha256)
    )
    .unwrap();
    writeln!(&mut output, "    \"rows\":{},", dataset_summary.rows).unwrap();
    writeln!(
        &mut output,
        "    \"events\":{},",
        dataset_summary.events
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"age_rows\":[{},{},{},{}],",
        dataset_summary.age_rows[0],
        dataset_summary.age_rows[1],
        dataset_summary.age_rows[2],
        dataset_summary.age_rows[3]
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"age_events\":[{},{},{},{}],",
        dataset_summary.age_events[0],
        dataset_summary.age_events[1],
        dataset_summary.age_events[2],
        dataset_summary.age_events[3]
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"cell_rows\":[{},{},{},{},{},{},{},{}],",
        dataset_summary.cell_rows[0],
        dataset_summary.cell_rows[1],
        dataset_summary.cell_rows[2],
        dataset_summary.cell_rows[3],
        dataset_summary.cell_rows[4],
        dataset_summary.cell_rows[5],
        dataset_summary.cell_rows[6],
        dataset_summary.cell_rows[7]
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"cell_events\":[{},{},{},{},{},{},{},{}]",
        dataset_summary.cell_events[0],
        dataset_summary.cell_events[1],
        dataset_summary.cell_events[2],
        dataset_summary.cell_events[3],
        dataset_summary.cell_events[4],
        dataset_summary.cell_events[5],
        dataset_summary.cell_events[6],
        dataset_summary.cell_events[7]
    )
    .unwrap();
    output.push_str("  },\n");
    output.push_str("  \"numerics\":{\n");
    output.push_str("    \"likelihood\":\"cloglog_4_day_interval\",\n");
    output.push_str("    \"frailty\":\"joint_nested_cell_and_dendrite_gaussian\",\n");
    output.push_str("    \"optimizer\":\"deterministic_full_bfgs_score_quadrature_armijo\",\n");
    output.push_str("    \"gradient_semantics\":\"score_quadrature_fisher_louis_not_exact_finite_q_derivative\",\n");
    writeln!(
        &mut output,
        "    \"model_feature_order\":{},",
        json_string(EXPECTED_MODEL_FEATURE_ORDER)
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"numerical_tolerance_profile\":{},",
        json_string(EXPECTED_TOLERANCE_PROFILE)
    )
    .unwrap();
    output.push_str("    \"quadrature_orders\":[15,25,35,45],\n");
    writeln!(
        &mut output,
        "    \"q15_fingerprint\":{},",
        json_string(&q15.fingerprint())
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"q25_fingerprint\":{},",
        json_string(&q25.fingerprint())
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"q35_fingerprint\":{},",
        json_string(&q35.fingerprint())
    )
    .unwrap();
    writeln!(
        &mut output,
        "    \"q45_fingerprint\":{}",
        json_string(&q45.fingerprint())
    )
    .unwrap();
    output.push_str("  },\n");
    output.push_str("  \"models\":[\n");
    for model in ModelKind::ALL {
        let index = model_index(model);
        output.push_str("    {");
        let q15_q25_delta =
            (report.pooled_scores_q25[index] - report.pooled_scores_q15[index]).abs();
        let q25_final_delta =
            (report.pooled_scores[index] - report.pooled_scores_q25[index]).abs();
        write!(
            &mut output,
            "\"name\":{},\"feature_names\":{},\"pooled_denominator\":{},\"per_cell_denominators\":[{},{},{},{},{},{},{},{}],\"pooled_nlpd_q15\":{},\"pooled_nlpd_q25\":{},\"pooled_nlpd_final\":{},\"abs_q15_q25_delta\":{},\"q15_q25_limit\":{},\"q15_q25_pass\":{},\"abs_q25_final_delta\":{},\"q25_final_semantics\":{},\"macro_nlpd_final\":{},\"per_cell_nlpd_final\":{}",
            json_string(model.name()),
            json_string_array(model.feature_names()),
            report.comparison_rows,
            report.cell_rows[0],
            report.cell_rows[1],
            report.cell_rows[2],
            report.cell_rows[3],
            report.cell_rows[4],
            report.cell_rows[5],
            report.cell_rows[6],
            report.cell_rows[7],
            json_float(report.pooled_scores_q15[index])?,
            json_float(report.pooled_scores_q25[index])?,
            json_float(report.pooled_scores[index])?,
            json_float(q15_q25_delta)?,
            json_float(CV_ORDER_TOL)?,
            q15_q25_delta <= CV_ORDER_TOL,
            json_float(q25_final_delta)?,
            json_string("record_only_fallback_path_shift"),
            json_float(report.macro_scores[index])?,
            json_float_array(&report.per_cell_scores[index])?
        )
        .unwrap();
        output.push('}');
        output.push_str(if index + 1 == ModelKind::ALL.len() {
            "\n"
        } else {
            ",\n"
        });
    }
    output.push_str("  ],\n");
    output.push_str("  \"folds\":[\n");
    for (index, fold) in report.folds.iter().enumerate() {
        output.push_str("    {");
        write!(
            &mut output,
            "\"heldout_cell\":{},\"model\":{},\"face_q15\":{},\"face_q25\":{},\"face_final\":{},",
            fold.heldout_cell,
            json_string(fold.model.name()),
            json_string(fold.face_q15.name()),
            json_string(fold.face_q25.name()),
            json_string(fold.face.name())
        )
        .unwrap();
        write!(
            &mut output,
            "\"training_rows\":{},\"heldout_rows\":{},\"training_rowset_sha256\":{},\"training_design_sha256\":{},\"heldout_rowset_sha256\":{},\"design_sha256\":{},",
            fold.training_rows,
            fold.heldout_rows,
            json_string(&fold.training_rowset_sha256),
            json_string(&fold.training_design_sha256),
            json_string(&fold.heldout_rowset_sha256),
            json_string(&fold.design_sha256)
        )
        .unwrap();
        write!(
            &mut output,
            "\"scaler_mean\":{},\"scaler_sd\":{},",
            json_float_array(&fold.scaler.mean)?,
            json_float_array(&fold.scaler.sd)?
        )
        .unwrap();
        write!(
            &mut output,
            "\"parameters_q15\":{},\"parameters_q25\":{},\"parameters_final\":{},",
            json_float_array(&fold.parameters_q15)?,
            json_float_array(&fold.parameters_q25)?,
            json_float_array(&fold.parameters_final)?
        )
        .unwrap();
        write!(
            &mut output,
            "\"train_log_likelihood_q15\":{},\"train_log_likelihood_q25\":{},\"train_log_likelihood_final\":{},",
            json_float(fold.train_log_likelihood_q15)?,
            json_float(fold.train_log_likelihood_q25)?,
            json_float(fold.train_log_likelihood_final)?
        )
        .unwrap();
        write!(
            &mut output,
            "\"heldout_log_likelihood_q15\":{},\"heldout_log_likelihood_q25\":{},\"heldout_log_likelihood_final\":{},\"heldout_log_likelihood_audit\":{},",
            json_float(fold.heldout_log_likelihood_q15)?,
            json_float(fold.heldout_log_likelihood_q25)?,
            json_float(fold.heldout_log_likelihood_final)?,
            json_float(fold.heldout_log_likelihood_audit)?
        )
        .unwrap();
        write!(
            &mut output,
            "\"final_order\":{},\"audit_order\":{},\"q15_converged_starts\":{},\"q25_converged_starts\":{},",
            fold.final_order,
            fold.audit_order,
            fold.q15_converged_starts,
            fold.q25_converged_starts
        )
        .unwrap();
        write!(
            &mut output,
            "\"q15_best_three_spread\":{},\"q25_best_three_spread\":{},\"q15_iterations\":{},\"q25_iterations\":{},\"q15_evaluations\":{},\"q25_evaluations\":{},",
            json_float(fold.q15_best_three_spread)?,
            json_float(fold.q25_best_three_spread)?,
            fold.q15_iterations,
            fold.q25_iterations,
            fold.q15_evaluations,
            fold.q25_evaluations
        )
        .unwrap();
        write!(
            &mut output,
            "\"score_quadrature_gradient_q25\":{},\"score_quadrature_gradient_inf_q25\":{},\"projected_gradient_inf_internal_q25\":{},\"projected_gradient_internal_limit\":{},\"projected_gradient_internal_pass_q25\":{},\"gradient_limit\":{},\"gradient_q25_pass\":{},\"hessian_condition_q25\":{},\"hessian_condition_limit\":{},\"hessian_condition_pass\":{},\"parameter_order_delta\":{},\"parameter_order_limit\":{},\"parameter_order_pass\":{},",
            json_float_array(&fold.gradient_q25)?,
            json_float(fold.gradient_inf_q25)?,
            json_float(fold.projected_gradient_inf_q25)?,
            json_float(OPT_INTERNAL_GRAD_TOL)?,
            fold.projected_gradient_inf_q25 <= OPT_INTERNAL_GRAD_TOL,
            json_float(OPT_GRAD_TOL)?,
            fold.gradient_inf_q25 <= OPT_GRAD_TOL,
            json_float(fold.hessian_condition_q25)?,
            json_float(HESSIAN_CONDITION_MAX)?,
            fold.hessian_condition_q25 <= HESSIAN_CONDITION_MAX,
            json_float(fold.parameter_order_delta)?,
            json_float(PARAMETER_ORDER_TOL)?,
            fold.parameter_order_delta <= PARAMETER_ORDER_TOL
        )
        .unwrap();
        let fallback_used = fold.fallback_parameter_delta.is_some();
        let fallback_parameter_pass = fold
            .fallback_parameter_delta
            .map(|value| value <= PARAMETER_ORDER_TOL);
        write!(
            &mut output,
            "\"initial_q25_q35_cell_delta\":{},\"cell_quadrature_limit\":{},\"initial_q25_q35_pass\":{},\"fallback_used\":{},\"fallback_parameter_delta\":{},\"fallback_parameter_pass\":{},\"final_audit_cell_delta\":{},\"final_audit_cell_delta_pass\":{},\"score_quadrature_gradient_final\":{},\"score_quadrature_gradient_inf_final\":{},\"projected_gradient_inf_internal_final\":{},\"projected_gradient_internal_pass_final\":{},\"gradient_final_pass\":{},",
            json_float(fold.initial_q25_q35_cell_delta)?,
            json_float(CELL_QUADRATURE_TOL)?,
            fold.initial_q25_q35_cell_delta <= CELL_QUADRATURE_TOL,
            fallback_used,
            json_optional_float(fold.fallback_parameter_delta)?,
            json_optional_bool(fallback_parameter_pass),
            json_float(fold.quadrature_cell_delta)?,
            fold.quadrature_cell_delta <= CELL_QUADRATURE_TOL,
            json_float_array(&fold.gradient_final)?,
            json_float(fold.gradient_inf_final)?,
            json_float(fold.projected_gradient_inf_final)?,
            fold.projected_gradient_inf_final <= OPT_INTERNAL_GRAD_TOL,
            fold.gradient_inf_final <= OPT_GRAD_TOL
        )
        .unwrap();
        write!(
            &mut output,
            "\"face_diagnostics_q15\":{},\"face_diagnostics_q25\":{},\"face_diagnostics_fallback\":{}",
            render_face_diagnostics(
                &fold.face_diagnostics_q15,
                fold.face_q15,
                fold.model,
            )?,
            render_face_diagnostics(
                &fold.face_diagnostics_q25,
                fold.face_q25,
                fold.model,
            )?,
            render_face_diagnostics(
                &fold.face_diagnostics_fallback,
                fold.face,
                fold.model,
            )?
        )
        .unwrap();
        output.push('}');
        output.push_str(if index + 1 == report.folds.len() {
            "\n"
        } else {
            ",\n"
        });
    }
    output.push_str("  ],\n");
    output.push_str("  \"comparisons\":[\n");
    for (index, comparison) in report.comparisons.iter().enumerate() {
        output.push_str("    {");
        write!(
            &mut output,
            "\"name\":{},\"reduced\":{},\"augmented\":{},\"pooled_delta\":{},\"macro_delta\":{},\"cell_deltas\":{},",
            json_string(comparison.name),
            json_string(comparison.reduced.name()),
            json_string(comparison.augmented.name()),
            json_float(comparison.pooled_delta)?,
            json_float(comparison.macro_delta)?,
            json_float_array(&comparison.cell_deltas)?
        )
        .unwrap();
        write!(
            &mut output,
            "\"positive_cells\":{},\"negative_cells\":{},\"decision\":{},\"gain_gate_vector\":{{\"cell_guard_fail\":{},\"pooled_margin_fail\":{},\"macro_margin_fail\":{},\"sign_count_fail\":{}}},\"loss_gate_vector\":{{\"cell_guard_fail\":{},\"pooled_margin_fail\":{},\"macro_margin_fail\":{},\"sign_count_fail\":{}}}",
            comparison.positive_cells,
            comparison.negative_cells,
            json_string(comparison.decision),
            comparison.gain_cell_guard_fail,
            comparison.gain_pooled_margin_fail,
            comparison.gain_macro_margin_fail,
            comparison.gain_sign_count_fail,
            comparison.loss_cell_guard_fail,
            comparison.loss_pooled_margin_fail,
            comparison.loss_macro_margin_fail,
            comparison.loss_sign_count_fail
        )
        .unwrap();
        output.push('}');
        output.push_str(if index + 1 == report.comparisons.len() {
            "\n"
        } else {
            ",\n"
        });
    }
    output.push_str("  ],\n");
    output.push_str("  \"governance\":{\"content_identity\":\"PASS\",\"long_term_availability\":\"NOT_LOCKED\",\"license\":\"NOT_LOCKED\"},\n");
    output.push_str("  \"forbidden_claims\":[\"mature_spine_survival\",\"synaptic_contact_truth\",\"biological_birth_or_age\",\"adolescent_fixation\",\"conducting_parent_state\",\"ctmc_or_pdmp_validation\",\"riemannian_folding\"]\n");
    output.push_str("}\n");
    Ok(output)
}

#[derive(Clone, Debug, Default)]
struct SelfTestMetrics {
    gh_weight_sum_max_error: f64,
    gh_moment_max_error: f64,
    gh_symmetry_max_error: f64,
    row_score_max_error: f64,
    row_second_max_error: f64,
    mode_max_error: f64,
    mode_score_scaled_error: f64,
    mode_curvature_scaled_error: f64,
    gradient_max_error: f64,
    gaussian_integral_error: f64,
    nested_one_dendrite_error: f64,
    nested_two_dendrite_error: f64,
    wrong_rowwise_separation: f64,
    optimizer_max_error: f64,
    optimizer_objective_spread: f64,
    hessian_eigen_max_error: f64,
    end_to_end_parameter_order_delta: f64,
    end_to_end_initial_q25_q35_cell_delta: f64,
    end_to_end_cell_quadrature_delta: f64,
    end_to_end_gradient_inf: f64,
    end_to_end_projected_gradient_inf: f64,
    loco_q15_q25_max_delta: f64,
    loco_q15_q25_rejection_delta: f64,
    sha256_known_vectors_pass: bool,
    strict_lock_negative_cases_pass: bool,
    authorization_gate_pass: bool,
    gh_finite_positive_pass: bool,
    heldout_poison_fit_bitwise_pass: bool,
    fitted_gradient_vector_bitwise_pass: bool,
    variance_faces_finite_pass: bool,
    lower_guard_reduction_pass: bool,
    comparison_direction_vectors_pass: bool,
    permutation_fit_bitwise_pass: bool,
    normal_no_fallback_pipeline_pass: bool,
    forced_fallback_pass: bool,
    fit_dataset_32_fold_aggregation_pass: bool,
    loco_q15_q25_negative_stop_exact_pass: bool,
    natural_renderer_repeat_and_null_pass: bool,
    forced_renderer_repeat_and_payload_pass: bool,
    production_core_renderer_repeat_pass: bool,
    receipt_determinism_pass: bool,
    json_golden_pass: bool,
    real_data_cli_rejection_pass: bool,
}

#[derive(Clone, Debug)]
struct LocoSelfTestFixture {
    natural_report: FitReport,
    forced_report: FitReport,
    positive_q15_q25_max_delta: f64,
    negative_q15_q25_observed_delta: f64,
}

fn scaled_error(left: f64, right: f64) -> f64 {
    (left - right).abs() / (1.0 + left.abs() + right.abs())
}

fn synthetic_lock_bytes(authorized: bool) -> Vec<u8> {
    let values = [
        (
            "schema_version",
            "ce_npf_loewenstein_2015_v0_v2_execution_lock_v1".to_string(),
        ),
        (
            "real_data_fit_authorized",
            if authorized { "true" } else { "false" }.to_string(),
        ),
        ("comparison_contract_sha256", "a".repeat(64)),
        ("rust_source_sha256", "b".repeat(64)),
        ("wrapper_sha256", "c".repeat(64)),
        (
            "source_manifest_sha256",
            EXPECTED_SOURCE_MANIFEST_SHA256.to_string(),
        ),
        (
            "preflight_auditor_sha256",
            EXPECTED_PREFLIGHT_AUDITOR_SHA256.to_string(),
        ),
        (
            "preflight_receipt_sha256",
            EXPECTED_PREFLIGHT_RECEIPT_SHA256.to_string(),
        ),
        (
            "preflight_decision",
            "PARTIAL_MODEL_ELIGIBILITY".to_string(),
        ),
        ("raw_csv_sha256", EXPECTED_DATA_SHA256.to_string()),
        ("raw_csv_bytes", EXPECTED_DATA_BYTES.to_string()),
        (
            "dictionary_sha256",
            EXPECTED_DICTIONARY_SHA256.to_string(),
        ),
        (
            "dictionary_bytes",
            EXPECTED_DICTIONARY_BYTES.to_string(),
        ),
        ("rowset_sha256", EXPECTED_ROWSET_SHA256.to_string()),
        ("comparison_rows", "2723".to_string()),
        ("comparison_events", "1459".to_string()),
        ("age_rows", "1861,557,219,86".to_string()),
        ("age_events", "1122,249,66,22".to_string()),
        ("cell_rows", "529,151,404,433,419,401,353,33".to_string()),
        ("cell_events", "321,72,201,231,229,202,185,18".to_string()),
        (
            "model_feature_order",
            EXPECTED_MODEL_FEATURE_ORDER.to_string(),
        ),
        (
            "numerical_tolerance_profile",
            EXPECTED_TOLERANCE_PROFILE.to_string(),
        ),
        ("self_test_core_sha256", "e".repeat(64)),
        ("rustc_version", EXPECTED_RUSTC_VERSION.to_string()),
        ("rustc_verbose_sha256", "f".repeat(64)),
        ("rustc_host", EXPECTED_RUSTC_HOST.to_string()),
        ("rustc_executable_sha256", "d".repeat(64)),
        ("compile_flags", EXPECTED_COMPILE_FLAGS.to_string()),
        ("runtime_threads", "1".to_string()),
    ];
    let mut output = String::from("key\tvalue\n");
    for (key, value) in values {
        writeln!(&mut output, "{key}\t{value}").unwrap();
    }
    output.into_bytes()
}

fn self_test_sha_and_lock() -> AppResult<(bool, bool)> {
    let vectors = [
        (
            b"".as_slice(),
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        ),
        (
            b"abc".as_slice(),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        ),
    ];
    for (bytes, expected) in vectors {
        if sha256_hex(bytes) != expected {
            return Err("STOP_GH_SELF_TEST:sha256_vector".to_string());
        }
    }
    let locked = synthetic_lock_bytes(false);
    let parsed = parse_strict_lock(&locked, Some(&sha256_hex(&locked)))?;
    validate_execution_lock(&parsed, false)?;
    let authorization_error = match validate_execution_lock(&parsed, true) {
        Ok(()) => return Err("STOP_GH_SELF_TEST:authorization_gate".to_string()),
        Err(error) => error,
    };
    if !authorization_error.starts_with("STOP_REAL_DATA_NOT_AUTHORIZED:") {
        return Err("STOP_GH_SELF_TEST:authorization_gate".to_string());
    }
    let authorized = synthetic_lock_bytes(true);
    let authorized_lock = parse_strict_lock(&authorized, Some(&sha256_hex(&authorized)))?;
    validate_execution_lock(&authorized_lock, true)?;

    let reject = |candidate: &[u8], expected_hash: Option<&str>| -> AppResult<()> {
        if parse_strict_lock(candidate, expected_hash).is_ok() {
            Err("STOP_GH_SELF_TEST:strict_lock_negative_accepted".to_string())
        } else {
            Ok(())
        }
    };
    let mut extra_column = locked.clone();
    let insertion = extra_column
        .iter()
        .position(|byte| *byte == b'\n')
        .ok_or_else(|| "STOP_GH_SELF_TEST:lock_fixture".to_string())?;
    extra_column.splice(insertion..insertion, b"\textra".iter().copied());
    reject(&extra_column, None)?;
    let mut bom = vec![0xef, 0xbb, 0xbf];
    bom.extend_from_slice(&locked);
    reject(&bom, None)?;
    let crlf = String::from_utf8(locked.clone())
        .map_err(|_| "STOP_GH_SELF_TEST:lock_fixture_utf8".to_string())?
        .replace('\n', "\r\n")
        .into_bytes();
    reject(&crlf, None)?;
    let mut no_final_lf = locked.clone();
    no_final_lf.pop();
    reject(&no_final_lf, None)?;
    let locked_text = std::str::from_utf8(&locked)
        .map_err(|_| "STOP_GH_SELF_TEST:lock_fixture_utf8".to_string())?;
    let mut reordered_lines = locked_text
        .strip_suffix('\n')
        .unwrap()
        .split('\n')
        .map(str::to_string)
        .collect::<Vec<_>>();
    reordered_lines.swap(1, 2);
    let reordered = (reordered_lines.join("\n") + "\n").into_bytes();
    reject(&reordered, None)?;
    let mut duplicate_lines = locked_text
        .strip_suffix('\n')
        .unwrap()
        .split('\n')
        .map(str::to_string)
        .collect::<Vec<_>>();
    duplicate_lines[2] = duplicate_lines[1].clone();
    let duplicated = (duplicate_lines.join("\n") + "\n").into_bytes();
    reject(&duplicated, None)?;
    reject(&locked, Some(&"0".repeat(64)))?;
    let expected_hash = "1".repeat(64);
    let observed_hash = "2".repeat(64);
    let explicit_error = format!(
        "STOP_SELF_TEST_CORE_HASH_MISMATCH:expected={expected_hash}:observed={observed_hash}"
    );
    let explicit_receipt = render_stop_receipt(&explicit_error, false);
    if !explicit_receipt.contains(&format!("\"expected\":\"{expected_hash}\""))
        || !explicit_receipt.contains(&format!("\"observed\":\"{observed_hash}\""))
    {
        return Err("STOP_GH_SELF_TEST:stop_receipt_explicit_values".to_string());
    }
    let generic_receipt = render_stop_receipt(
        "STOP_SOURCE_CONTENT_MISMATCH:read:C:\\private\\nondeterministic",
        false,
    );
    if generic_receipt.contains("private")
        || !generic_receipt.contains("\"expected\":\"all_locked_gates_pass\"")
    {
        return Err("STOP_GH_SELF_TEST:stop_receipt_generic_redaction".to_string());
    }
    Ok((true, true))
}

fn self_test_quadrature() -> AppResult<(f64, f64, f64)> {
    let mut weight_sum_max_error = 0.0f64;
    let mut moment_max_error = 0.0f64;
    let mut symmetry_max_error = 0.0f64;
    for order in [15usize, 25, 35, 45] {
        let quadrature = Quadrature::gauss_hermite(order)?;
        quadrature.self_check()?;
        if !is_lower_sha256(&quadrature.fingerprint()) {
            return Err("STOP_GH_SELF_TEST:fingerprint".to_string());
        }
        weight_sum_max_error = weight_sum_max_error
            .max((quadrature.weights.iter().sum::<f64>() - PI.sqrt()).abs());
        let normal_weights = quadrature
            .weights
            .iter()
            .map(|weight| weight / PI.sqrt())
            .collect::<Vec<_>>();
        for (power, target) in [0usize, 1, 2, 3, 4, 6]
            .into_iter()
            .zip([1.0, 0.0, 1.0, 0.0, 3.0, 15.0])
        {
            let observed = normal_weights
                .iter()
                .zip(&quadrature.nodes)
                .map(|(weight, node)| weight * (SQRT_2 * node).powi(power as i32))
                .sum::<f64>();
            moment_max_error = moment_max_error.max((observed - target).abs());
        }
        for index in 0..quadrature.order {
            let mirror = quadrature.order - 1 - index;
            symmetry_max_error = symmetry_max_error
                .max((quadrature.nodes[index] + quadrature.nodes[mirror]).abs())
                .max((quadrature.weights[index] - quadrature.weights[mirror]).abs());
        }
    }
    Ok((
        weight_sum_max_error,
        moment_max_error,
        symmetry_max_error,
    ))
}

fn self_test_row_likelihood() -> AppResult<(f64, f64)> {
    let mut score_error = 0.0f64;
    let mut second_error = 0.0f64;
    let mut score_context = String::new();
    let mut second_context = String::new();
    let step = 1.0e-5;
    for event in [0u8, 1u8] {
        for eta in [-30.0, -12.0, -4.0, -1.0, 0.0, 2.0, 5.0] {
            let center = row_likelihood(event, eta)?;
            let minus = row_likelihood(event, eta - step)?;
            let plus = row_likelihood(event, eta + step)?;
            let finite_score = (plus.log_value - minus.log_value) / (2.0 * step);
            let finite_second = (plus.score - minus.score) / (2.0 * step);
            let current_score_error = (finite_score - center.score).abs();
            let current_second_error = (finite_second - center.second).abs();
            if current_score_error > score_error {
                score_error = current_score_error;
                score_context = format!("event={event}:eta={eta}");
            }
            if current_second_error > second_error {
                second_error = current_second_error;
                second_context = format!("event={event}:eta={eta}");
            }
        }
    }
    if score_error > SYN_ROW_DERIVATIVE_TOL || second_error > SYN_ROW_DERIVATIVE_TOL {
        return Err(format!(
            "STOP_GH_SELF_TEST:row_derivative:{score_error:.17e}:{score_context}:{second_error:.17e}:{second_context}"
        ));
    }
    Ok((score_error, second_error))
}

fn self_test_mode() -> AppResult<f64> {
    let target = 1.25;
    let sigma = 0.7;
    let (mode, scale) = find_concave_mode(
        |point| {
            let residual = (point - target) / sigma;
            Ok((
                -0.5 * residual * residual,
                -(point - target) / (sigma * sigma),
                -1.0 / (sigma * sigma),
            ))
        },
        "self_test_quadratic",
    )?;
    let error = (mode - target).abs().max((scale - sigma).abs());
    if error > SYN_MODE_TOL {
        return Err(format!("STOP_GH_SELF_TEST:mode:{error:.17e}"));
    }
    Ok(error)
}

fn self_test_integral_mode_derivatives() -> AppResult<(f64, f64)> {
    let quadrature = Quadrature::gauss_hermite(35)?;
    let cell = fixture_cell(1, true);
    let beta = [-1.1];
    let sigma_u = 0.55;
    let sigma_v = 0.35;
    let mut maximum_score = 0.0f64;
    let mut maximum_curvature = 0.0f64;

    let u: f64 = 0.2;
    let step = 1.0e-5 * (1.0 + u.abs());
    let center = inner_integral(&cell.dendrites[0], &beta, u, sigma_v, &quadrature)?;
    let minus =
        inner_integral(&cell.dendrites[0], &beta, u - step, sigma_v, &quadrature)?;
    let plus =
        inner_integral(&cell.dendrites[0], &beta, u + step, sigma_v, &quadrature)?;
    let finite_score = (plus.log_integral - minus.log_integral) / (2.0 * step);
    let finite_curvature = (plus.u_score - minus.u_score) / (2.0 * step);
    maximum_score = maximum_score.max(scaled_error(center.u_score, finite_score));
    maximum_curvature =
        maximum_curvature.max(scaled_error(center.u_second, finite_curvature));

    let outer_u: f64 = 0.1;
    let outer_step = 1.0e-5 * (1.0 + outer_u.abs());
    let outer_center =
        outer_point(&cell, &beta, outer_u, sigma_u, sigma_v, &quadrature)?;
    let outer_minus = outer_point(
        &cell,
        &beta,
        outer_u - outer_step,
        sigma_u,
        sigma_v,
        &quadrature,
    )?;
    let outer_plus = outer_point(
        &cell,
        &beta,
        outer_u + outer_step,
        sigma_u,
        sigma_v,
        &quadrature,
    )?;
    let outer_finite_score =
        (outer_plus.log_integrand - outer_minus.log_integrand) / (2.0 * outer_step);
    let outer_finite_curvature =
        (outer_plus.derivative - outer_minus.derivative) / (2.0 * outer_step);
    maximum_score =
        maximum_score.max(scaled_error(outer_center.derivative, outer_finite_score));
    maximum_curvature = maximum_curvature.max(scaled_error(
        outer_center.second,
        outer_finite_curvature,
    ));
    if maximum_score > SYN_MODE_SCORE_SCALED_TOL
        || maximum_curvature > SYN_MODE_CURVATURE_SCALED_TOL
    {
        return Err(format!(
            "STOP_GH_SELF_TEST:mode_derivatives:{maximum_score:.17e}:{maximum_curvature:.17e}"
        ));
    }
    Ok((maximum_score, maximum_curvature))
}

fn fixture_row(event: u8, intercept_only: bool, value: f64) -> ModelRow {
    ModelRow {
        event,
        x: if intercept_only {
            vec![1.0]
        } else {
            vec![1.0, value]
        },
    }
}

fn fixture_cell(id: u8, two_dendrites: bool) -> ModelCell {
    let mut dendrites = vec![ModelDendrite {
        id: 1,
        rows: vec![
            fixture_row(0, true, 0.0),
            fixture_row(1, true, 0.0),
            fixture_row(1, true, 0.0),
        ],
    }];
    if two_dendrites {
        dendrites.push(ModelDendrite {
            id: 2,
            rows: vec![
                fixture_row(0, true, 0.0),
                fixture_row(0, true, 0.0),
                fixture_row(1, true, 0.0),
            ],
        });
    }
    let row_count = dendrites.iter().map(|dendrite| dendrite.rows.len()).sum();
    ModelCell {
        id,
        dendrites,
        row_count,
    }
}

fn one_dimensional_combined_reference(
    dendrite: &ModelDendrite,
    beta: &[f64],
    sigma: f64,
    quadrature: &Quadrature,
) -> AppResult<f64> {
    let evaluate = |value: f64| -> AppResult<(f64, f64, f64)> {
        let mut log_value = normal_log_density(value, sigma)?;
        let mut derivative = -value / (sigma * sigma);
        let mut second = -1.0 / (sigma * sigma);
        for row in &dendrite.rows {
            let likelihood = row_likelihood(row.event, dot(beta, &row.x) + value)?;
            log_value += likelihood.log_value;
            derivative += likelihood.score;
            second += likelihood.second;
        }
        Ok((log_value, derivative, second))
    };
    let (mode, scale) = find_concave_mode(&evaluate, "combined_reference")?;
    let log_jacobian = (SQRT_2 * scale).ln();
    let mut terms = Vec::new();
    for (node, weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
        let value = mode + SQRT_2 * scale * node;
        let (log_value, _, _) = evaluate(value)?;
        terms.push(weight.ln() + log_value + node * node + log_jacobian);
    }
    log_sum_exp(&terms)
}

fn brute_force_two_dendrite_log_integral(
    cell: &ModelCell,
    beta: &[f64],
    sigma_u: f64,
    sigma_v: f64,
    quadrature: &Quadrature,
) -> AppResult<f64> {
    if cell.dendrites.len() != 2 {
        return Err("STOP_GH_SELF_TEST:brute_fixture_shape".to_string());
    }
    let mut terms = Vec::new();
    let log_normalizer = -1.5 * PI.ln();
    for (u_node, u_weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
        let u = SQRT_2 * sigma_u * u_node;
        for (v1_node, v1_weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
            let v1 = SQRT_2 * sigma_v * v1_node;
            for (v2_node, v2_weight) in quadrature.nodes.iter().zip(&quadrature.weights) {
                let v2 = SQRT_2 * sigma_v * v2_node;
                let mut log_value =
                    u_weight.ln() + v1_weight.ln() + v2_weight.ln() + log_normalizer;
                for (dendrite, v) in cell.dendrites.iter().zip([v1, v2]) {
                    for row in &dendrite.rows {
                        log_value +=
                            row_likelihood(row.event, dot(beta, &row.x) + u + v)?.log_value;
                    }
                }
                terms.push(log_value);
            }
        }
    }
    log_sum_exp(&terms)
}

fn wrong_rowwise_log_integral(
    cell: &ModelCell,
    beta: &[f64],
    combined_sigma: f64,
    quadrature: &Quadrature,
) -> AppResult<f64> {
    let mut total = 0.0;
    for dendrite in &cell.dendrites {
        for row in &dendrite.rows {
            let single = ModelDendrite {
                id: dendrite.id,
                rows: vec![row.clone()],
            };
            total += one_dimensional_combined_reference(
                &single,
                beta,
                combined_sigma,
                quadrature,
            )?;
        }
    }
    Ok(total)
}

fn self_test_nested_integrals() -> AppResult<(f64, f64, f64, f64)> {
    let q25 = Quadrature::gauss_hermite(25)?;
    let q35 = Quadrature::gauss_hermite(35)?;
    let empty = ModelCell {
        id: 1,
        dendrites: vec![ModelDendrite {
            id: 1,
            rows: Vec::new(),
        }],
        row_count: 0,
    };
    let gaussian_error =
        cell_integral(&empty, &[0.0], 0.8, 0.6, &q25)?.log_likelihood.abs();
    if gaussian_error > SYN_GAUSSIAN_LOG_TOL {
        return Err(format!(
            "STOP_GH_SELF_TEST:gaussian_integral:{gaussian_error:.17e}"
        ));
    }

    let one = fixture_cell(1, false);
    let beta = [-1.1];
    let sigma_u: f64 = 0.55;
    let sigma_v: f64 = 0.35;
    let production =
        cell_integral(&one, &beta, sigma_u, sigma_v, &q35)?.log_likelihood;
    let reference = one_dimensional_combined_reference(
        &one.dendrites[0],
        &beta,
        (sigma_u * sigma_u + sigma_v * sigma_v).sqrt(),
        &q35,
    )?;
    let one_error = (production - reference).abs();
    if one_error > SYN_ONE_DENDRITE_TOL {
        return Err(format!(
            "STOP_GH_SELF_TEST:one_dendrite_nested:{one_error:.17e}"
        ));
    }

    let two = fixture_cell(2, true);
    let production_two =
        cell_integral(&two, &beta, sigma_u, sigma_v, &q25)?.log_likelihood;
    let brute = brute_force_two_dendrite_log_integral(
        &two,
        &beta,
        sigma_u,
        sigma_v,
        &q25,
    )?;
    let two_error = (production_two - brute).abs();
    if two_error > SYN_TWO_DENDRITE_TOL {
        return Err(format!(
            "STOP_GH_SELF_TEST:two_dendrite_nested:{two_error:.17e}"
        ));
    }
    let wrong = wrong_rowwise_log_integral(
        &two,
        &beta,
        (sigma_u * sigma_u + sigma_v * sigma_v).sqrt(),
        &q25,
    )?;
    let wrong_rowwise_separation = (wrong - production_two).abs();
    if wrong_rowwise_separation <= SYN_WRONG_ROWWISE_MIN {
        return Err("STOP_GH_SELF_TEST:rowwise_factorization_not_rejected".to_string());
    }
    Ok((
        gaussian_error,
        one_error,
        two_error,
        wrong_rowwise_separation,
    ))
}

fn gradient_fixture_design() -> FoldDesign {
    let training = vec![fixture_cell(1, true), fixture_cell(2, true)];
    let heldout = fixture_cell(3, true);
    FoldDesign {
        heldout_cell: 3,
        model: ModelKind::V0,
        scaler: Scaler {
            mean: [0.0; 4],
            sd: [1.0; 4],
        },
        training_rowset_sha256: "0".repeat(64),
        training_design_sha256: "3".repeat(64),
        heldout_rowset_sha256: "1".repeat(64),
        design_sha256: "2".repeat(64),
        training_rows: training.iter().map(|cell| cell.row_count).sum(),
        training,
        heldout,
    }
}

fn counted_dendrite(id: u16, event_count: usize) -> ModelDendrite {
    ModelDendrite {
        id,
        rows: (0..4)
            .map(|index| fixture_row((index < event_count) as u8, true, 0.0))
            .collect(),
    }
}

fn counted_cell(id: u8, event_counts: [usize; 2]) -> ModelCell {
    ModelCell {
        id,
        dendrites: vec![
            counted_dendrite(1, event_counts[0]),
            counted_dendrite(2, event_counts[1]),
        ],
        row_count: 8,
    }
}

fn production_fit_fixture_design() -> FoldDesign {
    let training = vec![
        counted_cell(1, [0, 1]),
        counted_cell(2, [1, 2]),
        counted_cell(3, [2, 3]),
        counted_cell(4, [3, 4]),
    ];
    FoldDesign {
        heldout_cell: 5,
        model: ModelKind::V0,
        scaler: Scaler {
            mean: [0.0; 4],
            sd: [1.0; 4],
        },
        training_rowset_sha256: sha256_hex(b"synthetic-train"),
        training_design_sha256: sha256_hex(b"synthetic-training-design"),
        heldout_rowset_sha256: sha256_hex(b"synthetic-heldout"),
        design_sha256: sha256_hex(b"synthetic-v0-nested-design"),
        training_rows: training.iter().map(|cell| cell.row_count).sum(),
        training,
        heldout: counted_cell(5, [1, 3]),
    }
}

fn five_point_objective_derivative(
    design: &FoldDesign,
    face: VarianceFace,
    parameters: &[f64],
    column: usize,
    quadrature: &Quadrature,
) -> AppResult<f64> {
    let step = 2.0e-4 * (1.0 + parameters[column].abs());
    let mut values = Vec::new();
    for multiplier in [-2.0, -1.0, 1.0, 2.0] {
        let mut shifted = parameters.to_vec();
        shifted[column] += multiplier * step;
        values.push(evaluate_training(design, face, &shifted, quadrature)?.objective);
    }
    Ok((values[0] - 8.0 * values[1] + 8.0 * values[2] - values[3])
        / (12.0 * step))
}

fn self_test_training_gradient() -> AppResult<f64> {
    let design = gradient_fixture_design();
    let quadrature = Quadrature::gauss_hermite(35)?;
    let parameters = vec![-1.0, 0.45f64.ln(), 0.30f64.ln()];
    let evaluation =
        evaluate_training(&design, VarianceFace::Both, &parameters, &quadrature)?;
    let mut maximum = 0.0f64;
    for column in 0..parameters.len() {
        let finite = five_point_objective_derivative(
            &design,
            VarianceFace::Both,
            &parameters,
            column,
            &quadrature,
        )?;
        maximum = maximum.max(scaled_error(finite, evaluation.gradient[column]));
    }
    if maximum > SYN_GRADIENT_SCALED_TOL {
        return Err(format!(
            "STOP_GH_SELF_TEST:training_gradient:{maximum:.17e}"
        ));
    }
    Ok(maximum)
}

fn self_test_optimizer_and_hessian() -> AppResult<(f64, f64, f64)> {
    let target = [1.25, -0.75];
    let bounds = [(-5.0, 5.0), (-5.0, 5.0)];
    let mut solutions = Vec::new();
    for start in [[-4.0, 4.0], [4.0, -4.0], [0.0, 0.0], [2.0, 2.0]] {
        solutions.push(bounded_bfgs(&start, &bounds, |parameters| {
            let residual = [parameters[0] - target[0], parameters[1] - target[1]];
            Ok(Eval {
                objective: 0.5 * residual[0] * residual[0] + residual[1] * residual[1],
                gradient: vec![residual[0], 2.0 * residual[1]],
                log_likelihood: -(0.5 * residual[0] * residual[0]
                    + residual[1] * residual[1]),
            })
        })?);
    }
    let maximum = solutions
        .iter()
        .flat_map(|solution| {
            solution
                .parameters
                .iter()
                .zip(target)
                .map(|(observed, expected)| (observed - expected).abs())
        })
        .fold(0.0, f64::max);
    let objective_spread = solutions
        .iter()
        .map(|solution| solution.objective)
        .fold(f64::NEG_INFINITY, f64::max)
        - solutions
            .iter()
            .map(|solution| solution.objective)
            .fold(f64::INFINITY, f64::min);
    if maximum > SYN_OPTIMIZER_PARAMETER_TOL
        || objective_spread > SYN_OPTIMIZER_SPREAD_TOL
    {
        return Err(format!(
            "STOP_GH_SELF_TEST:optimizer:{maximum:.17e}:{objective_spread:.17e}"
        ));
    }
    let (eigenvalues, _) = jacobi_eigen(vec![vec![2.0, 0.5], vec![0.5, 1.0]])?;
    let mut eigenvalues = eigenvalues;
    eigenvalues.sort_by(f64::total_cmp);
    let expected = [(3.0 - 2.0f64.sqrt()) / 2.0, (3.0 + 2.0f64.sqrt()) / 2.0];
    let hessian_eigen_max_error = (eigenvalues[0] - expected[0])
        .abs()
        .max((eigenvalues[1] - expected[1]).abs());
    if hessian_eigen_max_error > SYN_HESSIAN_EIGEN_TOL {
        return Err("STOP_GH_SELF_TEST:hessian_eigen_oracle".to_string());
    }
    Ok((maximum, objective_spread, hessian_eigen_max_error))
}

fn synthetic_observation_dataset() -> Dataset {
    let mut rows = Vec::new();
    let replicates = [1u8, 1, 1, 1, 2, 2, 2, 3];
    for cell in 1u8..=8 {
        let x = cell as f64 / 8.0;
        for age_bin in 0u8..=3 {
            for event in 0u8..=1 {
                for replicate in 0..replicates[(cell - 1) as usize] {
                    let protrusion = 100_000 * cell as u32
                        + 1_000 * age_bin as u32
                        + 100 * event as u32
                        + replicate as u32
                        + 1;
                    rows.push(Observation {
                        key: EntityKey {
                            cell,
                            dendrite: 1 + ((age_bin + replicate) % 2) as u16,
                            protrusion,
                        },
                        session: age_bin + 2,
                        age_bin,
                        event,
                        log_intensity: x,
                        shape: x.powi(2),
                        log_distance: 0.5 + x.powi(3),
                        z_offset: x.powi(4),
                    });
                }
            }
        }
    }
    rows.sort_by_key(|row| {
        (
            row.key.cell,
            row.key.dendrite,
            row.key.protrusion,
            row.session,
        )
    });
    Dataset {
        rowset_sha256: observation_rowset_hash(&rows.iter().collect::<Vec<_>>()),
        rows,
    }
}

fn synthetic_aggregation_score(model: ModelKind, heldout_cell: u8) -> f64 {
    let base = 0.40 + 0.001 * heldout_cell as f64;
    match model {
        ModelKind::V0 | ModelKind::V2 => base + 0.03,
        ModelKind::V1 | ModelKind::V1Z => base + 0.01,
    }
}

fn synthetic_face_diagnostics(
    model: ModelKind,
    order: usize,
    objective: f64,
    training_rows: usize,
) -> Vec<FaceDiagnostic> {
    VarianceFace::ALL
        .iter()
        .map(|face| {
            let mut parameters = vec![0.0; model.dimension()];
            parameters.extend(std::iter::repeat(0.3f64.ln()).take(face.active_count()));
            let gradient = vec![0.0; parameters.len()];
            FaceDiagnostic {
                face: *face,
                order,
                parameters,
                objective,
                log_likelihood: -objective * training_rows as f64,
                converged_starts: 4,
                best_three_spread: 0.0,
                iterations: 1,
                evaluations: 1,
                gradient,
                gradient_inf: 0.0,
                projected_gradient_inf: 0.0,
            }
        })
        .collect()
}

fn synthetic_aggregation_fit(
    design: &FoldDesign,
    q15_shift: f64,
    force_renderer_fallback: bool,
) -> AppResult<FoldModelFit> {
    let score = synthetic_aggregation_score(design.model, design.heldout_cell);
    let q15_score = score + q15_shift;
    let parameters = vec![0.0; design.model.dimension()];
    let gradient = vec![0.0; design.model.dimension()];
    let forced_fallback = force_renderer_fallback
        && design.heldout_cell == 5
        && design.model == ModelKind::V0;
    Ok(FoldModelFit {
        heldout_cell: design.heldout_cell,
        model: design.model,
        face_q15: VarianceFace::None,
        face_q25: VarianceFace::None,
        face: VarianceFace::None,
        parameters_q15: parameters.clone(),
        parameters_q25: parameters.clone(),
        parameters_final: parameters,
        train_log_likelihood_q15: -q15_score * design.training_rows as f64,
        train_log_likelihood_q25: -score * design.training_rows as f64,
        train_log_likelihood_final: -score * design.training_rows as f64,
        heldout_log_likelihood_q15: -q15_score * design.heldout.row_count as f64,
        heldout_log_likelihood_q25: -score * design.heldout.row_count as f64,
        heldout_log_likelihood_final: -score * design.heldout.row_count as f64,
        heldout_log_likelihood_audit: -score * design.heldout.row_count as f64,
        final_order: if forced_fallback { 35 } else { 25 },
        audit_order: if forced_fallback { 45 } else { 35 },
        q15_converged_starts: 4,
        q25_converged_starts: 4,
        q15_best_three_spread: 0.0,
        q25_best_three_spread: 0.0,
        q15_iterations: 1,
        q25_iterations: 1,
        q15_evaluations: 1,
        q25_evaluations: 1,
        gradient_q25: gradient.clone(),
        gradient_inf_q25: 0.0,
        projected_gradient_inf_q25: 0.0,
        hessian_condition_q25: 1.0,
        parameter_order_delta: 0.0,
        initial_q25_q35_cell_delta: 0.0,
        fallback_parameter_delta: if forced_fallback { Some(0.0) } else { None },
        quadrature_cell_delta: 0.0,
        gradient_final: gradient,
        gradient_inf_final: 0.0,
        projected_gradient_inf_final: 0.0,
        training_rows: design.training_rows,
        heldout_rows: design.heldout.row_count,
        scaler: design.scaler.clone(),
        training_rowset_sha256: design.training_rowset_sha256.clone(),
        training_design_sha256: design.training_design_sha256.clone(),
        heldout_rowset_sha256: design.heldout_rowset_sha256.clone(),
        design_sha256: design.design_sha256.clone(),
        face_diagnostics_q15: synthetic_face_diagnostics(
            design.model,
            15,
            q15_score,
            design.training_rows,
        ),
        face_diagnostics_q25: synthetic_face_diagnostics(
            design.model,
            25,
            score,
            design.training_rows,
        ),
        face_diagnostics_fallback: if forced_fallback {
            synthetic_face_diagnostics(design.model, 35, score, design.training_rows)
        } else {
            Vec::new()
        },
    })
}

fn self_test_fit_dataset_32_fold_aggregation() -> AppResult<LocoSelfTestFixture> {
    let dataset = synthetic_observation_dataset();
    let mut calls = 0usize;
    let report = fit_dataset_with_fitter(&dataset, false, |design| {
        calls += 1;
        synthetic_aggregation_fit(design, 2.0e-6, false)
    })?;
    let expected_cell_rows = [8usize, 8, 8, 8, 16, 16, 16, 24];
    if calls != 32
        || report.folds.len() != 32
        || report.comparison_rows != 104
        || report.cell_rows != expected_cell_rows
    {
        return Err("STOP_GH_SELF_TEST:fit_dataset_32_fold_count".to_string());
    }
    for model in ModelKind::ALL {
        let index = model_index(model);
        let mut expected_pooled = 0.0;
        let mut expected_macro = 0.0;
        for cell in 1u8..=8 {
            let score = synthetic_aggregation_score(model, cell);
            expected_pooled += score * expected_cell_rows[(cell - 1) as usize] as f64;
            expected_macro += score;
            if scaled_error(report.per_cell_scores[index][(cell - 1) as usize], score)
                > 1.0e-14
            {
                return Err("STOP_GH_SELF_TEST:fit_dataset_per_cell_score".to_string());
            }
        }
        expected_pooled /= report.comparison_rows as f64;
        expected_macro /= 8.0;
        if scaled_error(report.pooled_scores[index], expected_pooled) > 1.0e-14
            || scaled_error(report.pooled_scores_q25[index], expected_pooled) > 1.0e-14
            || scaled_error(report.macro_scores[index], expected_macro) > 1.0e-14
            || ((report.pooled_scores_q15[index] - report.pooled_scores_q25[index]).abs()
                - 2.0e-6)
                .abs()
                > 1.0e-14
        {
            return Err("STOP_GH_SELF_TEST:fit_dataset_aggregate_score".to_string());
        }
    }
    if report.comparisons.len() != 3
        || report.comparisons[0].decision != "ROBUST_DESCRIPTIVE_GAIN"
        || report.comparisons[1].decision != "DESCRIPTIVE_TIE_OR_MIXED"
        || report.comparisons[2].decision != "ROBUST_DESCRIPTIVE_LOSS"
    {
        return Err("STOP_GH_SELF_TEST:fit_dataset_comparisons".to_string());
    }
    let negative = fit_dataset_with_fitter(&dataset, false, |design| {
        synthetic_aggregation_fit(design, 2.0e-5, false)
    });
    let negative_error = negative
        .err()
        .filter(|error| error.starts_with("STOP_QUADRATURE_NONCONVERGENCE:V0:q15_q25_cv:"))
        .ok_or_else(|| "STOP_GH_SELF_TEST:fit_dataset_global_cv_negative".to_string())?;
    let (negative_expected, negative_observed) = explicit_stop_values(&negative_error)
        .ok_or_else(|| "STOP_GH_SELF_TEST:fit_dataset_global_cv_stop_values".to_string())?;
    let expected_cv_limit = format!("abs_delta<={CV_ORDER_TOL:.17e}");
    if negative_expected != expected_cv_limit {
        return Err("STOP_GH_SELF_TEST:fit_dataset_global_cv_expected".to_string());
    }
    let negative_observed_delta = negative_observed
        .parse::<f64>()
        .map_err(|_| "STOP_GH_SELF_TEST:fit_dataset_global_cv_observed".to_string())?;
    let maximum_delta = ModelKind::ALL
        .iter()
        .map(|model| {
            let index = model_index(*model);
            (report.pooled_scores_q25[index] - report.pooled_scores_q15[index]).abs()
        })
        .fold(0.0, f64::max);
    let forced_report = fit_dataset_with_fitter(&dataset, false, |design| {
        synthetic_aggregation_fit(design, 2.0e-6, true)
    })?;
    if forced_report
        .folds
        .iter()
        .filter(|fold| fold.fallback_parameter_delta.is_some())
        .count()
        != 1
    {
        return Err("STOP_GH_SELF_TEST:forced_renderer_fold_count".to_string());
    }
    Ok(LocoSelfTestFixture {
        natural_report: report,
        forced_report,
        positive_q15_q25_max_delta: maximum_delta,
        negative_q15_q25_observed_delta: negative_observed_delta,
    })
}

fn f64_slice_bits_equal(left: &[f64], right: &[f64]) -> bool {
    left.len() == right.len()
        && left
            .iter()
            .zip(right)
            .all(|(a, b)| a.to_bits() == b.to_bits())
}

fn optimized_bits_equal(left: &Optimized, right: &Optimized) -> bool {
    f64_slice_bits_equal(&left.parameters, &right.parameters)
        && left.objective.to_bits() == right.objective.to_bits()
        && left.log_likelihood.to_bits() == right.log_likelihood.to_bits()
        && f64_slice_bits_equal(&left.gradient, &right.gradient)
        && left.gradient_inf.to_bits() == right.gradient_inf.to_bits()
        && left.projected_gradient_inf.to_bits()
            == right.projected_gradient_inf.to_bits()
        && left.iterations == right.iterations
        && left.evaluations == right.evaluations
}

fn face_fit_bits_equal(left: &FaceFit, right: &FaceFit) -> bool {
    left.face == right.face
        && left.order == right.order
        && left.converged_starts == right.converged_starts
        && left.best_three_spread.to_bits() == right.best_three_spread.to_bits()
        && optimized_bits_equal(&left.optimum, &right.optimum)
        && left.solutions.len() == right.solutions.len()
        && left
            .solutions
            .iter()
            .zip(&right.solutions)
            .all(|(a, b)| optimized_bits_equal(a, b))
}

fn reevaluated_fit_gradient(
    design: &FoldDesign,
    fit: &FaceFit,
    quadrature: &Quadrature,
) -> AppResult<Vec<f64>> {
    Ok(evaluate_training(
        design,
        fit.face,
        &fit.optimum.parameters,
        quadrature,
    )?
    .gradient)
}

fn audit_face_diagnostic_gradient(
    design: &FoldDesign,
    diagnostic: &FaceDiagnostic,
    quadrature: &Quadrature,
) -> AppResult<(f64, f64)> {
    let evaluation = evaluate_training(
        design,
        diagnostic.face,
        &diagnostic.parameters,
        quadrature,
    )?;
    let bounds = parameter_bounds(design.model, diagnostic.face);
    let projected = projected_gradient(&diagnostic.parameters, &evaluation.gradient, &bounds);
    let raw_inf = inf_norm(&evaluation.gradient);
    let projected_inf = inf_norm(&projected);
    if !f64_slice_bits_equal(&evaluation.gradient, &diagnostic.gradient)
        || raw_inf.to_bits() != diagnostic.gradient_inf.to_bits()
        || projected_inf.to_bits() != diagnostic.projected_gradient_inf.to_bits()
    {
        return Err("STOP_GH_SELF_TEST:diagnostic_gradient_re_evaluation".to_string());
    }
    Ok((raw_inf, projected_inf))
}

fn self_test_leakage() -> AppResult<()> {
    let original = synthetic_observation_dataset();
    let first = build_fold_design(&original, 4, ModelKind::V2, false)?;
    let mut poisoned = original.clone();
    for row in poisoned.rows.iter_mut().filter(|row| row.key.cell == 4) {
        row.event = 1 - row.event;
        row.log_intensity += 100.0;
        row.shape -= 20.0;
        row.log_distance += 50.0;
        row.z_offset -= 500.0;
    }
    let second = build_fold_design(&poisoned, 4, ModelKind::V2, false)?;
    if first.training_rowset_sha256 != second.training_rowset_sha256
        || first.training_design_sha256 != second.training_design_sha256
        || first.scaler.mean.map(f64::to_bits) != second.scaler.mean.map(f64::to_bits)
        || first.scaler.sd.map(f64::to_bits) != second.scaler.sd.map(f64::to_bits)
    {
        return Err("STOP_HELDOUT_LEAKAGE:scaler_or_training_hash".to_string());
    }
    let quadrature = Quadrature::gauss_hermite(15)?;
    let parameters = vec![0.0; ModelKind::V2.dimension()];
    let first_eval =
        evaluate_training(&first, VarianceFace::None, &parameters, &quadrature)?;
    let second_eval =
        evaluate_training(&second, VarianceFace::None, &parameters, &quadrature)?;
    if first_eval.objective.to_bits() != second_eval.objective.to_bits()
        || first_eval
            .gradient
            .iter()
            .map(|value| value.to_bits())
            .collect::<Vec<_>>()
            != second_eval
                .gradient
                .iter()
                .map(|value| value.to_bits())
                .collect::<Vec<_>>()
    {
        return Err("STOP_HELDOUT_LEAKAGE:training_evaluation".to_string());
    }
    let first_fit = fit_face(
        &first,
        VarianceFace::None,
        &quadrature,
        canonical_starts(&first, VarianceFace::None)?,
    )?;
    let second_fit = fit_face(
        &second,
        VarianceFace::None,
        &quadrature,
        canonical_starts(&second, VarianceFace::None)?,
    )?;
    if !face_fit_bits_equal(&first_fit, &second_fit) {
        return Err("STOP_HELDOUT_LEAKAGE:fitted_result".to_string());
    }
    let first_gradient = reevaluated_fit_gradient(&first, &first_fit, &quadrature)?;
    let second_gradient = reevaluated_fit_gradient(&second, &second_fit, &quadrature)?;
    if !f64_slice_bits_equal(&first_gradient, &second_gradient)
        || !f64_slice_bits_equal(&first_gradient, &first_fit.optimum.gradient)
        || !f64_slice_bits_equal(&second_gradient, &second_fit.optimum.gradient)
    {
        return Err("STOP_HELDOUT_LEAKAGE:fitted_gradient_re_evaluation".to_string());
    }
    Ok(())
}

fn self_test_boundaries() -> AppResult<()> {
    let design = gradient_fixture_design();
    let quadrature = Quadrature::gauss_hermite(15)?;
    for (face, parameters) in [
        (VarianceFace::None, vec![-1.0]),
        (VarianceFace::Cell, vec![-1.0, 0.4f64.ln()]),
        (VarianceFace::Dendrite, vec![-1.0, 0.3f64.ln()]),
        (
            VarianceFace::Both,
            vec![-1.0, 0.4f64.ln(), 0.3f64.ln()],
        ),
    ] {
        let evaluation = evaluate_training(&design, face, &parameters, &quadrature)?;
        if !evaluation.objective.is_finite() || evaluation.gradient.iter().any(|x| !x.is_finite())
        {
            return Err("STOP_GH_SELF_TEST:variance_face_evaluation".to_string());
        }
    }
    let make_fit = |face: VarianceFace, objective: f64, parameters: Vec<f64>| FaceFit {
        face,
        order: 15,
        optimum: Optimized {
            gradient: vec![0.0; parameters.len()],
            parameters,
            objective,
            log_likelihood: -objective,
            gradient_inf: 0.0,
            projected_gradient_inf: 0.0,
            iterations: 1,
            evaluations: 1,
        },
        converged_starts: 4,
        best_three_spread: 0.0,
        solutions: Vec::new(),
    };
    let boundary_fits = vec![
        make_fit(VarianceFace::None, 1.0, vec![0.0]),
        make_fit(
            VarianceFace::Cell,
            1.0,
            vec![0.0, SIGMA_LOWER.ln()],
        ),
        make_fit(VarianceFace::Dendrite, 1.1, vec![0.0, 0.2f64.ln()]),
        make_fit(
            VarianceFace::Both,
            1.1,
            vec![0.0, SIGMA_LOWER.ln(), 0.2f64.ln()],
        ),
    ];
    if select_face(&boundary_fits)?.face != VarianceFace::None {
        return Err("STOP_GH_SELF_TEST:lower_boundary_reduction".to_string());
    }
    let positive_fits = vec![
        make_fit(VarianceFace::None, 1.2, vec![0.0]),
        make_fit(VarianceFace::Cell, 1.1, vec![0.0, 0.4f64.ln()]),
        make_fit(
            VarianceFace::Dendrite,
            1.15,
            vec![0.0, 0.3f64.ln()],
        ),
        make_fit(
            VarianceFace::Both,
            1.0,
            vec![0.0, 0.4f64.ln(), 0.3f64.ln()],
        ),
    ];
    if select_face(&positive_fits)?.face != VarianceFace::Both {
        return Err("STOP_GH_SELF_TEST:positive_variance_face".to_string());
    }
    Ok(())
}

fn self_test_production_fit_pipeline(
) -> AppResult<(f64, f64, f64, f64, f64)> {
    let design = production_fit_fixture_design();
    let q15 = Quadrature::gauss_hermite(15)?;
    let q25 = Quadrature::gauss_hermite(25)?;
    let q35 = Quadrature::gauss_hermite(35)?;
    let q45 = Quadrature::gauss_hermite(45)?;
    let ordinary = fit_fold_model(&design, &q15, &q25, &q35, &q45)?;
    if ordinary.final_order != 25
        || ordinary.audit_order != 35
        || ordinary.fallback_parameter_delta.is_some()
        || !ordinary.face_diagnostics_fallback.is_empty()
        || ordinary.initial_q25_q35_cell_delta > CELL_QUADRATURE_TOL
    {
        return Err("STOP_GH_SELF_TEST:production_pipeline_normal_branch".to_string());
    }
    let fit = fit_fold_model_internal(&design, &q15, &q25, &q35, &q45, true)?;
    if fit.face_diagnostics_q15.len() != VarianceFace::ALL.len()
        || fit.face_diagnostics_q25.len() != VarianceFace::ALL.len()
        || fit.face_diagnostics_fallback.len() != VarianceFace::ALL.len()
        || fit.final_order != 35
        || fit.audit_order != 45
        || fit.fallback_parameter_delta.is_none()
    {
        return Err("STOP_GH_SELF_TEST:production_pipeline_coverage".to_string());
    }
    if ordinary.face_q15 != fit.face_q15
        || ordinary.face_q25 != fit.face_q25
        || !f64_slice_bits_equal(&ordinary.parameters_q15, &fit.parameters_q15)
        || !f64_slice_bits_equal(&ordinary.parameters_q25, &fit.parameters_q25)
        || ordinary.initial_q25_q35_cell_delta.to_bits()
            != fit.initial_q25_q35_cell_delta.to_bits()
    {
        return Err("STOP_GH_SELF_TEST:production_pipeline_repeat".to_string());
    }
    if fit.parameter_order_delta > PARAMETER_ORDER_TOL
        || fit.fallback_parameter_delta.unwrap() > PARAMETER_ORDER_TOL
        || fit.quadrature_cell_delta > CELL_QUADRATURE_TOL
        || fit.gradient_inf_final > OPT_GRAD_TOL
        || fit.projected_gradient_inf_final > OPT_INTERNAL_GRAD_TOL
        || ordinary.gradient_inf_final > OPT_GRAD_TOL
        || ordinary.projected_gradient_inf_final > OPT_INTERNAL_GRAD_TOL
    {
        return Err("STOP_GH_SELF_TEST:production_pipeline_gate".to_string());
    }
    let mut raw_gradient_inf = 0.0f64;
    let mut projected_gradient_inf = 0.0f64;
    let mut audit_diagnostics = |
        selected: VarianceFace,
        diagnostics: &[FaceDiagnostic],
        quadrature: &Quadrature,
    | -> AppResult<()> {
        let mut selected_seen = 0usize;
        for diagnostic in diagnostics {
            let (raw, projected) =
                audit_face_diagnostic_gradient(&design, diagnostic, quadrature)?;
            projected_gradient_inf = projected_gradient_inf.max(projected);
            if diagnostic.face == selected {
                selected_seen += 1;
                raw_gradient_inf = raw_gradient_inf.max(raw);
            }
        }
        if selected_seen != 1 {
            return Err("STOP_GH_SELF_TEST:selected_diagnostic_count".to_string());
        }
        Ok(())
    };
    audit_diagnostics(ordinary.face_q15, &ordinary.face_diagnostics_q15, &q15)?;
    audit_diagnostics(ordinary.face_q25, &ordinary.face_diagnostics_q25, &q25)?;
    audit_diagnostics(fit.face_q15, &fit.face_diagnostics_q15, &q15)?;
    audit_diagnostics(fit.face_q25, &fit.face_diagnostics_q25, &q25)?;
    audit_diagnostics(fit.face, &fit.face_diagnostics_fallback, &q35)?;
    Ok((
        ordinary
            .parameter_order_delta
            .max(fit.parameter_order_delta)
            .max(fit.fallback_parameter_delta.unwrap()),
        fit.initial_q25_q35_cell_delta,
        fit.quadrature_cell_delta,
        raw_gradient_inf,
        projected_gradient_inf,
    ))
}

fn self_test_comparison_directions() -> AppResult<()> {
    let gain_pooled = [0.03, 0.0, 0.0, 0.0];
    let gain_macro = [0.03, 0.0, 0.0, 0.0];
    let mut gain_cells = [[0.0; 8]; 4];
    gain_cells[0] = [0.03; 8];
    let gain = make_comparison(
        "SYN_GAIN",
        ModelKind::V0,
        ModelKind::V1,
        &gain_pooled,
        &gain_macro,
        &gain_cells,
    );
    if gain.decision != "ROBUST_DESCRIPTIVE_GAIN"
        || gain.gain_cell_guard_fail
        || gain.gain_pooled_margin_fail
        || gain.gain_macro_margin_fail
        || gain.gain_sign_count_fail
        || gain.loss_cell_guard_fail
        || !gain.loss_pooled_margin_fail
        || !gain.loss_macro_margin_fail
        || !gain.loss_sign_count_fail
    {
        return Err("STOP_GH_SELF_TEST:comparison_gain_vector".to_string());
    }

    let loss_pooled = [0.0, 0.03, 0.0, 0.0];
    let loss_macro = [0.0, 0.03, 0.0, 0.0];
    let mut loss_cells = [[0.0; 8]; 4];
    loss_cells[1] = [0.03; 8];
    let loss = make_comparison(
        "SYN_LOSS",
        ModelKind::V0,
        ModelKind::V1,
        &loss_pooled,
        &loss_macro,
        &loss_cells,
    );
    if loss.decision != "ROBUST_DESCRIPTIVE_LOSS"
        || loss.loss_cell_guard_fail
        || loss.loss_pooled_margin_fail
        || loss.loss_macro_margin_fail
        || loss.loss_sign_count_fail
        || loss.gain_cell_guard_fail
        || !loss.gain_pooled_margin_fail
        || !loss.gain_macro_margin_fail
        || !loss.gain_sign_count_fail
    {
        return Err("STOP_GH_SELF_TEST:comparison_loss_vector".to_string());
    }

    let mixed_macro = [0.0, 0.03, 0.0, 0.0];
    let mixed = make_comparison(
        "SYN_MIXED",
        ModelKind::V0,
        ModelKind::V1,
        &gain_pooled,
        &mixed_macro,
        &gain_cells,
    );
    if mixed.decision != "DESCRIPTIVE_TIE_OR_MIXED"
        || mixed.gain_pooled_margin_fail
        || !mixed.gain_macro_margin_fail
        || !mixed.loss_pooled_margin_fail
        || mixed.loss_macro_margin_fail
    {
        return Err("STOP_GH_SELF_TEST:comparison_mixed_vector".to_string());
    }
    Ok(())
}

fn self_test_permutation_and_schema() -> AppResult<()> {
    let make_raw = |cell: u8, dendrite: u16, protrusion: u32, session: u8| RawRow {
        key: EntityKey {
            cell,
            dendrite,
            protrusion,
        },
        session,
        intensity: 2.0
            + 0.07 * cell as f64
            + 0.03 * dendrite as f64
            + 0.011 * session as f64
            + 0.001 * (protrusion % 11) as f64,
        lambda1: 2.2 + 0.02 * cell as f64 + 0.01 * session as f64,
        lambda2: 1.0 + 0.015 * dendrite as f64 + 0.002 * (protrusion % 7) as f64,
        distance: 3.0
            + 0.04 * cell as f64
            + 0.025 * dendrite as f64
            + 0.006 * session as f64,
        z_offset: -0.3
            + 0.08 * cell as f64
            - 0.025 * dendrite as f64
            + 0.009 * session as f64
            + 0.001 * (protrusion % 5) as f64,
    };
    let mut ordered = Vec::new();
    for cell in 1u8..=4 {
        for terminal_age in 0u8..=3 {
            let dendrite = 1 + terminal_age as u16 % 2;
            let protrusion = 100 * cell as u32 + terminal_age as u32 + 1;
            for age in 0u8..=terminal_age {
                ordered.push(make_raw(cell, dendrite, protrusion, age + 2));
            }
        }
        let survivor = 100 * cell as u32 + 9;
        for session in 2u8..=6 {
            ordered.push(make_raw(cell, 2, survivor, session));
        }
    }
    let first = build_dataset(&ordered, false)?;
    let mut permuted = ordered.clone();
    permuted.reverse();
    let second = build_dataset(&permuted, false)?;
    if first.rowset_sha256 != second.rowset_sha256
        || first.rows.len() != second.rows.len()
        || first
            .rows
            .iter()
            .map(|row| (row.key, row.session, row.event))
            .collect::<Vec<_>>()
            != second
                .rows
                .iter()
                .map(|row| (row.key, row.session, row.event))
                .collect::<Vec<_>>()
    {
        return Err("STOP_GH_SELF_TEST:canonical_permutation".to_string());
    }
    let first_design = build_fold_design(&first, 4, ModelKind::V0, false)?;
    let second_design = build_fold_design(&second, 4, ModelKind::V0, false)?;
    if first_design.training_rowset_sha256 != second_design.training_rowset_sha256
        || first_design.training_design_sha256 != second_design.training_design_sha256
        || first_design.design_sha256 != second_design.design_sha256
        || first_design.scaler.mean.map(f64::to_bits)
            != second_design.scaler.mean.map(f64::to_bits)
        || first_design.scaler.sd.map(f64::to_bits)
            != second_design.scaler.sd.map(f64::to_bits)
    {
        return Err("STOP_GH_SELF_TEST:canonical_design_permutation".to_string());
    }
    let quadrature = Quadrature::gauss_hermite(15)?;
    let first_fit = fit_face(
        &first_design,
        VarianceFace::None,
        &quadrature,
        canonical_starts(&first_design, VarianceFace::None)?,
    )?;
    let second_fit = fit_face(
        &second_design,
        VarianceFace::None,
        &quadrature,
        canonical_starts(&second_design, VarianceFace::None)?,
    )?;
    if !face_fit_bits_equal(&first_fit, &second_fit) {
        return Err("STOP_GH_SELF_TEST:canonical_fit_permutation".to_string());
    }
    let first_gradient =
        reevaluated_fit_gradient(&first_design, &first_fit, &quadrature)?;
    let second_gradient =
        reevaluated_fit_gradient(&second_design, &second_fit, &quadrature)?;
    if !f64_slice_bits_equal(&first_gradient, &second_gradient)
        || !f64_slice_bits_equal(&first_gradient, &first_fit.optimum.gradient)
        || !f64_slice_bits_equal(&second_gradient, &second_fit.optimum.gradient)
    {
        return Err("STOP_GH_SELF_TEST:canonical_fitted_gradient_re_evaluation".to_string());
    }
    let mut duplicate = ordered;
    duplicate.push(duplicate[0].clone());
    if build_dataset(&duplicate, false).is_ok() {
        return Err("STOP_GH_SELF_TEST:duplicate_not_rejected".to_string());
    }
    Ok(())
}

fn render_json_golden_fixture() -> AppResult<String> {
    Ok(format!(
        "{{\"string\":{},\"zero\":{},\"values\":{}}}\n",
        json_string("a\"b"),
        json_float(-0.0)?,
        json_float_array(&[1.0, -2.5])?
    ))
}

fn numeric_gate_json(
    observed: f64,
    limit: f64,
    comparison: &str,
    pass: bool,
) -> AppResult<String> {
    Ok(format!(
        "{{\"observed\":{},\"limit\":{},\"comparison\":{},\"pass\":{}}}",
        json_float(observed)?,
        json_float(limit)?,
        json_string(comparison),
        pass
    ))
}

fn self_test_metrics_all_pass(metrics: &SelfTestMetrics) -> bool {
    metrics.gh_weight_sum_max_error <= SYN_GH_WEIGHT_SUM_TOL
        && metrics.gh_moment_max_error <= SYN_GH_MOMENT_TOL
        && metrics.gh_symmetry_max_error <= SYN_GH_SYMMETRY_TOL
        && metrics.gaussian_integral_error <= SYN_GAUSSIAN_LOG_TOL
        && metrics.row_score_max_error <= SYN_ROW_DERIVATIVE_TOL
        && metrics.row_second_max_error <= SYN_ROW_DERIVATIVE_TOL
        && metrics.gradient_max_error <= SYN_GRADIENT_SCALED_TOL
        && metrics.mode_max_error <= SYN_MODE_TOL
        && metrics.mode_score_scaled_error <= SYN_MODE_SCORE_SCALED_TOL
        && metrics.mode_curvature_scaled_error <= SYN_MODE_CURVATURE_SCALED_TOL
        && metrics.nested_one_dendrite_error <= SYN_ONE_DENDRITE_TOL
        && metrics.nested_two_dendrite_error <= SYN_TWO_DENDRITE_TOL
        && metrics.wrong_rowwise_separation >= SYN_WRONG_ROWWISE_MIN
        && metrics.optimizer_max_error <= SYN_OPTIMIZER_PARAMETER_TOL
        && metrics.optimizer_objective_spread <= SYN_OPTIMIZER_SPREAD_TOL
        && metrics.hessian_eigen_max_error <= SYN_HESSIAN_EIGEN_TOL
        && metrics.end_to_end_parameter_order_delta <= PARAMETER_ORDER_TOL
        && metrics.end_to_end_initial_q25_q35_cell_delta <= CELL_QUADRATURE_TOL
        && metrics.end_to_end_cell_quadrature_delta <= CELL_QUADRATURE_TOL
        && metrics.end_to_end_gradient_inf <= OPT_GRAD_TOL
        && metrics.end_to_end_projected_gradient_inf <= OPT_INTERNAL_GRAD_TOL
        && metrics.loco_q15_q25_max_delta <= CV_ORDER_TOL
        && metrics.loco_q15_q25_rejection_delta > CV_ORDER_TOL
        && metrics.sha256_known_vectors_pass
        && metrics.strict_lock_negative_cases_pass
        && metrics.authorization_gate_pass
        && metrics.gh_finite_positive_pass
        && metrics.heldout_poison_fit_bitwise_pass
        && metrics.fitted_gradient_vector_bitwise_pass
        && metrics.variance_faces_finite_pass
        && metrics.lower_guard_reduction_pass
        && metrics.comparison_direction_vectors_pass
        && metrics.permutation_fit_bitwise_pass
        && metrics.normal_no_fallback_pipeline_pass
        && metrics.forced_fallback_pass
        && metrics.fit_dataset_32_fold_aggregation_pass
        && metrics.loco_q15_q25_negative_stop_exact_pass
        && metrics.natural_renderer_repeat_and_null_pass
        && metrics.forced_renderer_repeat_and_payload_pass
        && metrics.production_core_renderer_repeat_pass
        && metrics.receipt_determinism_pass
        && metrics.json_golden_pass
        && metrics.real_data_cli_rejection_pass
}

fn render_self_test_evidence(metrics: &SelfTestMetrics) -> AppResult<String> {
    let mut output = String::new();
    output.push('{');
    write!(
        &mut output,
        "\"gradient_semantics\":{},\"numerical_tolerance_profile\":{},\"numeric_gates\":{{",
        json_string("score_quadrature_fisher_louis_not_exact_finite_q_derivative"),
        json_string(EXPECTED_TOLERANCE_PROFILE)
    )
    .unwrap();
    let gates = [
        (
            "gh_weight_sum_max_abs_error",
            metrics.gh_weight_sum_max_error,
            SYN_GH_WEIGHT_SUM_TOL,
            "<=",
            metrics.gh_weight_sum_max_error <= SYN_GH_WEIGHT_SUM_TOL,
        ),
        (
            "gh_moment_max_abs_error",
            metrics.gh_moment_max_error,
            SYN_GH_MOMENT_TOL,
            "<=",
            metrics.gh_moment_max_error <= SYN_GH_MOMENT_TOL,
        ),
        (
            "gh_symmetry_max_abs_error",
            metrics.gh_symmetry_max_error,
            SYN_GH_SYMMETRY_TOL,
            "<=",
            metrics.gh_symmetry_max_error <= SYN_GH_SYMMETRY_TOL,
        ),
        (
            "gaussian_integral_abs_log_error",
            metrics.gaussian_integral_error,
            SYN_GAUSSIAN_LOG_TOL,
            "<=",
            metrics.gaussian_integral_error <= SYN_GAUSSIAN_LOG_TOL,
        ),
        (
            "row_score_max_abs_error",
            metrics.row_score_max_error,
            SYN_ROW_DERIVATIVE_TOL,
            "<=",
            metrics.row_score_max_error <= SYN_ROW_DERIVATIVE_TOL,
        ),
        (
            "row_second_max_abs_error",
            metrics.row_second_max_error,
            SYN_ROW_DERIVATIVE_TOL,
            "<=",
            metrics.row_second_max_error <= SYN_ROW_DERIVATIVE_TOL,
        ),
        (
            "score_quadrature_gradient_max_scaled_error",
            metrics.gradient_max_error,
            SYN_GRADIENT_SCALED_TOL,
            "<=",
            metrics.gradient_max_error <= SYN_GRADIENT_SCALED_TOL,
        ),
        (
            "quadratic_mode_scale_max_abs_error",
            metrics.mode_max_error,
            SYN_MODE_TOL,
            "<=",
            metrics.mode_max_error <= SYN_MODE_TOL,
        ),
        (
            "inner_outer_score_max_scaled_error",
            metrics.mode_score_scaled_error,
            SYN_MODE_SCORE_SCALED_TOL,
            "<=",
            metrics.mode_score_scaled_error <= SYN_MODE_SCORE_SCALED_TOL,
        ),
        (
            "inner_outer_curvature_max_scaled_error",
            metrics.mode_curvature_scaled_error,
            SYN_MODE_CURVATURE_SCALED_TOL,
            "<=",
            metrics.mode_curvature_scaled_error <= SYN_MODE_CURVATURE_SCALED_TOL,
        ),
        (
            "nested_one_dendrite_abs_log_error",
            metrics.nested_one_dendrite_error,
            SYN_ONE_DENDRITE_TOL,
            "<=",
            metrics.nested_one_dendrite_error <= SYN_ONE_DENDRITE_TOL,
        ),
        (
            "nested_two_dendrite_abs_log_error",
            metrics.nested_two_dendrite_error,
            SYN_TWO_DENDRITE_TOL,
            "<=",
            metrics.nested_two_dendrite_error <= SYN_TWO_DENDRITE_TOL,
        ),
        (
            "wrong_rowwise_abs_separation",
            metrics.wrong_rowwise_separation,
            SYN_WRONG_ROWWISE_MIN,
            ">=",
            metrics.wrong_rowwise_separation >= SYN_WRONG_ROWWISE_MIN,
        ),
        (
            "optimizer_parameter_max_abs_error",
            metrics.optimizer_max_error,
            SYN_OPTIMIZER_PARAMETER_TOL,
            "<=",
            metrics.optimizer_max_error <= SYN_OPTIMIZER_PARAMETER_TOL,
        ),
        (
            "optimizer_objective_spread",
            metrics.optimizer_objective_spread,
            SYN_OPTIMIZER_SPREAD_TOL,
            "<=",
            metrics.optimizer_objective_spread <= SYN_OPTIMIZER_SPREAD_TOL,
        ),
        (
            "hessian_eigenvalue_max_abs_error",
            metrics.hessian_eigen_max_error,
            SYN_HESSIAN_EIGEN_TOL,
            "<=",
            metrics.hessian_eigen_max_error <= SYN_HESSIAN_EIGEN_TOL,
        ),
        (
            "end_to_end_parameter_order_delta",
            metrics.end_to_end_parameter_order_delta,
            PARAMETER_ORDER_TOL,
            "<=",
            metrics.end_to_end_parameter_order_delta <= PARAMETER_ORDER_TOL,
        ),
        (
            "end_to_end_initial_q25_q35_cell_delta",
            metrics.end_to_end_initial_q25_q35_cell_delta,
            CELL_QUADRATURE_TOL,
            "<=",
            metrics.end_to_end_initial_q25_q35_cell_delta <= CELL_QUADRATURE_TOL,
        ),
        (
            "end_to_end_final_q35_q45_cell_delta",
            metrics.end_to_end_cell_quadrature_delta,
            CELL_QUADRATURE_TOL,
            "<=",
            metrics.end_to_end_cell_quadrature_delta <= CELL_QUADRATURE_TOL,
        ),
        (
            "end_to_end_score_quadrature_gradient_inf",
            metrics.end_to_end_gradient_inf,
            OPT_GRAD_TOL,
            "<=",
            metrics.end_to_end_gradient_inf <= OPT_GRAD_TOL,
        ),
        (
            "end_to_end_projected_gradient_inf_internal",
            metrics.end_to_end_projected_gradient_inf,
            OPT_INTERNAL_GRAD_TOL,
            "<=",
            metrics.end_to_end_projected_gradient_inf <= OPT_INTERNAL_GRAD_TOL,
        ),
        (
            "loco_q15_q25_max_abs_delta",
            metrics.loco_q15_q25_max_delta,
            CV_ORDER_TOL,
            "<=",
            metrics.loco_q15_q25_max_delta <= CV_ORDER_TOL,
        ),
        (
            "loco_q15_q25_rejection_abs_delta",
            metrics.loco_q15_q25_rejection_delta,
            CV_ORDER_TOL,
            ">",
            metrics.loco_q15_q25_rejection_delta > CV_ORDER_TOL,
        ),
    ];
    for (index, (name, observed, limit, comparison, pass)) in gates.iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        write!(
            &mut output,
            "{}:{}",
            json_string(name),
            numeric_gate_json(*observed, *limit, comparison, *pass)?
        )
        .unwrap();
    }
    output.push_str("},\"exact_gates\":{");
    let exact_gates = [
        ("sha256_known_vectors_pass", metrics.sha256_known_vectors_pass),
        (
            "strict_lock_negative_cases_pass",
            metrics.strict_lock_negative_cases_pass,
        ),
        ("authorization_gate_pass", metrics.authorization_gate_pass),
        ("gh_finite_positive_pass", metrics.gh_finite_positive_pass),
        (
            "heldout_poison_fit_bitwise_pass",
            metrics.heldout_poison_fit_bitwise_pass,
        ),
        (
            "fitted_score_gradient_vector_bitwise_pass",
            metrics.fitted_gradient_vector_bitwise_pass,
        ),
        (
            "variance_faces_finite_pass",
            metrics.variance_faces_finite_pass,
        ),
        (
            "lower_guard_reduction_pass",
            metrics.lower_guard_reduction_pass,
        ),
        (
            "comparison_direction_vectors_pass",
            metrics.comparison_direction_vectors_pass,
        ),
        (
            "row_and_dendrite_permutation_fit_bitwise_pass",
            metrics.permutation_fit_bitwise_pass,
        ),
        (
            "normal_no_fallback_pipeline_pass",
            metrics.normal_no_fallback_pipeline_pass,
        ),
        ("forced_fallback_pipeline_pass", metrics.forced_fallback_pass),
        (
            "fit_dataset_32_fold_aggregation_pass",
            metrics.fit_dataset_32_fold_aggregation_pass,
        ),
        (
            "loco_q15_q25_negative_stop_exact_pass",
            metrics.loco_q15_q25_negative_stop_exact_pass,
        ),
        (
            "natural_renderer_repeat_and_null_pass",
            metrics.natural_renderer_repeat_and_null_pass,
        ),
        (
            "forced_renderer_repeat_and_payload_pass",
            metrics.forced_renderer_repeat_and_payload_pass,
        ),
        (
            "production_core_renderer_repeat_pass",
            metrics.production_core_renderer_repeat_pass,
        ),
        (
            "receipt_repeat_byte_identical_pass",
            metrics.receipt_determinism_pass,
        ),
        (
            "json_golden_byte_identical_pass",
            metrics.json_golden_pass,
        ),
        (
            "real_data_cli_rejection_pass",
            metrics.real_data_cli_rejection_pass,
        ),
    ];
    for (index, (name, pass)) in exact_gates.iter().enumerate() {
        if index > 0 {
            output.push(',');
        }
        write!(&mut output, "{}:{}", json_string(name), pass).unwrap();
    }
    output.push_str("}}");
    Ok(output)
}

fn render_self_test_receipt(metrics: &SelfTestMetrics) -> AppResult<String> {
    if !self_test_metrics_all_pass(metrics) {
        return Err("STOP_GH_SELF_TEST:self_test_metrics_not_all_pass".to_string());
    }
    let mut output = String::new();
    output.push_str("{\n");
    output.push_str("  \"schema_version\":\"ce_npf_loewenstein_2015_v0_v2_self_test_v3\",\n");
    output.push_str("  \"status\":\"PASS\",\n");
    output.push_str("  \"real_data_opened\":false,\n");
    writeln!(
        &mut output,
        "  \"evidence\":{}",
        render_self_test_evidence(metrics)?
    )
    .unwrap();
    output.push_str("}\n");
    Ok(output)
}

fn self_test_receipt() -> AppResult<()> {
    let expected =
        "{\"string\":\"a\\\"b\",\"zero\":0.00000000000000000e0,\"values\":[1.00000000000000000e0,-2.50000000000000000e0]}\n";
    if render_json_golden_fixture()? != expected {
        return Err("STOP_RECEIPT_NONDETERMINISTIC:golden_json".to_string());
    }
    Ok(())
}

fn self_test_production_core_renderer(
    metrics: &SelfTestMetrics,
    self_test_receipt: &str,
    natural_report: FitReport,
    forced_report: FitReport,
) -> AppResult<()> {
    let self_test_sha256 = sha256_hex(self_test_receipt.as_bytes());
    let lock_bytes = synthetic_lock_bytes(true);
    let mut lock = parse_strict_lock(&lock_bytes, Some(&sha256_hex(&lock_bytes)))?;
    lock.values.insert(
        "self_test_core_sha256".to_string(),
        self_test_sha256.clone(),
    );
    let dataset = synthetic_observation_dataset();
    let natural_first = render_core_receipt(
        &dataset,
        &natural_report,
        &lock,
        metrics,
        &self_test_sha256,
    )?;
    let natural_second = render_core_receipt(
        &dataset,
        &natural_report,
        &lock,
        metrics,
        &self_test_sha256,
    )?;
    let diagnostic = &natural_report.folds[0].face_diagnostics_q15[0];
    let normalized_fragment = format!(
        "\"normalized_objective\":{}",
        json_float(diagnostic.objective)?
    );
    if natural_first.as_bytes() != natural_second.as_bytes()
        || natural_first.contains('\r')
        || !natural_first.ends_with('\n')
        || natural_first.ends_with("\n\n")
        || natural_first.matches("\"heldout_cell\":").count() != 32
        || natural_first.contains("\"fallback_used\":true")
        || !natural_first.contains("\"rows\":104,")
        || !natural_first.contains("\"cell_rows\":[8,8,8,8,16,16,16,24]")
        || !natural_first.contains("\"fallback_used\":false")
        || !natural_first.contains(
            "\"fallback_parameter_delta\":null,\"fallback_parameter_pass\":null",
        )
        || !natural_first.contains("\"face_diagnostics_q15\":[{")
        || !natural_first.contains("\"face_diagnostics_q25\":[{")
        || !natural_first.contains("\"face_diagnostics_fallback\":[]")
        || !natural_first.contains("\"score_quadrature_gradient_q25\":[")
        || !natural_first.contains("\"projected_gradient_inf_internal_q25\":")
        || !natural_first.contains(
            "\"q25_final_semantics\":\"record_only_fallback_path_shift\"",
        )
        || natural_first.contains("\"q25_final_limit\":")
        || natural_first.contains("\"q25_final_pass\":")
        || !natural_first.contains(&normalized_fragment)
        || !natural_first.contains("\"gain_gate_vector\":{")
        || !natural_first.contains("\"loss_gate_vector\":{")
        || !natural_first.contains("\"self_test_core_sha256_match\":true")
    {
        return Err("STOP_RECEIPT_NONDETERMINISTIC:natural_core_fixture".to_string());
    }
    let forced_first = render_core_receipt(
        &dataset,
        &forced_report,
        &lock,
        metrics,
        &self_test_sha256,
    )?;
    let forced_second = render_core_receipt(
        &dataset,
        &forced_report,
        &lock,
        metrics,
        &self_test_sha256,
    )?;
    if forced_first.as_bytes() != forced_second.as_bytes()
        || forced_first.matches("\"fallback_used\":true").count() != 1
        || !forced_first.contains("\"face_diagnostics_fallback\":[{")
        || !forced_first.contains("\"projected_gradient_inf_internal_final\":")
        || !forced_first.contains("\"rows\":104,")
        || !forced_first.contains("\"cell_rows\":[8,8,8,8,16,16,16,24]")
    {
        return Err("STOP_RECEIPT_NONDETERMINISTIC:forced_core_fixture".to_string());
    }
    Ok(())
}

fn run_self_test_suite() -> AppResult<(SelfTestMetrics, String)> {
    let (strict_lock_negative_cases_pass, authorization_gate_pass) = self_test_sha_and_lock()?;
    let (gh_weight_sum_max_error, gh_moment_max_error, gh_symmetry_max_error) =
        self_test_quadrature()?;
    let (row_score_max_error, row_second_max_error) = self_test_row_likelihood()?;
    let mode_max_error = self_test_mode()?;
    let (mode_score_scaled_error, mode_curvature_scaled_error) =
        self_test_integral_mode_derivatives()?;
    let (
        gaussian_integral_error,
        nested_one_dendrite_error,
        nested_two_dendrite_error,
        wrong_rowwise_separation,
    ) = self_test_nested_integrals()?;
    let gradient_max_error = self_test_training_gradient()?;
    let (optimizer_max_error, optimizer_objective_spread, hessian_eigen_max_error) =
        self_test_optimizer_and_hessian()?;
    self_test_leakage()?;
    self_test_boundaries()?;
    self_test_permutation_and_schema()?;
    self_test_comparison_directions()?;
    let (
        end_to_end_parameter_order_delta,
        end_to_end_initial_q25_q35_cell_delta,
        end_to_end_cell_quadrature_delta,
        end_to_end_gradient_inf,
        end_to_end_projected_gradient_inf,
    ) = self_test_production_fit_pipeline()?;
    let loco_fixture = self_test_fit_dataset_32_fold_aggregation()?;
    let loco_q15_q25_max_delta = loco_fixture.positive_q15_q25_max_delta;
    let loco_q15_q25_rejection_delta = loco_fixture.negative_q15_q25_observed_delta;
    self_test_receipt()?;
    let forbidden_real_data = vec!["--data".to_string(), "real.csv".to_string()];
    if self_test_output_path(&forbidden_real_data)
        != Err("STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST".to_string())
    {
        return Err("STOP_GH_SELF_TEST:real_data_cli_rejection".to_string());
    }
    let metrics = SelfTestMetrics {
        gh_weight_sum_max_error,
        gh_moment_max_error,
        gh_symmetry_max_error,
        row_score_max_error,
        row_second_max_error,
        mode_max_error,
        mode_score_scaled_error,
        mode_curvature_scaled_error,
        gradient_max_error,
        gaussian_integral_error,
        nested_one_dendrite_error,
        nested_two_dendrite_error,
        wrong_rowwise_separation,
        optimizer_max_error,
        optimizer_objective_spread,
        hessian_eigen_max_error,
        end_to_end_parameter_order_delta,
        end_to_end_initial_q25_q35_cell_delta,
        end_to_end_cell_quadrature_delta,
        end_to_end_gradient_inf,
        end_to_end_projected_gradient_inf,
        loco_q15_q25_max_delta,
        loco_q15_q25_rejection_delta,
        sha256_known_vectors_pass: true,
        strict_lock_negative_cases_pass,
        authorization_gate_pass,
        gh_finite_positive_pass: true,
        heldout_poison_fit_bitwise_pass: true,
        fitted_gradient_vector_bitwise_pass: true,
        variance_faces_finite_pass: true,
        lower_guard_reduction_pass: true,
        comparison_direction_vectors_pass: true,
        permutation_fit_bitwise_pass: true,
        normal_no_fallback_pipeline_pass: true,
        forced_fallback_pass: true,
        fit_dataset_32_fold_aggregation_pass: true,
        loco_q15_q25_negative_stop_exact_pass: true,
        natural_renderer_repeat_and_null_pass: true,
        forced_renderer_repeat_and_payload_pass: true,
        production_core_renderer_repeat_pass: true,
        receipt_determinism_pass: true,
        json_golden_pass: true,
        real_data_cli_rejection_pass: true,
    };
    let receipt = render_self_test_receipt(&metrics)?;
    self_test_production_core_renderer(
        &metrics,
        &receipt,
        loco_fixture.natural_report,
        loco_fixture.forced_report,
    )?;
    if receipt != render_self_test_receipt(&metrics)? {
        return Err("STOP_RECEIPT_NONDETERMINISTIC:repeat".to_string());
    }
    Ok((metrics, receipt))
}

fn parse_option_pairs(args: &[String], allowed: &[&str]) -> AppResult<BTreeMap<String, String>> {
    if args.len() % 2 != 0 {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:cli_pairing".to_string());
    }
    let mut output = BTreeMap::new();
    for pair in args.chunks_exact(2) {
        let key = pair[0].as_str();
        if !allowed.contains(&key) || pair[1].is_empty() {
            return Err(format!("STOP_CONTRACT_SCHEMA_MISMATCH:cli_option:{key}"));
        }
        if output.insert(key.to_string(), pair[1].clone()).is_some() {
            return Err(format!("STOP_CONTRACT_SCHEMA_MISMATCH:cli_duplicate:{key}"));
        }
    }
    Ok(output)
}

fn self_test_output_path(args: &[String]) -> AppResult<Option<PathBuf>> {
    if args
        .iter()
        .any(|argument| argument == "--data" || argument == "--dictionary")
    {
        return Err("STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST".to_string());
    }
    let options = parse_option_pairs(args, &["--core-receipt"])?;
    Ok(options.get("--core-receipt").map(PathBuf::from))
}

fn ensure_output_absent(path: &Path) -> AppResult<()> {
    if path.exists() {
        Err(format!("STOP_OUTPUT_EXISTS:{}", path.display()))
    } else {
        Ok(())
    }
}

fn write_new_file(path: &Path, bytes: &[u8]) -> AppResult<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|error| {
            if path.exists() {
                format!("STOP_OUTPUT_EXISTS:{}", path.display())
            } else {
                format!("STOP_RECEIPT_NONDETERMINISTIC:create:{error}")
            }
        })?;
    file.write_all(bytes)
        .map_err(|error| format!("STOP_RECEIPT_NONDETERMINISTIC:write:{error}"))?;
    file.sync_all()
        .map_err(|error| format!("STOP_RECEIPT_NONDETERMINISTIC:sync:{error}"))
}

fn fit_marker_pending_path(path: &Path) -> PathBuf {
    let mut value = path.as_os_str().to_os_string();
    value.push(".pending");
    PathBuf::from(value)
}

fn commit_fit_start_marker(path: &Path) -> AppResult<()> {
    let pending = fit_marker_pending_path(path);
    ensure_output_absent(path)?;
    ensure_output_absent(&pending)?;
    write_new_file(&pending, FIT_START_MARKER_BYTES)?;
    fs::rename(&pending, path)
        .map_err(|_| "STOP_RECEIPT_NONDETERMINISTIC:fit_marker_commit".to_string())
}

fn explicit_stop_values(error: &str) -> Option<(&str, &str)> {
    const EXPECTED: &str = ":expected=";
    const OBSERVED: &str = ":observed=";
    let expected_start = error.find(EXPECTED)? + EXPECTED.len();
    let observed_marker = error.rfind(OBSERVED)?;
    if observed_marker < expected_start {
        return None;
    }
    Some((
        &error[expected_start..observed_marker],
        &error[observed_marker + OBSERVED.len()..],
    ))
}

fn render_stop_receipt(error: &str, fit_started: bool) -> String {
    let stop_code = error.split(':').next().unwrap_or("STOP_UNKNOWN");
    let (expected, observed) = if stop_code == "STOP_REAL_DATA_NOT_AUTHORIZED" {
        (
            "real_data_fit_authorized=true",
            "real_data_fit_authorized=false",
        )
    } else if let Some(values) = explicit_stop_values(error) {
        values
    } else {
        ("all_locked_gates_pass", stop_code)
    };
    format!(
        "{{\n  \"schema_version\":\"ce_npf_loewenstein_2015_v0_v2_stop_receipt_v1\",\n  \"stop_code\":{},\n  \"expected\":{},\n  \"observed\":{},\n  \"fit_started\":{}\n}}\n",
        json_string(stop_code),
        json_string(expected),
        json_string(observed),
        fit_started
    )
}

fn run_self_test_mode(args: &[String]) -> AppResult<String> {
    let output_path = self_test_output_path(args)?;
    if let Some(path) = &output_path {
        ensure_output_absent(path)?;
    }
    let (_, receipt) = run_self_test_suite()?;
    if let Some(path) = output_path {
        write_new_file(&path, receipt.as_bytes())?;
    }
    Ok(format!(
        "SELF_TEST_PASS core_sha256={}",
        sha256_hex(receipt.as_bytes())
    ))
}

fn run_fit_mode(args: &[String]) -> AppResult<String> {
    let allowed = [
        "--data",
        "--dictionary",
        "--execution-lock",
        "--expected-lock-sha256",
        "--core-receipt",
        "--fit-started-marker",
    ];
    let options = parse_option_pairs(args, &allowed)?;
    if options.len() != allowed.len() {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:fit_cli_required".to_string());
    }
    let data_path = PathBuf::from(
        options
            .get("--data")
            .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:data_path".to_string())?,
    );
    let dictionary_path = PathBuf::from(
        options
            .get("--dictionary")
            .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:dictionary_path".to_string())?,
    );
    let lock_path = PathBuf::from(
        options
            .get("--execution-lock")
            .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:lock_path".to_string())?,
    );
    let expected_lock_sha256 = options
        .get("--expected-lock-sha256")
        .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:lock_sha".to_string())?;
    let output_path = PathBuf::from(
        options
            .get("--core-receipt")
            .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:core_path".to_string())?,
    );
    let fit_started_marker_path = PathBuf::from(
        options
            .get("--fit-started-marker")
            .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:fit_started_marker".to_string())?,
    );
    if output_path == fit_started_marker_path {
        return Err("STOP_CONTRACT_SCHEMA_MISMATCH:fit_marker_alias".to_string());
    }
    ensure_output_absent(&output_path)?;
    ensure_output_absent(&fit_started_marker_path)?;
    let mut fit_started = false;
    let result = (|| -> AppResult<String> {
        let lock_bytes = fs::read(&lock_path)
            .map_err(|error| format!("STOP_EXECUTION_CONTRACT_HASH_MISMATCH:read:{error}"))?;
        let lock = parse_strict_lock(&lock_bytes, Some(expected_lock_sha256))?;
        validate_execution_lock(&lock, true)?;
        let (self_test_metrics, self_test_receipt) = run_self_test_suite()?;
        let observed_self_test_sha256 = sha256_hex(self_test_receipt.as_bytes());
        let expected_self_test_sha256 = lock.value("self_test_core_sha256")?;
        if observed_self_test_sha256 != expected_self_test_sha256 {
            return Err(format!(
                "STOP_SELF_TEST_CORE_HASH_MISMATCH:expected={expected_self_test_sha256}:observed={observed_self_test_sha256}"
            ));
        }
        let dictionary_bytes = fs::read(&dictionary_path)
            .map_err(|error| format!("STOP_SOURCE_CONTENT_MISMATCH:dictionary_read:{error}"))?;
        if dictionary_bytes.len() != EXPECTED_DICTIONARY_BYTES
            || sha256_hex(&dictionary_bytes) != EXPECTED_DICTIONARY_SHA256
        {
            return Err("STOP_SOURCE_CONTENT_MISMATCH:dictionary".to_string());
        }
        let data_bytes = fs::read(&data_path)
            .map_err(|error| format!("STOP_SOURCE_CONTENT_MISMATCH:read:{error}"))?;
        let raw_rows = parse_raw_rows(&data_bytes, true)?;
        let dataset = build_dataset(&raw_rows, true)?;
        commit_fit_start_marker(&fit_started_marker_path)?;
        fit_started = true;
        let report = fit_dataset(&dataset)?;
        let receipt = render_core_receipt(
            &dataset,
            &report,
            &lock,
            &self_test_metrics,
            &observed_self_test_sha256,
        )?;
        write_new_file(&output_path, receipt.as_bytes())?;
        Ok(format!(
            "FIT_PASS core_sha256={}",
            sha256_hex(receipt.as_bytes())
        ))
    })();
    match result {
        Ok(message) => Ok(message),
        Err(error) => {
            if !output_path.exists() {
                let stop_receipt = render_stop_receipt(&error, fit_started);
                write_new_file(&output_path, stop_receipt.as_bytes())?;
            }
            Err(error)
        }
    }
}

fn run_cli(arguments: &[String]) -> AppResult<String> {
    let (mode, remaining) = arguments
        .split_first()
        .ok_or_else(|| "STOP_CONTRACT_SCHEMA_MISMATCH:missing_mode".to_string())?;
    match mode.as_str() {
        "--self-test" => run_self_test_mode(remaining),
        "--fit" => run_fit_mode(remaining),
        _ => Err(format!("STOP_CONTRACT_SCHEMA_MISMATCH:mode:{mode}")),
    }
}

fn main() {
    let arguments = env::args().skip(1).collect::<Vec<_>>();
    match run_cli(&arguments) {
        Ok(message) => println!("{message}"),
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha_and_strict_lock() {
        self_test_sha_and_lock().unwrap();
        let forbidden = vec!["--data".to_string(), "real.csv".to_string()];
        assert_eq!(
            self_test_output_path(&forbidden).unwrap_err(),
            "STOP_REAL_DATA_FORBIDDEN_IN_SELF_TEST"
        );
    }

    #[test]
    fn quadrature_nodes_weights_and_moments() {
        self_test_quadrature().unwrap();
    }

    #[test]
    fn cloglog_derivatives() {
        self_test_row_likelihood().unwrap();
    }

    #[test]
    fn mode_and_integral_derivatives() {
        self_test_mode().unwrap();
        self_test_integral_mode_derivatives().unwrap();
    }

    #[test]
    fn nested_integral_factorization() {
        self_test_nested_integrals().unwrap();
    }

    #[test]
    fn full_training_gradient() {
        self_test_training_gradient().unwrap();
    }

    #[test]
    fn optimizer_and_hessian_oracles() {
        self_test_optimizer_and_hessian().unwrap();
    }

    #[test]
    fn heldout_leakage_is_closed() {
        self_test_leakage().unwrap();
    }

    #[test]
    fn variance_boundaries() {
        self_test_boundaries().unwrap();
    }

    #[test]
    fn production_fit_pipeline_and_forced_fallback() {
        self_test_production_fit_pipeline().unwrap();
    }

    #[test]
    fn permutation_schema_and_receipt_determinism() {
        self_test_permutation_and_schema().unwrap();
        self_test_receipt().unwrap();
    }
}
