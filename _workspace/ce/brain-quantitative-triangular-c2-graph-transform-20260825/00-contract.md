# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-quantitative-c1-graph-transform-20260825`

## Question and domain

For the normalized triangular chart

$$
x'=A_tx+a_t,\qquad y'=B_ty+g_t(x,y),
$$

replace the qualitative "$C^2$ bootstrap" by an exact conditional theorem and
finite recurrence. The base is affine, $A_t$ is invertible, and every norm is
the declared normalized product-chart operator norm. The result concerns a
supplied real base dimension $d\ge1$ and does not select $d$.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| triangular Lipschitz graph run | PASS / final-gated | $q<1$, tube/slope invariance, unique invariant Lipschitz graph | Do not weaken the predecessor gates. |
| triangular C1 run | PASS / final-gated | strict $\beta_1=q\mu<1$ and exact $(\delta,d)$ recurrence | Preserve predecessor failure ordering. |
| affine coupled C1 successor | PASS / final-gated | graph-dependent inverse-Jacobian is closed at first derivative | It does not supply a coupled C2 theorem. |

## Frozen C2 candidate

Let $\|Dh\|\le\kappa$, $\|D^2h\|\le\Lambda_2$. Let

$$
K_2\ge\sup\|D^2g_t\|,
\qquad
\|D^2g_t(x,y_1)-D^2g_t(x,y_2)\|\le K_3\|y_1-y_2\|.
$$

The proposed invariant-class and bunching quantities are

$$
\Lambda_{2,\mathrm{out}}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\},
\qquad
\beta_2=q\mu^2,
$$

$$
c_{21}=2\mu^2K_2(1+\kappa),
\qquad
c_{20}=\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}.
$$

The target recurrence is

$$
\delta_{n+1}\le q\delta_n,
\quad
d_{n+1}\le\beta_1d_n+c_{10}\delta_n,
\quad
e_{n+1}\le\beta_2e_n+c_{21}d_n+c_{20}\delta_n.
$$

Promotion requires the passing C1 predecessor,
$\Lambda_{2,\mathrm{out}}\le\Lambda_2$, and strict $\beta_2<1$.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| affine triangular C2 with $K_2,K_3$ | SELECTED | Exact Hessian chain rule and equality-boundary counterexample. |
| C2 convergence with $K_2$ but no $K_3$ | REJECTED | Different graph values leave $D^2g(x,h_1)-D^2g(x,h_2)$ uncontrolled. |
| affine coupled-base C2 | DEFERRED | Requires second derivatives of graph-dependent inverse maps. |
| nonaffine/local C2 | DEFERRED | Requires $D^2\phi^{-1}$, domain/boundary, and variable-base controls. |
| empirical neural C2 constants | DEFERRED | Requires a source-locked differentiable state/measurement model and held-out bounds. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED / not used in this formal successor.
- `CE_DELTA`: none; this run audits a conditional mathematical subtheorem only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE; no observation is scored.
- `DATA_PROVENANCE`: none; no local or remote empirical data are opened.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities plus exact-rational boundary fixtures.
- `FALSIFIER`: $q\mu^2=1$ with local invariant $h_c(x)=c x|x|$, which is C1 but not C2 at zero.
- `MATCHED_CONTROLS`: zero-$K_2/K_3$ affine reduction, failed C1 predecessor, class-boundary equality, and dimensions $1,4,5,6,100$.
- `MODEL_SELECTION`: no fitted model; select only the narrowest theorem whose proof closes.
- `REVISION_TRIGGER`: a missing chain-rule term or complete counterexample forces narrowing before implementation.
- `CLAIM_CEILING`: conditional affine triangular C2 theorem/apparatus only; no coupled/nonaffine/local C2, biology, consciousness, or 4--6 selection.

## Exactness and validation

All certificate inputs must be exact integers, `Fraction`, or canonical rational
strings. Binary floats and negative derivative bounds fail closed. Validation is
the focused C2 test first, then C1/C2 and dimensionless adjacency only if green.
No full suite, remote call, benchmark, or empirical analysis is authorized.
