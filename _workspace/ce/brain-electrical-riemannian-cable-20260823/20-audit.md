# BA-ERC1 ledger audit -- electrical Riemannian cable reset

Status: COMPLETE

Gate: PASS

Scope verdict: PASS -- BA-ERC1 L0 numerical integrity only; five frozen gates U0/K0/P0/N0/H0 passed after one H0-predicate-only apparatus revision; attempt-00 failure preserved; source and environment seals match; no real endpoint, behavior, model fit, biological claim, consciousness claim, or downstream authorization.

## 1. Frozen-input manifest

| frozen input | SHA-256 | audit use |
|---|---|---|
| `00-contract.md` | `97a0d6318ddd4ea4a11cd2aff01ab858c8381765b709212681bf5ef428c1cdd5` | scope, falsifiers, staged authorization, claim ceiling |
| `10-sources.md` | `6fb05ae378257ed666d34ca5c5cdd2611e7f6ce1fcf070dd988c9a231b9c0f35` | mechanistic source lock and provenance exclusions |
| `11-math.md` | `a96c9cda861691ea0edabefcc1f7d34befae3e4ec4973d8ecdc8b9492ac15685` | equation, units, state space, conditional results, counterexample |
| `12-routes.md` | `6269d567bcb2c1328f8d6a7be945116499c1b6ed95d1383c4f30b7761400ce51` | selected/deferred/rejected route boundary |

| predecessor evidence | SHA-256 | status carried forward |
|---|---|---|
| BA-SRM9 `artifacts/f2c-receipt.json` | `a43e14da1e099f30d3cb970f35db199159be83916b9ce33e685f494641958bf2` | `F2C_TERMINAL_NUMERIC_FUTILITY / FORMAL_AUDIT_INCOMPLETE / NO_DOWNSTREAM`; it is not evidence for or against the cable equation |

## 2. Claim-status ledger

| item | status | audited boundary |
|---|---|---|
| Branched metric-graph morphology, typed axial Ohm law, charge conservation, and cable--HH primary PDE | [definition] + [axiom: physical model selection] + [derived] | Formalized under the stated sign convention and current-density units; not a claim of exact biology at every scale. |
| Coordinate rewrite as weighted Laplace--Beltrami/Sturm--Liouville operator | [derived] | Valid only with the declared $ds=\sqrt g\,dx$, transport, and membrane-area weights. |
| Passive dissipation identity | [theorem: conditional] | Requires one spatially constant $E_L$, passive leak, sufficiently regular solutions, and sealed-end/Kirchhoff conditions. |
| Cable voltage state, history field, reference metric, and observation quotient | [definition] | Infinite dimensionality is a function-space property; the observation pullback is only semidefinite on the full state and requires the quotient. |
| Finite-observation no-go | [theorem] | Holds for finite-dimensional observations of the declared infinite-dimensional state, with the stated quotient regularity condition. |
| HH channel and conductance-synapse families | [empirical formula] | Source-locked model family; no mammalian parameter fit or biological validation has occurred. |
| Bounded causal-history conductance | [hypothesis] | Directed $i\leftarrow j$ is presynaptic $j$ to postsynaptic $i$; history is strictly past and has no atom at zero. It must later beat finite-state controls. |
| Smooth causal release bump | [definition] | A $C^\infty$ compact-support kernel construction, not evidence that neural release is globally smooth. |
| Continuous effective dimensions | [derived diagnostic] | Conditional on a nonzero positive trace-class covariance; not graph dimension, consciousness dimension, or an observer-independent quantity. |
| PNP electrodiffusion | [axiom: upgrade model] | Higher-fidelity boundary only; neither derived, solved, nor rigorously reduced to the cable PDE here. |

## 3. Closure and counterexample audit

| audit item | finding | disposition |
|---|---|---|
| P0: direction and electrical typing | Resolved: $i\leftarrow j$ assigns presynaptic $j$ and postsynaptic $i$; membrane terms in the PDE are current densities, while IC/VC remain separate typed observables. | no open P0 |
| P1: causality, soma, and passive-energy premises | Resolved: strict-past measure has no atom at zero; soma voltage is the trace-equality closed subspace; passive theorem fixes a spatially constant $E_L$. | no open P1 |
| Source-lock execution | The preflight statement that L0 was unrun and had no receipt is preserved verbatim in `artifacts/20-audit-preflight.md`, SHA-256 `f7333a259659a4fd758c1fdb7f008c282a777c8f31162f6f447f5eae2e76083a`. The final receipt matches all frozen 00/10/11/12 and preflight hashes. | E0/E1 have a sealed L0 numerical-integrity receipt; no biological or downstream promotion follows. |
| Complete counterexample | A synapse with a finite sum of exponential kernels admits a finite-dimensional Markov realization through auxiliary ODE states. | The parent statement `every history synapse is intrinsically infinite-dimensional` is false and is not active. The continuum cable state may still be infinite dimensional. |
| Smoothness overclaim | A multi-edge metric-graph vertex is not a globally smooth manifold point; impulses and threshold events can reduce temporal regularity. | Only edgewise smooth/weak solutions under stated compatibility assumptions remain active. |

## 4. L0 execution evidence

| evidence | SHA-256 | finding | ledger status |
|---|---|---|---|
| verifier `artifacts/verify_electrical_cable_l0.py` | `708740755c0b183aa37aaa7883baa96dcd2a7347a5c76a72df0f46f49b7e9ce8` | Frozen U0/K0/P0/N0/H0 fixture implementation. | source sealed |
| attempt-00 `artifacts/l0-receipt-attempt-00.json` | `848a0a5ab528dc681eff9c384dbb0e733366ba3e89e45a2283399965658b41c4` | U0, K0, P0, and N0 passed; H0 alone failed its original numerical endpoint-flatness predicate. | preserved failure; no overwrite |
| final `artifacts/l0-receipt.json` | `9e643eaf70302ff4369f15bf1fa044f11660a45c9148869395fb65a643006501` | U0/K0/P0/N0/H0 all passed; `source_match=true`; `claim_status=L0_NUMERICAL_INTEGRITY_ONLY`. | L0 numerical integrity only |

The sole apparatus revision is restricted to the H0 numerical predicate: it replaces the endpoint finite-difference threshold with a machine-precision-scaled tolerance and closes floating-point conductance bounds. It does not change the electrical equation or any other gate. The recorded endpoint-flatness check at `1024eps` is only a finite-difference proxy. The $C^\infty$ claim rests on the exact compactly supported bump's analytic construction in the frozen mathematics, not on that floating-point proxy.

The final receipt records the sealed system-Python environment, Python 3.11.9, NumPy 2.4.6, bytecode disabled, `real_endpoint_opened=false`, `behavior_loaded=false`, `model_fit=false`, `biological_claim=false`, `consciousness_claim=false`, and `downstream_authorized=false`.

## 5. Authorization and claim ceiling

| boundary | ledger decision |
|---|---|
| E0 equation audit | executed and passed as L0 numerical integrity only |
| E1 manufactured cable | executed and passed as L0 numerical integrity only |
| E2 and later | locked pending a successor frozen apparatus and receipt |
| Real data, behavior, or fitted biological parameters | locked; no data endpoint has opened |
| Consciousness, memory, hippocampal hash, or AGI interpretation | locked; no active claim |

`CLAIM_CEILING`: `CONDITIONAL_ELECTROPHYSIOLOGICAL_CABLE_MODEL / INFINITE_DIMENSIONAL_STATE_FORMALIZATION / FINITE_OBSERVATION_QUOTIENT / L0_ONLY / BIOLOGICAL_VALIDATION_UNOPENED`.

## 6. Final audit decision

PASS -- BA-ERC1 L0 numerical integrity only; five frozen gates U0/K0/P0/N0/H0 passed after one H0-predicate-only apparatus revision; attempt-00 failure preserved; source and environment seals match; no real endpoint, behavior, model fit, biological claim, consciousness claim, or downstream authorization.
