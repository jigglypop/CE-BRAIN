# BA-ERC1-E2 route decision

Status: COMPLETE

## 1. Route comparison

| route | decision | reason and stop boundary |
|---|---|---|
| Conservative FV/RK4 versus shared-node FEM/generalized eigensolver, both against exact star modes | `SELECTED / E2_AUTHORIZED` | Different spatial representations and propagation paths; exact modes prevent two wrong solvers from passing merely by agreeing. |
| Two implementations of the same FV matrix | `REJECTED_AS_CIRCULAR` | Code duplication would not independently test the junction representation. |
| FV matrix exponential versus FEM matrix exponential | `REJECTED_FOR_THIS_GATE` | Different meshes but an unnecessarily shared propagation path weakens fault separation. |
| Full external neuronal simulator with morphology/channel database | `DEFERRED` | Adds software, morphology, and parameter confounds before the passive graph seam is closed. |
| Nonlinear HH and finite-state/history synapse discrimination | `LOCKED_TO_E3` | E2 is passive solver equivalence only. |
| Real electrophysiology | `LOCKED_TO_E5+` | Requires source-locked endpoints, acquisition typing, development/confirmation separation, and a new contract. |
| Loop implies four dimensions; curvature equals consciousness; hippocampus is a literal hash | `PROHIBITED_INFERENCE` | None is entailed by the passive electrical calculation. |

## 2. Selected execution order

1. Freeze 00/10/11/12 and their hashes before verifier creation.
2. Assemble and independently propagate FV and FEM paths on S1/A0/M1 for (N=16,32,64).
3. Compare each path with the exact field before scoring cross-solver agreement.
4. Check refinement, FV strong KCL, FEM continuity/weak residual, energy, spectrum, and pure-mode decay.
5. Run D0 only as the prespecified adverse control; it must fail the correct-star prediction.
6. Emit a fail-closed receipt. Any failed scientific gate is STOP; an undetected D0 or seal mismatch is APPARATUS_INVALID.
7. Audit the stable artifacts independently. Only a fully sealed PASS permits consideration of a separately contracted E3.

## 3. Why the confirmation sector matters

S1 alone has identical values on all branches and zero centre derivative. A disconnected-centre implementation can therefore look correct on S1. A0 forces nonzero branchwise centre derivatives whose weighted sum cancels, and M1 checks simultaneous symmetric and antisymmetric content. They are the junction-sensitive confirmation panels.

## 4. Present authorization

Only E2 synthetic numerical equivalence is authorized. The output label can be at most `E2_CROSSSOLVER_MANUFACTURED_ONLY`; it cannot open a biological, behavioral, consciousness, memory, hippocampal, effective-dimension, or AGI claim.
