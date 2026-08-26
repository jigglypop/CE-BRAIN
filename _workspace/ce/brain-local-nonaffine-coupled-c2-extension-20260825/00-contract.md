# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-nonaffine-coupled-c2-extension-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-local-nonaffine-triangular-c2-extension-20260825`

## Question

For compact local base domains $U_t=\overline B(c_t,R_t)$ and graph-dependent
base maps

$$
F_{t,h}(x)=\phi_t(x)+f_t(x,h(x)),
$$

what additional domain certificate makes the final-gated global nonaffine
coupled C2 graph transform well-defined locally?

## Predecessor evidence

| Predecessor | State | Preserved result | Missing seam |
|---|---|---|---|
| global nonaffine coupled C2 | PASS / final-gated | Exact $P,R,N,J$ calculus, conditional C2,1 invariance, and strict second bunching | It assumes the graph-dependent inverse is available wherever evaluated. |
| overflow-local graph-independent nonaffine C2 | PASS / final-gated | Uniform inverse-domain coverage is sufficient for a local overflow graph transform | Its inverse is $\phi_t^{-1}$ and does not vary with the graph. |
| matched-domain graph-independent nonaffine C2 | PASS / final-gated | Independent forward/inverse inclusions give exact domain equality | It does not prove uniform boundary contact for graph-dependent $F_{t,h}$. |

Threshold, seed, endpoint, decoder, and empirical data are absent. This is a
new domain-composition seam, not a retry of an empirical or simulator route.

## Frozen domain gate

For every admissible graph $h$ require a C2 inverse on an open collar of
$U_{t+1}$ and a supplied uniform bound

$$
\sup_h\sup_{x'\in U_{t+1}}
\|F_{t,h}^{-1}(x')-c_t\|
\le R_{\rm pre}\le R_t.
$$

The normalized coverage margin is

$$
m_{\rm dom}=\frac{R_t-R_{\rm pre}}{X_0}.
$$

Passing equality is allowed but is not robust. The conclusion is
backward-covered overflow invariance only; it does not assert
$F_{t,h}(U_t)\subseteq U_{t+1}$.

## Exact coupled witness

In one base dimension let

$$
F_h(x)=\lambda x+a\sin x+\varepsilon h(x),
\qquad |h(x)|\le R_y,
\qquad \lambda>a\ge0,
$$

with $\varepsilon\ge0$. For $|x'|\le R_{t+1}$,

$$
|F_h(x)|\ge(\lambda-a)|x|-\varepsilon R_y
$$

implies the uniform bound

$$
R_{\rm pre}
=\frac{R_{t+1}+\varepsilon R_y}{\lambda-a}.
$$

Freeze the strict fixture

$$
\lambda=2,quad a=\frac14,quad
\varepsilon=\frac1{20},quad R_y=R_t=R_{t+1}=1,
$$

so the base inverse bound is $\mu=4/7$, the actual coupled inverse bound
is $40/69$, $H_\phi=T_\phi=1/4$,
$R_{\rm pre}=3/5$, and $m_{\rm dom}=2/5$.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| uniform graph-dependent inverse coverage | SELECTED | It evaluates the actual $F_{t,h}^{-1}$ required by the transform. |
| reuse coverage of $\phi_t^{-1}$ | REJECTED | A bounded fiber coupling can move the preimage outside $U_t$. |
| infer full forward retention from inverse coverage | REJECTED | The expanding affine subcase is a counterexample. |
| exact matched-domain graph-dependent composition | DEFERRED | Uniform boundary contact for every admissible graph needs an additional boundary-compatible class. |
| C3 and higher | DEFERRED | Requires fourth-order moduli and higher recurrences. |

## Required controls

- exact strict coupled witness and zero-coupling reduction;
- equality coverage passes without robust interior;
- $R_{\rm pre}>R_t$ fails with a named domain code;
- predecessor failures stay primary;
- checking $\phi_t^{-1}$ alone is falsified explicitly;
- inverse coverage does not imply forward retention;
- exact recurrence, scale covariance, dimensions 1/4/5/6/100, and invalid
  exact inputs.

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact identities, inequalities, and rational fixtures.
- `FALSIFIER`: $\phi$-only coverage counterexample, overflow counterexample,
  failed exact reductions, or a missing domain failure.
- `MATCHED_CONTROLS`: strict/equality/failed coverage, zero coupling,
  predecessor failure, scale and dimension controls.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: any use of $\phi^{-1}$ in place of $F_h^{-1}$ or any
  unsupported full-forward claim forces revision.
- `CLAIM_CEILING`: conditional backward-covered local nonaffine coupled C2;
  no matched full-forward domain, C3+, biology, consciousness, or dimension
  selection.

## Exactness and validation

Exact rational inputs only. Floats, Booleans, negative radii/moduli, and
invalid iterations fail closed. Run focused, predecessor adjacency,
dimensionless, and graph integration only; no full suite or empirical action.
