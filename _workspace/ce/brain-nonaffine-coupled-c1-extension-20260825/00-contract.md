# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-quantitative-coupled-c1-graph-transform-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-nonaffine-triangular-c2-extension-20260825`

## Question and chart

For

$$
x'=\phi_t(x)+f_t(x,y),
\qquad
y'=B_ty+g_t(x,y),
$$

replace the affine base $A_tx+a_t$ by a graph-independent global C2
diffeomorphism satisfying the co-Lipschitz and curvature bounds

$$
\|\phi_t(x_1)-\phi_t(x_2)\|
\ge\mu^{-1}\|x_1-x_2\|,
\qquad
\|D^2\phi_t\|\le H_\phi.
$$

All coupled Lipschitz constants and normalized graph classes retain the
predecessor meanings.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| affine coupled C1 | PASS / final-gated | exact base inversion, C1,1 class and derivative recurrence | $D\phi$ was constant. |
| graph-independent nonaffine triangular C2 | PASS / final-gated | uniform inverse/curvature calculus is admissible | It had no graph-dependent base preimage. |

## Frozen nonaffine C1 candidate

The Lipschitz base certificate is unchanged:

$$
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa>0,
\qquad
Q=q+\frac{(q\kappa+L_{gx})L_{fy}}{\alpha}<1.
$$

Let $s=q\kappa+L_{gx}$, $r_x=L_{fy}/\alpha$,
$Z=1+(1+\kappa)r_x$, and let $\Lambda$ bound
$\operatorname{Lip}(Dh)$. The one-graph Jacobian bounds become

$$
C_F^{\rm na}
=H_\phi+H_f(1+\kappa)^2+L_{fy}\Lambda,
$$

$$
C_Y=q\Lambda+H_g(1+\kappa)^2.
$$

Thus

$$
\Lambda_{\rm out}^{\rm na}
=\frac{C_Y}{\alpha^2}
+\frac{sC_F^{\rm na}}{\alpha^3}.
$$

For two graphs, freeze

$$
A_\delta^{\rm na}
=H_\phi r_x+H_fZ(1+\kappa)+L_{fy}\Lambda r_x,
$$

$$
Y_\delta=q\Lambda r_x+H_gZ(1+\kappa).
$$

The derivative recurrence is

$$
d_{n+1}\le\beta_1d_n+c_{10}^{\rm na}\delta_n,
$$

where

$$
\beta_1=\frac Q\alpha,
\qquad
c_{10}^{\rm na}
=\frac{Y_\delta}{\alpha}
+\frac{sA_\delta^{\rm na}}{\alpha^2}.
$$

Promotion requires the coupled Lipschitz certificate,
$\Lambda_{\rm out}^{\rm na}\le\Lambda$, and strict $Q/\alpha<1$.

## Exact curved fixture

For

$$
\phi_{\lambda,a}(x)=\lambda x+a\sin x,
\qquad \lambda>a\ge0,
$$

freeze

$$
\mu=(\lambda-a)^{-1},
\qquad
H_\phi=a.
$$

Choose $\lambda=1001/1000$, $a=1/1000$, so $\mu=1$ and
$H_\phi=1/1000$. With the affine predecessor's strict baseline,

$$
\alpha=\frac{37}{40},
\quad
Q=\frac{77}{370},
\quad
C_F^{\rm na}=\frac{147}{2000},
\quad
C_Y=\frac{89}{400},
$$

$$
\Lambda_{\rm out}^{\rm na}=\frac{69388}{253265},
\quad
A_\delta^{\rm na}=\frac{351}{18500},
\quad
Y_\delta=\frac1{37},
$$

$$
\beta_1=\frac{308}{1369},
\qquad
c_{10}^{\rm na}=\frac{41212}{1266325}.
$$

At $H_\phi=0$, every new term vanishes and all coefficients reduce exactly to
the affine coupled C1 theorem.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| global nonaffine coupled C1 with finite $H_\phi$ | SELECTED | Exact derivative and inverse-Jacobian expansion closes. |
| reuse affine $C_F,A_\delta$ unchanged | REJECTED | Omits $D\phi(x_1)-D\phi(x_2)$. |
| C1 from co-Lipschitz $\mu$ alone | REJECTED | Gives no modulus for $D\phi$. |
| local matched-domain version | DEFERRED | Domain gates are independent of the differential extension. |
| nonaffine coupled C2 | DEFERRED TO IMMEDIATE SUCCESSOR | Needs $D^2\phi$ variation and modified Hessian terms. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities and rational fixtures.
- `FALSIFIER`: missing $H_\phi$ or $H_\phi r_x$ term; affine reduction
  mismatch; derivative bunching equality.
- `MATCHED_CONTROLS`: exact curved fixture, $H_\phi=0$ affine reduction,
  zero coupling, class/bunching equality, dimensions 1/4/5/6/100.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: any additional nonaffine first-order term or failed
  affine reduction forces revision before C2 work.
- `CLAIM_CEILING`: conditional global graph-independent-base nonaffine coupled
  C1 theorem/apparatus only; no nonaffine coupled C2, local domain, C3+,
  biology, consciousness, or dimension selection.

## Exactness and validation

All inputs use exact integers, `Fraction`, or canonical rational strings.
Floats, Booleans, negative curvature, and invalid witness parameters fail
closed. Run focused, affine reduction, dimensionless, and graph adjacency only.
No full suite, remote call, or empirical operation is authorized.
