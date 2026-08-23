# BA-ERC1-E2 research contract — passive Y-cable cross-solver test

Status: COMPLETE

Mode: light successor; frozen synthetic E2 verification only.

PREDECESSOR: `_workspace/ce/brain-electrical-riemannian-cable-20260823`

CE_RUN: `_workspace/ce/brain-electrical-riemannian-cable-e2-crosssolver-20260823`

## 1. Question and hard scope

Does the passive metric-graph cable equation already closed at BA-ERC1 L0 give the same sealed Y-branch prediction under two materially different numerical constructions: a conservative cell-centred finite-volume method (FV) and a shared-node linear finite-element generalized-eigen method (FEM)? E2 tests exact symmetric and antisymmetric modes, refinement, junction conditions, energy decay, and one deliberately disconnected-junction adverse control.

This run does not change the electrical equation, introduce a new CE force, use biological recordings, fit parameters, compare synapse models, infer state-space dimension, or support claims about consciousness, memory, hippocampal lookup, or AGI. “Independent solver” here means independent discretization and time-propagation paths, not independent software teams or empirical replication.

## 2. Frozen dimensionless problem

BA-ERC1's unit-consistent physical equation is nondimensionalized with fixed reference length and time. On three equal edges (e=1,2,3), with outward coordinate (s\in[0,1]) measured from the common centre,

$$
\partial_\theta u_e=D_*\partial_s^2u_e-\kappa_*u_e,
\qquad D_*=0.2,\quad \kappa_*=0.3.
$$

At the centre and sealed distal ends,

$$
u_1(0,\theta)=u_2(0,\theta)=u_3(0,\theta),\qquad
\sum_{e=1}^{3}\partial_su_e(0,\theta)=0,\qquad
\partial_su_e(1,\theta)=0.
$$

All displayed (s,\theta,D_*,\kappa_*) are dimensionless. Thus every exponential argument (-(D_*\lambda+\kappa_*)\theta) is dimensionless. The terminal time is frozen at (\theta_f=0.2).

## 3. Frozen panels and apparatus

No parameter fitting or threshold tuning is permitted. The grids are (N\in\{16,32,64\}) equal cells/elements per edge.

| panel | frozen initial state | role |
|---|---|---|
| S1 | (u_e(s,0)=\cos(\pi s)) on every edge | development/positive control for the symmetric sector |
| A0 | (u_e(s,0)=c_e\sin(\pi s/2)), (c=(1,-1,0)/\sqrt2) | sealed confirmation of continuity plus Kirchhoff coupling |
| M1 | (0.7\cos(\pi s)+0.3c_e\sin(\pi s/2)) | sealed confirmation of superposition across both sectors |
| D0 | A0 initial state with the centre incorrectly sealed on each edge independently | adverse control; it must be detected |

The FV solver uses centre cells (s_j=(j+1/2)h), a common junction face value (v=\frac13\sum_eu_{e,0}), the conservative first-cell stencil

$$
(L_hu)_{e,0}=\frac{(u_{e,1}-u_{e,0})/h-(u_{e,0}-v)/(h/2)}{h},
$$

the standard interior stencil, zero distal flux, and classical RK4 with

$$
n_{\rm step}=\left\lceil\frac{\theta_f}{0.05h^2/D_*}\right\rceil,
\qquad \Delta\theta=\theta_f/n_{\rm step}.
$$

The FEM solver uses one shared centre node, (N) linear elements per edge, the consistent element mass and stiffness matrices

$$
M^{(e)}=\frac h6\begin{pmatrix}2&1\\1&2\end{pmatrix},\qquad
K^{(e)}=\frac1h\begin{pmatrix}1&-1\\-1&1\end{pmatrix},
$$

and `scipy.linalg.eigh(K,M)`. If (Q^TMQ=I), propagation is

$$
u(\theta)=Q\exp[-(D_*\Lambda+\kappa_*I)\theta]Q^TMu(0).
$$

FEM nodal values are linearly evaluated at FV cell centres before comparison. No common evolution matrix, time integrator, or branch stencil may be shared between the two solvers.

## 4. Required brain-research fields

`BIO_STARTING_MECHANISM`: The inherited mechanism is passive membrane charge conservation plus axial Ohmic conduction on a branched cable with voltage continuity, Kirchhoff current balance, sealed distal ends, and passive leak. E2 evaluates only its nondimensional linear limit.

`CE_DELTA`: None at E2. The history-functional synapse and state-space geometry remain outside the simulated equation. This run tests numerical representation invariance of the inherited passive metric-graph law.

`MEASUREMENT_MODEL`: Every observation is a deterministic synthetic voltage field sampled at the same physical locations and time. The comparison norm is the cell-volume-weighted relative (L^2) norm. There is no measurement noise, filter, electrode transfer function, or latent-state inversion.

`DATA_PROVENANCE`: Only exact manufactured fields from the formulas in this contract may be generated. The verifier and receipt do not exist at contract freeze. `real_endpoint_opened=false`, `behavior_loaded=false`, and `model_fit=false` throughout.

`DATA_SPLIT`: S1 is a development/positive-control panel. A0 and M1 are sealed confirmation panels. D0 is a prespecified adverse control. No coefficient, mesh, time, tolerance, panel, or split may change after any result is read.

`OBSERVABLES`: FV exact-field error, FEM exact-field error, FV–FEM discrepancy at cell centres, 32-to-64 refinement ratios, FV strong junction-flux residual, FEM shared-node continuity and semidiscrete weak residual, discrete-energy change, generalized eigenvalue floor, mass-matrix positive definiteness, modal decay error, and D0 adverse-control error.

`RESIDUAL_RULE`: Every value must be finite. At (N=64), each exact-field error and each cross-solver discrepancy for S1/A0/M1 must be at most (10^{-3}). For each solver and each panel, (E_{32}/E_{64}\ge3). FV normalized strong Kirchhoff residual must be at most (10^{-12}). FEM centre continuity is exact by construction and its normalized weak equation residual must be at most (10^{-11}). Maximum relative energy increase must be at most (10^{-10}). Cholesky factorization of (M) must succeed and the smallest generalized eigenvalue must be at least (-10^{-10}). Modal decay relative error must be at most (10^{-3}). D0 must have A0 exact-field error at least (2\times10^{-2}) at (N=64); failure to detect it invalidates the apparatus.

`FALSIFIER`: Any frozen threshold failure stops E2. In particular, agreement on S1 alone is insufficient; failure on the antisymmetric or mixed sector kills solver equivalence. If D0 passes as if it were coupled, the test is non-discriminating. A solver mismatch cannot be repaired by changing both implementations or by relaxing thresholds after inspection.

`MATCHED_CONTROLS`: Exact S1/A0/M1 solutions; FV versus FEM; coarse/fine grids; correct shared junction versus D0 disconnected centre; energy-decay and nonnegative-spectrum controls. All share (D_*,\kappa_*,\theta_f), geometry, and sampling coordinates.

`MODEL_SELECTION`: There is no biological model selection at E2. A PASS requires both solvers independently to meet exact-solution gates and to agree with each other. A tie or cross-agreement without exact accuracy is not evidence. E3 may be considered only after a sealed PASS and independent audit; it is never automatically authorized.

`REVISION_TRIGGER`: One local apparatus revision is allowed only for a documented implementation defect that leaves the PDE, exact modes, panels, meshes, time, metrics, and thresholds unchanged. A wrong continuous identity, genuine cross-solver mismatch, missing adverse-control discrimination, or post-result threshold change ends this run as STOP. The failed receipt and exact failed source must be preserved before any allowed revision.

`CLAIM_CEILING`: `PASSIVE_METRIC_GRAPH_CROSSSOLVER_EQUIVALENCE / SYNTHETIC_MANUFACTURED_STIMULI / E2_NUMERICAL_VALIDATION_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

## 5. Predecessor evidence

`PREDECESSOR_EVIDENCE`:

| frozen predecessor item | SHA-256 | admissible inheritance |
|---|---|---|
| `00-contract.md` | `97a0d6318ddd4ea4a11cd2aff01ab858c8381765b709212681bf5ef428c1cdd5` | physical convention, staged ladder, and claim boundaries |
| `10-sources.md` | `6fb05ae378257ed666d34ca5c5cdd2611e7f6ce1fcf070dd988c9a231b9c0f35` | source map only |
| `11-math.md` | `a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685` | passive metric-graph equation and junction law |
| `12-routes.md` | `6269d567bcb2c1328f8d6a7be945116499c1b6ed95d1383c4f30b7761400ce51` | E2 route definition only |
| `artifacts/verify_electrical_cable_l0.py` | `708740755c0b183aa37aaa7883baa96dcd2a7347a5c76a72df0f46f49b7e9ce8` | L0 implementation history; not imported by E2 |
| `artifacts/l0-receipt.json` | `9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501` | `L0_NUMERICAL_INTEGRITY_ONLY` PASS |
| `20-audit.md` | `72ba6d2074afdb91c3c7867c4bd9c6abcdf76d285e08e77d4f58ecf7826f7cef` | post-L0 status boundary |
| `40-final-report.md` | `7a0989e50cdbaf7b8b6d5be4abdd0fc3259460c8528b2961a19e000c5d82a619` | final L0 narrative; no E2 result inherited |

The predecessor's PASS does not predict this run's result. Its biological, behavioral, state-dimension, consciousness, hippocampal, and AGI non-claims remain locked.

## 6. Frozen outcome labels

- `PASS`: all E2 gates pass; claim status is exactly `E2_CROSSSOLVER_MANUFACTURED_ONLY`.
- `STOP`: a mathematical or numerical gate fails; E3 remains locked.
- `APPARATUS_INVALID`: the adverse control is not detected, a source/environment seal fails, or an unauthorized post-result change occurs; no scientific conclusion is drawn.

All outcome labels keep `biological_claim=false`, `consciousness_claim=false`, `model_fit=false`, `real_endpoint_opened=false`, `behavior_loaded=false`, and `downstream_authorized=false`.
