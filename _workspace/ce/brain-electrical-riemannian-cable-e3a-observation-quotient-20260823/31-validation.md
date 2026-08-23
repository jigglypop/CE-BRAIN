# BA-ERC1-E3a validation

Status: COMPLETE

Verdict: PASS — specified synthetic branch-observation quotient only.

The sealed receipt is `artifacts/e3a-receipt.json`, SHA-256 `4ad4d72e6136d9849fd1f6265c85decd2263ac6090107d878f1da3e1515beb5e`. It reports `E3A_OBSERVATION_QUOTIENT_SYNTHETIC_ONLY`, no failed checks, and matching source, predecessor, preflight, and environment seals.

| panel/control | unresolved fraction $\eta_\perp$ | oracle point relative error | result |
|---|---:|---:|---|
| S1 symmetric | 1.25188e-32 | 1.11887e-16 | correctly indistinguishable from branch-shared point output |
| A0 antisymmetric | 1.0 | 1.0 | fully resolved by three branch channels |
| M1 mixed | 0.353474 | 0.594536 | exceeds frozen unresolved-energy minimum 0.2 |
| A0 after branch mean | maximum absolute value 0 | — | exact quotient/no-go control |

The projector has rank one, zero symmetry and idempotence errors, zero shared-subspace error, and antisymmetric-kernel error 6.64e-18. Every output is finite.

## Interpretation

The per-time point oracle is stronger than a scalar point-neuron ODE: it may choose a new common branch value at every sample. A0 and 35.3% of M1's sampled energy remain outside even that oracle because they lie in branch-contrast directions. Conversely, averaging branches destroys A0 exactly. Therefore a mean-only observation cannot test this cable-versus-point seam, no matter how finely it is sampled in time.

This is chiefly a machine check of a frozen linear-algebra theorem, not empirical model evidence. It is conditional on equal branch weights, equal-arclength identically typed sensors, fixed branch ordering, and no unknown gains/offsets. Weighted, filtered, noisy, missing-channel, or real observations require separate contracts. The result is not a no-go for all neural recording systems.

`CLAIM_CEILING`: `SYNTHETIC_BRANCH_OBSERVATION_QUOTIENT_IDENTIFIABILITY / E3A_ANALYTIC_SCREEN_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

No real data, fitted model, behavior, biological validation, state-dimension estimate, consciousness, memory, hippocampal mechanism, or AGI claim is opened. E3b remains locked until this stable result is independently audited and separately contracted.
