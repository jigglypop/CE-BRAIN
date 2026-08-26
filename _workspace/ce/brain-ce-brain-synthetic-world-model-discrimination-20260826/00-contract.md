# CE-BRAIN Stage 0 contract — synthetic structural model discrimination

Status: COMPLETE

Revision: pre-execution revision 1

Mode: outcome-blind synthetic falsification benchmark

CE_RUN: `_workspace/ce/brain-ce-brain-synthetic-world-model-discrimination-20260826`

PREDECESSOR: `_workspace/ce/brain-human-ccep-reference-robust-replication-20260825`

The predecessor ended at `APPARATUS_OR_EVOCATION_STOP`. Its signal outcomes are
not inputs to this benchmark. This run is the manual's logically prior Stage 0
test: can the analysis distinguish broad structure classes before any additional
real-brain geometry claim is attempted?

## 1. Frozen question and claim ceiling

Question: from intervention input, observed state, waveform, spike, delay and
amplitude alone, can fixed candidate procedures recover the generating structure
and predict completely unseen interventions?

This run may establish only synthetic structure-discrimination capability under
the generators below. It cannot establish that a real neuron or brain is
Riemannian, Finsler, graph-like, switching, recurrent, hidden-state, conscious,
or memory-bearing.

## 2. Synthetic worlds

Each world has eight observed nodes, 64 time samples per trajectory, fixed
integration step 0.05, additive Gaussian observation noise SD 0.02, and dynamics
that remain finite on the frozen initial-condition/intervention domain for the
64-sample horizon. This is not a global stability claim for nonlinear World E.
All coefficient matrices and intervention schedules are generated before fitting
from the frozen seed rule.

- **A — Riemannian local dynamics:** symmetric positive-definite local mobility;
  linearized transition is symmetric after the fixed coordinate normalization.
- **B — directed graph:** stable nonsymmetric sparse transition with at least
  four directed edges whose reverse coefficient differs by at least 0.20.
- **C — Finsler-like:** the same state/input location has different transition
  cost for positive and negative input direction; positive/negative input gains
  differ by at least 0.30.
- **D — switching/stratified:** two strongly separated stable transition laws with a state-observable
  regime boundary. Neither single law may explain both regimes.
- **E — recurrent nonlinear operator:** a finite-horizon polynomial recurrence
  containing fixed quadratic state and state/input interactions not representable
  by A--D's linear laws. Its registered-domain trajectories, not arbitrary
  initial states, are subject to the finite-state gate.
- **F — hidden-node system:** eight observed and 24 hidden linear recurrent nodes;
  the first hidden bank forms a fixed observed-to-hidden-to-observed delay path,
  so marginal observed dynamics are non-Markov and require observed history.
- **G — history-dependent network:** next state depends explicitly on two state
  lags with nonzero lag-two norm at least 0.25; the full companion matrix must
  have spectral radius below 0.99.

Linear generator spectral stability and every generator's registered-domain
finite-horizon stability are checked before any model fit. Failure to meet a
stated world identity stops that replicate rather than silently resampling after
model scores are seen.

## 3. Intervention split

For every world and replicate:

- train: 96 trajectories using steps and single pulses, amplitudes
  `{-0.8,-0.4,0.4,0.8}` and all eight input nodes;
- validation: 48 trajectories using ramps and shifted pulses, amplitudes
  `{-0.6,0.6}`;
- completely unseen test: 48 trajectories using chirps and paired pulses,
  amplitudes `{-1.0,-0.3,0.3,1.0}` and unseen pulse intervals.

Candidate selection uses train and validation only. The unseen test is opened
once after the selected class and fitted hyperparameters have been serialized.

## 4. Frozen candidate procedures

All candidates use float64, fixed feature standardization learned on train,
ridge values `10^{-8},10^{-6},10^{-4},10^{-2}` chosen by validation, and no
outcome-specific feature additions.

- **R:** symmetric linear state transition plus signed-linear input.
- **F:** linear state transition plus separate positive and negative input gains.
- **G:** unrestricted directed linear state transition plus signed-linear input.
- **O:** general polynomial/history transition operator with state, two lags,
  input, squared-state and state-input features.
- **S:** two-regime linear transition selected by a frozen threshold search over
  zero and fixed quantiles of the first observed state coordinate; regime laws
  share the same input schema.

The persistence predictor `x[t+1]=x[t]` is a baseline, not a selectable model.
Parameter counts include intercepts and every fitted coefficient. A failed,
nonfinite or unstable rollout receives infinite score.

## 5. Metrics and selection

For candidate `m`, compute normalized one-step and closed-loop rollout RMSE on
validation, each divided by the validation target SD. The frozen selection score
is

`score_m = 0.5 * NRMSE_one_step + 0.5 * NRMSE_rollout + 2*k_m/n_validation_scalar`.

The smallest finite validation score wins; exact ties prefer lower parameter
count and then lexical class order. Test metrics are evaluated only for that
serialized winner. Training reconstruction error is reported but never used as
the primary ranking.

## 6. Seed and replication lock

Root seed is `26082600`. Replicate seeds are derived as the unsigned little-endian
integer from the first 16 bytes of
`SHA256("CE-BRAIN-STAGE0|v1|world|replicate|26082600")`. Replicates are numbered
0--11. No seed may be dropped because of a poor model result.

## 7. Frozen gates

Expected winning classes are `A:R`, `B:G`, `C:F`, `D:S`, `E:O`, `F:O`, `G:O`.
Stage 0 passes only if all conditions hold:

1. each world selects its expected class in at least 10/12 replicates;
2. Worlds A--E have median validation winner margin over the next class at least
   0.001. This absolute score-resolution gate replaces the incompatible draft
   value 0.02 after the pre-execution dimensional/identifiability audit; it is
   frozen before manifest sealing and before unseen outcomes are opened;
3. each world's selected model has median unseen composite NRMSE at most 0.50;
4. each selected model improves unseen composite NRMSE over persistence by at
   least 20% in at least 10/12 replicates;
5. all 84 replicates preserve split identity, finite metrics, deterministic
   serialization and generator identity.

If A--E structure classification fails, Stage 0 stops and no real-data geometry
claim proceeds. Failure only in F/G weakens hidden/history identifiability and
must be reported; it is not relabeled as a geometry success.

## 8. Negative controls and fail-closed rules

- a fixed-prediction, one-step permutation of validation trajectory targets must
  reduce the original winner's advantage to at most 0.02; it is a diagnostic
  negative control and is not the composite model-selection score;
- replacing unseen interventions with train interventions is reported separately
  and cannot satisfy the unseen gate;
- directed/signed/switch/history identity checks are performed from generator
  coefficients, not inferred from fitted outcomes;
- train/validation/test trajectory hashes, selected-model receipt and final metrics are
  written atomically;
- nonfinite values, feature leakage, test-before-selection access, unstable
  rollout, split overlap or hash mismatch stops the run.

## 9. Required preregistration artifacts

Before execution, the run must contain completed `10-data-lock.md`,
`20-hypotheses.md`, `30-models.md`, `40-metrics.md`, `50-gates.md`, and
`60-negative-controls.md`. Their SHA-256 values and the implementation/test
hashes are sealed in `artifacts/stage0-preregistration-manifest.json`. Any later
change invalidates the manifest and requires a new exploratory epoch, never an
in-place threshold change.
