# BA-ERC1-E3b contract — finite-state versus compact-history synapse

Status: COMPLETE

Mode: full synthetic model-discrimination run; E3b-0 through E3b-2 only.

PREDECESSOR: `_workspace/ce/brain-electrical-riemannian-cable-e3a-observation-quotient-20260823`

CE_RUN: `_workspace/ce/brain-electrical-synaptic-history-e3b-discrimination-20260823`

## 1. Question and hard scope

Can a frozen selection apparatus choose a finite two-state exponential synapse when that family generated the response, yet choose a nonzero compactly supported smooth history kernel when that kernel generated a separate response? The test must reject a time-reversed history control and must show that the fixed exponential dictionary with at most eight states does not reach the preregistered confirmation tolerance on the compact-history panel.

This is a synthetic specificity test for the equation-selection apparatus. It does not infer a biological synaptic kernel, prove that a recorded synapse is infinite dimensional, alter the cable equation, or open consciousness, memory, hippocampal, or AGI claims.

## 2. Frozen linearized synaptic port

All times are normalized by one fixed reference time $T_0$. Write dimensionless time as $\theta=t/T_0$. A presynaptic event train is

$$
u(\theta)=\sum_r A_r\delta(\theta-\theta_r),
$$

where event areas $A_r$ are dimensionless. The scored, dimensionless pre-sigmoid synaptic coordinate is

$$
q(\theta)=\sum_r A_r k(\theta-\theta_r),
\qquad k(a)=0\quad\text{for }a<0.
$$

The electrical port $i_{ij}^{\rm syn}=g_{ij}(V_i-E_{ij})$ remains unchanged. The later bounded link $g=g_{\min}+(g_{\max}-g_{\min})S(b+q)$ is not executed here, so voltage dependence and saturation cannot mask kernel discrimination.

### 2.1 Finite-state family

The nested finite dictionary is

$$
k_M(a)=\sum_{m=1}^{M}w_m\tau_m^{-1}e^{-a/\tau_m}\mathbf1[a\ge0],
\qquad M\in\{1,2,4,8\},
$$

with ordered dimensionless time constants

$$
(0.03,0.12,0.015,0.06,0.24,0.45,0.008,0.75).
$$

Weights are unrestricted real least-squares coefficients. This makes the finite LTI control stronger than a nonnegative-conductance mixture; the fitted coefficients are not interpreted as biological conductances. The negative generator is exactly $M=2$ with weights $(0.65,0.35)$.

### 2.2 Compact-history family

Let $W=0.25$, $r=a/W$, and

$$
\widetilde k_B(a)=
\begin{cases}
\exp[-1/r-2/(1-r)],&0<r<1,\\
0,&\text{otherwise},
\end{cases}
\qquad
Z=\int_0^W\widetilde k_B(a)\,da,
\qquad k_B=\widetilde k_B/Z.
$$

The history candidate has this fixed shape and one fitted scalar gain. Its adverse control is $k_{\rm rev}(a)=k_B(W-a)$ on $0<a<W$, also with one fitted gain. No kernel-shape parameter is fit.

## 3. Frozen stimuli, split, and fitting

Every split uses $\theta=0,0.001,\ldots,2.4$. Events are fixed before execution:

| split | event pairs $(\theta_r,A_r)$ |
|---|---|
| calibration | $(0.08,1.00)$, $(0.14,0.55)$, $(0.31,1.15)$, $(0.57,0.75)$, $(0.94,1.25)$, $(1.29,0.60)$, $(1.52,0.95)$ |
| development | $(0.05,0.80)$, $(0.09,1.10)$, $(0.22,0.45)$, $(0.26,1.20)$, $(0.68,0.90)$, $(0.74,0.65)$, $(1.08,1.30)$, $(1.42,0.70)$, $(1.47,1.00)$ |
| confirmation | $(0.04,1.20)$, $(0.17,0.50)$, $(0.20,0.85)$, $(0.48,1.10)$, $(0.53,0.70)$, $(0.59,1.25)$, $(0.97,0.60)$, $(1.18,1.00)$, $(1.21,0.40)$, $(1.57,1.30)$, $(1.64,0.80)$, $(1.83,0.55)$ |

For each generator, every candidate coefficient is fit once on calibration by SVD least squares on column-normalized design matrices. Development relative $L^2$ error selects the family. Models within $10^{-10}$ of the minimum are tied; ties select fewer coefficients, and equal-size ties select the finite baseline over the history candidate. Confirmation is evaluated once without refitting.

The relative error is $R=\|\widehat q-q\|_2/\|q\|_2$. A dense direct-kernel diagnostic uses 3001 fixed lags on $[0,0.75]$ with the calibration-fit coefficients.

## 4. Frozen execution ladder and gates

| substage | maximum end-to-end budget | gate |
|---|---:|---|
| E3b-0 | 0.25% | dimensions, causality, bump normalization/support, exact-realization theorem, rank/conditioning |
| E3b-1 | 0.50% | finite-$M=2$ negative generator must select `E2`; confirmation $R\le10^{-10}$ |
| E3b-2 | 0.75% | only after E3b-1: bump generator must select `B`; confirmation $R\le10^{-10}$; best finite $M\le8$ confirmation and dense-kernel errors each at least $5\times10^{-3}$; reversed bump confirmation error at least $5\times10^{-2}$ |

Every calibration design must have full column rank. The condition number after column normalization must be at most $10^6$. Bump normalization absolute error must be at most $10^{-10}$; pre-causal and outside-support bump values must be exactly zero; all outputs must be finite. The implementation must use SVD/QR, never normal equations.

If E3b-1 fails, the positive generator and its confirmation panel remain unopened and the run stops. E3b-3 nonlinear Volterra/history terms remain locked regardless of E3b-2 outcome.

## 5. Required brain-research fields

`BIO_STARTING_MECHANISM`: The inherited electrical mechanism is conductance-based synaptic current $i_{ij}^{\rm syn}=g_{ij}(V_i-E_{ij})$. Standard finite sums of exponential synaptic filters have finite-dimensional auxiliary-state realizations. E3b isolates the linearized presynaptic history-to-$q$ port before re-embedding it in voltage dynamics.

`CE_DELTA`: The candidate change is a fixed nonzero compactly supported $C^\infty$ causal kernel in place of the finite exponential auxiliary-state family. It is a model-selection hypothesis, not a new electrical force.

`MEASUREMENT_MODEL`: Direct noiseless sampling of dimensionless $q(\theta)$ on the common 0.001 clock. There is no electrode, clamp, filter, voltage/current unit conversion, unknown gain, or observation noise. This isolates apparatus specificity and is not a real recording model.

`DATA_PROVENANCE`: Formula-generated deterministic event responses only. No external or real neural endpoint is opened. The exact verifier and receipts do not exist at contract freeze.

`DATA_SPLIT`: Coefficients use calibration only; structure selection uses development only; confirmation is read once after selection and never refit. The negative generator is completed first. The positive generator is generated only if the negative selection gate passes.

`OBSERVABLES`: Kernel normalization/support, normalized design ranks/condition numbers, calibration coefficients, development selection, confirmation relative errors, dense-kernel error, reversed-kernel error, source/environment hashes, and open/closed panel flags.

`RESIDUAL_RULE`: The exact thresholds are those in section 4. The $5\times10^{-3}$ finite-family separation is an empirical synthetic falsifier, not a consequence of the analytic no-realization theorem. Non-finite values fail closed.

`FALSIFIER`: Selecting history on the finite negative generator invalidates the apparatus. Failure of the compact bump to beat the fixed $M\le8$ dictionary by the frozen confirmation and dense-kernel margins stops this history route. Failure to detect reversal invalidates temporal orientation. Post-result threshold, time-constant, event, horizon, or model-menu changes are prohibited.

`MATCHED_CONTROLS`: Nested $M=1,2,4,8$ exponential dictionaries, the correctly oriented fixed bump, its time reversal, identical event information and clock, a negative finite generator, and a positive compact-history generator.

`MODEL_SELECTION`: The finite family is preferred on every tie. Only calibration coefficients are free. No time constant, bump support, bump asymmetry, event time, threshold, or split is optimized. A PASS rejects only this fixed finite dictionary under these fixed stimuli; it does not reject arbitrary finite-dimensional nonlinear, delayed, or higher-order models.

`REVISION_TRIGGER`: One local implementation revision is allowed only for a documented code defect that leaves every formula, event, time constant, split, model, norm, threshold, and claim ceiling unchanged. Preserve the failed source and receipt before revision. A substantive selection or separation failure ends this version as STOP.

`CLAIM_CEILING`: `SYNTHETIC_HISTORY_SYNAPSE_OBSERVATION_DISCRIMINATION / E3B_FIXED_MODEL_MENU_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

## 6. Predecessor evidence

`PREDECESSOR_EVIDENCE`:

| item | SHA-256 | status and admissible inheritance |
|---|---|---|
| E3a `00-contract.md` | `daf732762f6418191cbe15671e68baa027578b7b5c59107f4bec7eaeb1478df2` | synthetic scope and successor lock |
| E3a `10-sources.md` | `5ddfe50b64f3378069f0821f5a0eccc604a81054a92a865a6585ac7fc3af3579` | no new empirical source |
| E3a `11-math.md` | `85065c545a582e362efab549b5ae52e4241785238ac5b85cd4b882ebd8e55e15` | finite-observation quotient boundary |
| E3a `12-routes.md` | `35a6d2018164409006edeb46164c1a6b150472710d576a69a3f8ada0fcc366f1` | E3b became separately contractable only |
| E3a `20-audit.md` | `0ed074b4f467c9287841211d9d1be900a1428dcc378de090e3b908be5bb24f74` | final synthetic-only claim ledger |
| E3a `31-validation.md` | `841debb52d1bf6ddd48e532cb3e4ff2da4145994d3dcadd69541e1ad02e59cb8` | observation apparatus PASS only |
| E3a `40-final-report.md` | `d7cff74a1583d74ab5451dfaf5d0e7a82e3c2345a807c643ae8c70fa678295c2` | no biological promotion |
| E3a verifier | `9ef1c2074ca2195f617a934102437e13f260ba39a165a74d1e5d1b7a521900fb` | implementation history, not imported |
| E3a receipt | `4ad4d72e6136d9849fd1f6265c85decd2263ac6090107d878f1da3e1515beb5e` | `E3A_OBSERVATION_QUOTIENT_SYNTHETIC_ONLY` |
| BA-ERC1 `11-math.md` | `a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685` | finite exponential realization counterexample and compact-bump definition |
| BA-ERC1 L0 receipt | `9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501` | H0 causality/support integrity only; not model superiority |
| brain route ledger | `8256c0eb6b48e5c9a83ba061049e5409044a1d90da9cef85f45027daf48c8c51` | BA-SRM3 mixed IC/VC results remain apparatus-invalid; rank-four/consciousness/hash claims remain prohibited |

## 7. Outcome labels

- `PASS`: both generators select their own frozen family, all separation/adverse/seal gates pass, and status is `E3B_FIXED_KERNEL_DISCRIMINATION_SYNTHETIC_ONLY`.
- `STOP`: the finite dictionary approximates the bump inside the kill margin, the bump loses positive selection, or another substantive frozen prediction fails.
- `APPARATUS_INVALID`: the negative generator selects history, conditioning/normalization/seals fail, reversal is not detected, or an unauthorized change occurs.

The receipt must distinguish `synthetic_model_fit=true` from `model_fit=false`, where the latter means no real or biological model fit. All outcomes keep `real_endpoint_opened=false`, `behavior_loaded=false`, `biological_claim=false`, `consciousness_claim=false`, and `downstream_authorized=false`.
