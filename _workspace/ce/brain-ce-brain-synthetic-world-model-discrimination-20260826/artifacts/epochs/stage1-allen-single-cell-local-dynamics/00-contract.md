# Stage 1 Allen single-cell local dynamics contract

Status: COMPLETE / OUTCOME_BLIND

## Authorization and question

Predecessor authorization is the sealed independent successor
`STATE_RESET_STAGE0_PASS` (manifest
`fd3701d4344ef48754401403cf4b41592f07847e5e95ef3a004ae52996776d65`,
result `3d9beb418c39a54b54e780b06bc1ce4c482b91bb31ffffb0cdc94ce4971cd479`).
The original parent and matched-twin STOP results remain unchanged.

Question: for one Allen Cell Types whole-cell recording, does a fixed recent
history representation improve held-out naturalistic-waveform prediction beyond
the current membrane voltage and injected current alone?

## Required real-brain fields

- `BIO_STARTING_MECHANISM`: a phenomenological discrete current-clamp state
  transition, `V(t+h)=f(V(t),I(t))`, compared with an explicit recent-history
  extension. This is not asserted to be a complete membrane conductance model.
- `CE_DELTA`: none at Stage 1. The tested addition is a registered empirical
  history state, not a CE biological axiom.
- `MEASUREMENT_MODEL`: Allen whole-cell current clamp; the official Allen SDK
  sweep semantics define the valid `index_range`. NWB response voltage (V) and
  stimulus current (A) are converted to mV and pA, then block-averaged from
  200 kHz to 10 kHz. Horizon `h=1 ms` (10 bins).
- `DATA_PROVENANCE`: mouse specimen `320654829`, ephys result `320654827`,
  official well-known file `491201608`, filename `320654827_ephys.nwb`, byte size
  `53,057,893`, server ETag `546d9396f5b40`, last modified 2017-01-24.
- `DATA_SPLIT`: fit on Long Square sweeps 33--54, 56--59 and Ramp sweeps 5--6;
  development on Noise 1 sweeps 60, 62, 64; sealed confirmation on Noise 2
  sweeps 61, 63. No confirmation value may be read before manifest sealing.
- `OBSERVABLES`: per-sweep voltage RMSE in mV, voltage NRMSE using the observed
  sweep standard deviation, spike-event Brier score, event prevalence, and
  model-versus-persistence improvement at a 1 ms horizon.
- `RESIDUAL_RULE`: predictions and residuals are evaluated only where all lagged
  features and the future target exist. Metrics are computed per sweep before
  aggregation; no sample is pooled across split boundaries.
- `FALSIFIER`: unseen Noise 2. History support requires both confirmation sweeps
  to show at least 2% voltage-RMSE improvement over Markov, pooled Brier no worse,
  and neither sweep to degrade Brier by more than 5% relative. Otherwise the
  strong Stage 1 history claim is reduced or marked tension as frozen below.
- `MATCHED_CONTROLS`: voltage persistence, Markov ridge/logistic model, and the
  same preprocessing/samples for the history model.
- `MODEL_SELECTION`: no confirmation selection. The two registered models and
  fixed ridge/logistic procedures are fit on the fit split; Noise 1 is a
  development diagnostic only and cannot change features, horizon or gates.
- `REVISION_TRIGGER`: schema/unit/QC failure stops as apparatus failure. A
  confirmation miss may motivate a new independently locked model family but
  cannot retune this epoch.
- `CLAIM_CEILING`: one-cell public-recording L3 predictive result. No cell-type,
  population, causal mechanism, geometry, memory, consciousness or AGI claim.

## Preprocessing and event definition

The source sampling rate must equal 200,000 Hz and divide exactly by 20. Allen's
SDK `index_range=(a,s)` is inclusive at both ends; convert it to raw half-open
`[a,b)=[a,s+1)`. Define `a'=20 ceil(a/20)` and `b'=20 floor(b/20)`, then

`V_k = mean(v[a'+20k : a'+20(k+1)])`

and identically for current, for `k=0,...,(b'-a')/20-1`. Block means produce
10,000 Hz voltage/current series. Sweep-specific stimulus
onset/duration metadata are receipts, not crop-tuning parameters; the scored
window is the SDK-equivalent valid `index_range`, after the maximum 50 ms history
and before the 1 ms future horizon. Initial test pulses and invalid trailing data
outside `index_range` are excluded by source semantics. Nonfinite samples, unit ambiguity, unequal
response/stimulus lengths or fewer than 100,000 scored bins in any Noise sweep
stop before scientific disposition.

Spikes are upward 0 mV crossings in the downsampled observed voltage. The binary
target at origin `t` is
`y_t=1{exists q in [t,t+9]: V_q<0<=V_(q+1)}`. History features use only crossing
indices `q<t`, so target and history are index-disjoint. Valid scored origins are
exactly `t=500,...,K-11`, where 500 bins is 50 ms and the target is `V_(t+10)`.
This operational
event is a measurement definition, not Allen's feature-extractor spike identity.

## Frozen models

Both models standardize continuous features using fit-split means/scales only.
Voltage uses ridge regression with an unpenalized intercept and fixed standardized
slope penalty `lambda=1e-4`; spike probability uses logistic IRLS with an
unpenalized intercept and L2 slope penalty `1e-4`, at
most 50 iterations and convergence tolerance `1e-8`.

- `M0_MARKOV`: `V_t`, `I_t`.
- `M1_HISTORY`: M0 plus `V` and `I` at 1, 5 and 20 ms lags and observed spike
  counts over the preceding 2, 10 and 50 ms.

Every continuous fit feature must have finite, strictly positive fit-split scale;
no feature may be dropped. An all-zero/all-one fit spike target or nonconvergent
IRLS is `STAGE1_APPARATUS_STOP`.

Fit rows are deterministically thinned to origins satisfying `(t-500) mod 10=0`
to bound memory; evaluation uses every valid bin.

## Frozen decision

- `STAGE1_HISTORY_SUPPORTED`: M1 improves voltage RMSE by at least 2% on each
  Noise 2 sweep; `Brier_M1_pooled <= Brier_M0_pooled`; on each sweep
  `(Brier_M1-Brier_M0)/Brier_M0 <= 0.05`; and `RMSE_M1 < RMSE_persistence` on
  each sweep.
- `STAGE1_MARKOV_SUFFICIENT`: absolute M1 voltage improvement is below 2% on both
  confirmation sweeps and pooled Brier improvement is at most 2% in magnitude.
- `STAGE1_HISTORY_TENSION`: all other finite, valid outcomes.
- `STAGE1_APPARATUS_STOP`: source, schema, unit, split, sample-count, fitting,
  convergence, finite-value or manifest failure.

Only the first status supports a narrow one-cell history-prediction result. None
of the statuses authorizes Stage 2 automatically; Stage 2 requires a separately
audited dataset/protocol contract.
