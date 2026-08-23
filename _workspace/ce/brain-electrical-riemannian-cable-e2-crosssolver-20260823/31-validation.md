# BA-ERC1-E2 validation

Status: COMPLETE

Verdict: PASS — E2 cross-solver manufactured-only numerical validation.

## 1. Sealed result

The one-shot receipt is `artifacts/e2-receipt.json`, SHA-256 `badb1ec5246976b723a257aec4ffb16be1d1e015bb6ebe38afe509b34024ded6`. It reports `status=PASS`, `claim_status=E2_CROSSSOLVER_MANUFACTURED_ONLY`, no failed checks, and matching current-source, predecessor, preflight-archive, and environment seals.

Fine-grid ($N=64$) relative errors are:

| panel | FV vs exact | FEM vs exact | FV vs FEM | FV ratio 32/64 | FEM ratio 32/64 |
|---|---:|---:|---:|---:|---:|
| S1 symmetric | 7.92685e-5 | 3.80432e-4 | 4.59876e-4 | 3.99951 | 3.99887 |
| A0 antisymmetric | 4.95440e-6 | 8.02524e-5 | 8.52136e-5 | 3.99979 | 3.99982 |
| M1 mixed | 7.52312e-5 | 3.61866e-4 | 4.37175e-4 | 3.99951 | 3.99888 |

Every fine exact/cross error is below the frozen 1e-3 ceiling. Every exact-error refinement ratio exceeds the frozen minimum 3 and is approximately 4, consistent with second-order spatial convergence.

## 2. Junction, dissipation, and spectral gates

| diagnostic | observed worst case | frozen rule | result |
|---|---:|---:|---|
| FV normalized strong KCL residual | 5.68434e-14 | at most 1e-12 | PASS |
| FEM normalized weak residual | 4.38028e-12 | at most 1e-11 | PASS |
| FEM centre continuity | 0 | exact shared node | PASS |
| maximum sampled relative energy increase | 0 | at most 1e-10 | PASS |
| minimum generalized eigenvalue | -5.64838e-13 | at least -1e-10 | PASS |
| mass Cholesky, all grids | success | required | PASS |

Pure-mode decay relative errors at $N=64$ range from 4.95440e-6 to 3.80432e-4, below the frozen 1e-3 ceiling.

## 3. Adverse-control discrimination

The D0 path independently seals all three centre faces while keeping the A0 initial state and every other coefficient fixed. Its error against the correct coupled-star solution is 0.163843, exceeding the required 0.02 failure signal by a factor of about 8.2. This matters because S1 alone cannot distinguish a correct junction from disconnected equal branches.

## 4. Independent post-run audits

The read-only mathematics audit found no P0. It independently confirmed the exact rates and fields, FV junction stencil, FEM mass/stiffness assembly and eigensolution, refinement computation, energy direction, and D0 failure. It found no hidden fit, panel leakage, threshold change, or circular reuse of an evolution operator.

The read-only status audit independently confirmed the receipt and verifier hashes, all current/predecessor/environment/archive seals, the preserved first STOP chain, zero failed checks, and all false promotion flags.

Two P1 interpretation limits remain explicit:

1. FV KCL is algebraically enforced by the common face value, so it checks implementation of that discrete condition rather than independently proving continuum fidelity. A0 exact convergence and D0 discrimination provide the substantive guard.
2. The FEM weak residual is reconstructed from the same generalized eigenpairs, so it is an algebraic solver-consistency check rather than an independent point-flux measurement. A0 exact convergence is again the external mathematical check.

The solvers are independent discretization and propagation paths, not independent software-team or laboratory replications.

## 5. Preserved negative preflight

Before verifier creation, the first audit stopped on one malformed cosine token in the antisymmetric distal-boundary proof. The exact stopped math and ledger are preserved with hashes `36e133bf59a428c9658ad82ae3adc59c8cce708c30781a143447f2c161909713` and `91e6dc6797780a5b6f6545152c489111b514b613d449d0b42b7df6ac6a06419d`. A single pre-build correction changed only that token and explicit sum rendering; no equation, mode, panel, grid, coefficient, solver, metric, threshold, split, or claim ceiling changed. The CE state records `math-verifier 1/2` and numerical attempt zero.

## 6. Claim boundary

This PASS establishes only that the frozen passive equal-edge Y-cable has matching second-order synthetic predictions under the stated FV/RK4 and FEM/generalized-eigen constructions.

It does not validate biological parameters or morphology; active HH propagation; finite-state versus history synapses; a physical state-space Riemannian metric; effective dimension; real neural data; behavior; consciousness; memory; hippocampal retrieval; or AGI. All receipt flags for those promotions remain false, including `downstream_authorized=false`.

`CLAIM_CEILING`: `PASSIVE_METRIC_GRAPH_CROSSSOLVER_EQUIVALENCE / SYNTHETIC_MANUFACTURED_STIMULI / E2_NUMERICAL_VALIDATION_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

E2 PASS permits consideration of a separately frozen E3 successor. It does not itself authorize E3 execution.
