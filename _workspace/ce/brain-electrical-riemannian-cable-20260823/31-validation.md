# BA-ERC1 L0 validation

Status: COMPLETE

Verdict: PASS -- BA-ERC1 L0 numerical integrity only; five frozen gates U0/K0/P0/N0/H0 passed after one H0-predicate-only apparatus revision; attempt-00 failure preserved; source and environment seals match; no real endpoint, behavior, model fit, biological claim, consciousness claim, or downstream authorization.

## 1. Frozen result

| gate | result | principal diagnostic |
|---|---|---|
| U0 typed units | PASS | Cable left side, weighted axial divergence, and conductance current all have signature $(0,-2,0,1)=\mathrm{A\,m^{-2}}$; every metric term has joule signature $(1,2,-2,0)$; $D_0$ is dimensionless. |
| K0 Kirchhoff/Ohm | PASS | Normalized Y-vertex imbalance $0$; derivative fluxes $(6,-2,-4)$ and physical outward currents $(-6,2,4)$ each sum to zero; the Ohmic current opposes the voltage gradient. |
| P0 passive mode | PASS | Fine relative $L^2$ error $4.685124378672343\times10^{-5}$; coarse/fine error ratio $4.002034508838505$; maximum recorded relative energy change is negative; constant-voltage axial residual $0$. |
| N0 active nonlinearity | PASS | Normalized midpoint residual $0.5369160749968305\gg10^{-4}$; fixed-conductance linear-control residual $0$. |
| H0 causal history | PASS after one local predicate revision | Pre-event and outside-support values $0$; normalization error $2.220446049250313\times10^{-16}$; time-reversed adverse control detected; conductance remains in its closed bounds. |

The final receipt has `source_match=true`, no failed checks, and `claim_status=L0_NUMERICAL_INTEGRITY_ONLY`. Python 3.11.9, NumPy 2.4.6, the selected interpreter path, platform, and disabled bytecode state are recorded inside the receipt.

## 2. Attempt history

Attempt 00 is a negative apparatus result, not deleted evidence. It failed only H0 because a finite-difference proxy was required to be below $10^{-20}$ and floating logistic evaluation at $\pm100$ reached the exact stored bounds. The final receipt names the failed receipt by its exact SHA-256 and labels the revision `H0 numeric predicate only`. The exact attempt source hash is also preserved. No electrical equation, source input, passive solver, branch fixture, active-current observable, data, seed, or endpoint changed.

## 3. Independent post-implementation audit

The read-only math audit found no P0: the SI algebra, cell-centered finite-volume Neumann scheme, analytic cosine mode, explicit stability/energy behavior, Kirchhoff orientation, nonlinear matched control, and causal bump implementation are mathematically consistent. The status audit verified the failed-attempt chain, source hashes, environment seal, five PASS statuses, and all false endpoint/promotion flags. The post-run ledger is `20-audit.md`, SHA-256 `72ba6d2074afdb91c3c7867c4bd9c6abcdf76d285e08e77d4f58ecf7826f7cef`.

## 4. What this result does and does not show

**[Result: numerical integrity]** The frozen equation passed the cheapest internal consistency checks: typed units, signs, branch conservation, passive dissipation/convergence, active-current nonlinearity, and causal smooth-kernel construction.

**[Unfinished]** This does not validate mammalian channel parameters, morphology, spike propagation, a history synapse over a finite-state synapse, a biological state-space metric, effective dimension, consciousness, memory, hippocampal retrieval, or AGI. E2 independent-solver comparison, E3 model discrimination, E4 measurement stress, and every real-data stage remain unrun and locked.

**[Counterexample retained]** A finite sum of exponential synaptic kernels has a finite-dimensional auxiliary-ODE realization. The L0 result therefore does not promote the false statement that every history-dependent synapse is intrinsically infinite-dimensional. The continuum voltage field is the secure source of infinite-dimensionality in the present formalization.
