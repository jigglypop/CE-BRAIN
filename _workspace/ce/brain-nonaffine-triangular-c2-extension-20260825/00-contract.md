# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-quantitative-triangular-c2-graph-transform-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-nonaffine-triangular-c1-extension-20260825`

## Question and domain

For the normalized graph-independent triangular chart

$$
x'=\phi_t(x),
\qquad
y'=B_ty+g_t(x,y),
$$

replace the affine-base C2 restriction by uniform bounds on the inverse base
map $\psi_t=\phi_t^{-1}$. The base is a global C2 diffeomorphism with

$$
\|D\psi_t\|\le\mu,
\qquad
\|D^2\psi_t\|\le\nu.
$$

Every graph norm is taken in the declared normalized product chart. The result
preserves a supplied real base dimension $d\ge1$ and does not select it.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| global nonaffine triangular C1 run | PASS / final-gated | graph independence makes the inverse derivative common; strict $q\mu<1$ closes C1 | Local boundaries and second derivatives remain separate. |
| affine triangular C2 run | PASS / final-gated | invariant Hessian class, $K_3$ necessity, strict $q\mu^2<1$, exact recurrence | Every new $\nu$ term must vanish at $\nu=0$. |

## Frozen C2 candidate

Let $q=b+L_y$, $s=q\kappa+L_x$, $\|D^2h\|\le\Lambda_2$,
$\|D^2g\|\le K_2$, and

$$
\|D^2g_t(x,y_1)-D^2g_t(x,y_2)\|
\le K_3\|y_1-y_2\|.
$$

The proposed output Hessian bound is

$$
\Lambda_{2,\mathrm{out}}^{\rm na}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}+s\nu.
$$

For two graph iterates, freeze

$$
\beta_2=q\mu^2,
$$

$$
c_{21}^{\rm na}
=2\mu^2K_2(1+\kappa)+q\nu,
$$

$$
c_{20}^{\rm na}
=\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}
+\nu(H_y\kappa+H_x).
$$

The target recurrence is

$$
e_{n+1}\le\beta_2e_n+c_{21}^{\rm na}d_n
+c_{20}^{\rm na}\delta_n.
$$

Promotion requires the passing nonaffine C1 certificate,
$\Lambda_{2,\mathrm{out}}^{\rm na}\le\Lambda_2$, and strict
$\beta_2<1$.

## Exact analytic witness

For

$$
\phi_a(x)=x+a\sin x,
\qquad 0\le a<1,
$$

freeze

$$
\mu_a=\frac1{1-a},
\qquad
\nu_a=\frac{a}{(1-a)^3}.
$$

The second formula follows from
$\psi_a''=-\phi_a''/(\phi_a')^3$ and is a conservative exact global bound.
$a=1$ remains inadmissible because $\phi_1'(\pi)=0$.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| global nonaffine triangular C2 with $\mu,\nu$ | SELECTED | Exact second-order chain rule and affine reduction. |
| C2 using only $\mu$ | REJECTED | $DS_hD^2\psi_t$ is uncontrolled. |
| sine-perturbed analytic family | SELECTED | Supplies exact nonaffine inverse derivative/Hessian bounds. |
| local nonaffine C2 | DEFERRED | Needs image/domain compatibility and inward boundary conditions. |
| nonaffine coupled C2 | DEFERRED | Graph-dependent inverse derivatives require additional comparison terms. |
| C3 and higher | DEFERRED | Requires higher inverse derivatives and Faà di Bruno bounds. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED / not used in this formal successor.
- `CE_DELTA`: none; this run audits a conditional mathematical subtheorem only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE; no observation is scored.
- `DATA_PROVENANCE`: none; no local or remote empirical data are opened.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities and exact-rational analytic fixtures.
- `FALSIFIER`: missing $\nu$ term; $q\mu^2=1$ invariant $h_c(x)=cx|x|$; $a=1$ inverse failure.
- `MATCHED_CONTROLS`: $a=0$, $\nu=0$ affine reduction, strict/equality class and bunching, dimensions $1,4,5,6,100$.
- `MODEL_SELECTION`: no fitted model; admit only the fully proved global triangular theorem.
- `REVISION_TRIGGER`: a missing chain-rule or inverse-Hessian term forces revision before implementation.
- `CLAIM_CEILING`: conditional global nonaffine triangular C2 theorem/apparatus only; no local/coupled nonaffine C2, C3+, biology, consciousness, or 4--6 selection.

## Exactness and validation

All inputs use exact integers, `Fraction`, or canonical rational strings.
Binary floats, Booleans, negative bounds, $a\notin[0,1)$, and invalid iteration
inputs fail closed. Run the focused nonaffine C2 test first, then affine
reduction, nonaffine C1/C2, and dimensionless adjacency. No full suite,
benchmark, remote call, or empirical analysis is authorized.
