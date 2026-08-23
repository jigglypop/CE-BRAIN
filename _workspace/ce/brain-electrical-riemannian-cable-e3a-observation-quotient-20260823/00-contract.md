# BA-ERC1-E3a contract — observation-quotient identifiability

Status: COMPLETE

Mode: light successor; analytic/synthetic measurement screen only.

PREDECESSOR: `_workspace/ce/brain-electrical-riemannian-cable-e2-crosssolver-20260823`

CE_RUN: `_workspace/ce/brain-electrical-riemannian-cable-e3a-observation-quotient-20260823`

## 1. Question and scope

Can branch-resolved voltage observations distinguish the passive Y-cable's antisymmetric sector from even an oracle scalar point-neuron predictor, and does branch averaging erase exactly that distinction? E3a is a 0.5%-budget measurement-identifiability screen before any history-synapse comparison.

This is not a biological fit. It uses no recording, noise tuning, morphology fit, intervention, effective-dimension estimator, consciousness variable, hippocampal mechanism, or AGI endpoint.

## 2. Frozen apparatus

Sample the inherited exact S1, A0, and M1 fields at the same dimensionless arclength $s_0=0.6$ on all three edges and at 41 equally spaced times in $[0,0.2]$. Let $Y\in\mathbb R^{3\times41}$ collect branch voltages. The strongest branch-shared point-neuron oracle is allowed to choose a new scalar value independently at every time:

$$
\Pi=\frac13\mathbf 1\mathbf 1^T,\qquad
Y_{\rm point}=\Pi Y.
$$

Its unresolved energy fraction and relative error are

$$
\eta_\perp=\frac{\|(I-\Pi)Y\|_F^2}{\|Y\|_F^2},
\qquad R_{\rm point}=\sqrt{\eta_\perp}.
$$

The branch-mean observation is $\bar Y=\mathbf1^TY/3$. All quantities are dimensionless after the E2 scaling.

Frozen gates: projector symmetry/idempotence errors and $\|\Pi\mathbf1-\mathbf1\|_2$ are each at most $10^{-14}$; S1 $\eta_\perp\le10^{-24}$; A0 $\eta_\perp\ge1-10^{-12}$; M1 $\eta_\perp\ge0.2$; and collapsed A0 maximum absolute mean is at most $10^{-15}$. Every output must be finite. No threshold, sensor, time, panel, or projection may change after execution.

## 3. Required brain-research fields

`BIO_STARTING_MECHANISM`: The inherited passive Y-cable has a symmetric sector and branch-antisymmetric voltage sectors under continuity and Kirchhoff coupling. A scalar point neuron has only the branch-shared observation subspace.

`CE_DELTA`: None. E3a tests only whether the observation map preserves or quotients out a known cable mode.

`MEASUREMENT_MODEL`: Three noiseless, identically typed voltage sensors at equal arclength with a shared clock. The resolved map returns all three voltages; the collapsed map returns their arithmetic mean. Sensor-specific gains, offsets, and time warps are prohibited.

`DATA_PROVENANCE`: Deterministic exact S1/A0/M1 fields inherited from E2 formulas only. `real_endpoint_opened=false`, `behavior_loaded=false`, and `model_fit=false`.

`DATA_SPLIT`: S1 is the symmetric negative control; A0 is the sealed antisymmetric confirmation; M1 is the sealed mixed confirmation; the branch mean is the prespecified quotient/no-go control. There is no fitting split because the point oracle is solved analytically at each time.

`OBSERVABLES`: Projector algebra errors, rank, $\eta_\perp$, oracle point relative error, branch-mean amplitude, exact analytic identities, hashes, and prohibited-promotion flags.

`RESIDUAL_RULE`: Use the frozen thresholds in section 2. Cross-model advantage is not scored by an unstable ratio against zero cable error; the projection residual itself is the sufficient statistic.

`FALSIFIER`: Non-projector algebra, nonzero S1 rejection, failure to resolve A0, M1 unresolved energy below 0.2, or survival of A0 under the collapsed mean kills this measurement design before E3b.

`MATCHED_CONTROLS`: Same arclength, clock, voltage type, exact equation, and times across S1/A0/M1; full three-branch observation versus its mean quotient; oracle point projection versus exact cable field.

`MODEL_SELECTION`: The point baseline is deliberately stronger than a fitted scalar ODE because it may choose its value at every time. PASS means only that branch-resolved measurement has discriminating information. A mean-only or one-channel real dataset cannot test this seam and must be killed or relabelled before model comparison.

`REVISION_TRIGGER`: One local implementation correction is allowed only with the failed receipt/source preserved and with all formulas, sensors, times, panels, projections, and thresholds unchanged. A failed analytic identity or nondiscriminating observation map ends E3a.

`CLAIM_CEILING`: `SYNTHETIC_BRANCH_OBSERVATION_QUOTIENT_IDENTIFIABILITY / E3A_ANALYTIC_SCREEN_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

## 4. Predecessor evidence

`PREDECESSOR_EVIDENCE`:

| E2 item | SHA-256 | inheritance |
|---|---|---|
| `00-contract.md` | `090873c753c3c69b2360435a2989de62092ccd63bc1f4a56cfcbfa3c24f6477d` | synthetic scope and exact panels |
| `10-sources.md` | `ca6b7e4fb3b42d2a5f0ef6703982aee3c47b49517bd3d43fafd6c9d9811bb506` | source boundary only |
| `11-math.md` | `974b1dbc0f4441985140c55d8f9ffc07fe21662b7e44a3f5bcbe54be0c6e5c95` | symmetric/antisymmetric mode formulas |
| `12-routes.md` | `dc2f9ab90b3b06c9d910c61f45d54ddd5d5164b6740e5ef4d159d4140d63929e` | E3 remains separately contractable |
| `20-audit.md` | `2e64fe533dba988363346f2425d22d1601b3897ccb39676170c5a501d0e8f0d3` | final E2 claim boundary |
| `31-validation.md` | `e49e321350e43e37313f89eb2c26843991798e881f55bcb9d63a4b2953f73a32` | E2 numerical results only |
| `40-final-report.md` | `836d429b5ce899d4b4149b81a05e8ba1108f9abaa2b9cf0630117a5dfad1b6cb` | final narrative boundary |
| `artifacts/verify_passive_y_crosssolver_e2.py` | `a32c833acf740ca9c28764d50230807e391adf247f6790ca593ec183bcbdbb46` | implementation evidence, not imported |
| `artifacts/e2-receipt.json` | `badb1ec5246976b723a257aec4ffb16be1d1e015bb6ebe38afe509b34024ded6` | `E2_CROSSSOLVER_MANUFACTURED_ONLY` PASS |

## 5. Outcomes

- `PASS`: all analytic/measurement gates pass; claim status `E3A_OBSERVATION_QUOTIENT_SYNTHETIC_ONLY`.
- `STOP`: a substantive identifiability gate fails; E3b remains locked.
- `APPARATUS_INVALID`: a seal, projector, finite-value, or no-go-control gate fails.

All outcomes keep biological, real-data, behavior, model-fit, consciousness, hippocampal, AGI, and downstream-authorization flags false.
