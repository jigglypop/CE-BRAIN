# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-quantitative-coupled-c1-graph-transform-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-quantitative-triangular-c2-graph-transform-20260825`

## Question and domain

For the normalized affine coupled chart

$$
x'=A_tx+a_t+f_t(x,y),
\qquad
y'=B_ty+g_t(x,y),
$$

derive a complete two-graph Hessian recurrence. The output base point is held
fixed while each graph has its own preimage. Every norm is the declared
normalized product-chart operator norm. The theorem preserves a supplied real
base dimension $d\ge1$ and does not select it.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| affine coupled C1 run | PASS / final-gated | $\alpha>0$, $Q<1$, invariant $C^{1,1}$ class, $\beta_1=Q/\alpha<1$, exact $(\delta,d)$ recurrence | Do not omit graph-dependent preimage or inverse-Jacobian differences. |
| affine triangular C2 run | PASS / final-gated | complete Hessian chain rule, $K_3$ necessity, strict $q\mu^2<1$ boundary witness | The coupled result must reduce exactly when base coupling vanishes. |

## Frozen notation from the C1 predecessor

Let

$$
q=b+L_{gy},
\qquad
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa,
\qquad
s=q\kappa+L_{gx},
$$

$$
Q=q+s\frac{L_{fy}}{\alpha},
\qquad
r_x=\frac{L_{fy}}{\alpha},
\qquad
Z=1+(1+\kappa)r_x.
$$

The graph Hessian bound is $\Lambda$. When $L_{fy}>0$, the coupled preimage
shift also requires the graph-Hessian modulus
$\operatorname{Lip}(D^2h)\le\Xi$. The map Hessian bounds are $H_f,H_g$,
and their normalized full-state Lipschitz moduli are $T_f,T_g$. Define

$$
C_F=H_f(1+\kappa)^2+L_{fy}\Lambda,
\qquad
C_Y=q\Lambda+H_g(1+\kappa)^2,
$$

$$
\rho=\frac{s}{\alpha},
\qquad
N=C_Y+\rho C_F.
$$

For one graph, define the input-base Lipschitz bounds

$$
C_T=\frac{C_Y}{\alpha}+\frac{sC_F}{\alpha^2},
$$

$$
C_P=T_f(1+\kappa)^3+3H_f(1+\kappa)\Lambda+L_{fy}\Xi,
$$

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda+T_g(1+\kappa)^3,
$$

$$
C_N=C_R+C_TC_F+\rho C_P,
\qquad
\Xi_{\mathrm{out}}
=\frac{C_N}{\alpha^3}+\frac{2NC_F}{\alpha^4}.
$$

The predecessor supplies

$$
\|DF_1-DF_2\|\le L_{fy}d+A_\delta\delta,
\qquad
\|D(\mathcal Th_1)-D(\mathcal Th_2)\|
\le\beta_1d+c_1\delta.
$$

## Frozen second-order candidate

For the base-map Hessian difference define

$$
P_d=2H_f(1+\kappa),
$$

$$
P_\delta
=L_{fy}\Xi r_x+H_fZ\Lambda+2H_f(1+\kappa)\Lambda r_x
+T_fZ(1+\kappa)^2.
$$

For the fiber-map Hessian difference define

$$
R_d=2H_g(1+\kappa),
$$

$$
R_\delta
=q\Xi r_x+H_gZ\Lambda+2H_g(1+\kappa)\Lambda r_x
+T_gZ(1+\kappa)^2.
$$

Then

$$
N_e=Q,
\qquad
N_d=R_d+C_F\beta_1+\rho P_d,
\qquad
N_\delta=R_\delta+C_Fc_1+\rho P_\delta.
$$

The target Hessian recurrence is

$$
e_{n+1}\le\beta_{2,c}e_n+c_{21,c}d_n+c_{20,c}\delta_n,
$$

with

$$
\beta_{2,c}=\frac{Q}{\alpha^2},
$$

$$
c_{21,c}=\frac{N_d}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3},
\qquad
c_{20,c}=\frac{N_\delta}{\alpha^2}
+\frac{2NA_\delta}{\alpha^3}.
$$

Promotion requires the passing coupled C1 certificate and strict
$\beta_{2,c}<1$. Its existing class condition is exactly
$N/\alpha^2\le\Lambda$. If $L_{fy}>0$, promotion additionally requires
$\Xi_{\mathrm{out}}\le\Xi$. If $L_{fy}=0$, both graphs have the same
preimage, every $\Xi r_x$ term vanishes, and this additional class gate is not
required; this branch preserves the graph-independent triangular reduction.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| affine coupled C2 with $T_f,T_g$ | SELECTED | Full inverse-map Hessian identity and triangular reduction. |
| coupled C2 without map-Hessian moduli | REJECTED | Different preimages leave $D^2f,D^2g$ location changes uncontrolled. |
| coupled C2 with no graph-Hessian modulus | REJECTED FOR $L_{fy}>0$ | $D^2h(x_1)-D^2h(x_2)$ is uncontrolled; reopened automatically only at $L_{fy}=0$. |
| nonaffine/local coupled C2 | DEFERRED | Requires variable $A(x)$, chart boundaries, and additional inverse-map terms. |
| C3 and higher | DEFERRED | Requires order-wise multilinear classes and Faà di Bruno bookkeeping. |
| empirical neural constants | DEFERRED | Requires a source-locked differentiable dynamics/measurement model. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED / not used in this formal successor.
- `CE_DELTA`: none; this run audits a conditional mathematical subtheorem only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE; no observation is scored.
- `DATA_PROVENANCE`: none; no local or remote empirical data are opened.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities and exact-rational boundary fixtures.
- `FALSIFIER`: zero-coupling reduction at $q\mu^2=1$ with invariant $h_c(x)=cx|x|$.
- `MATCHED_CONTROLS`: zero coupling, missing map/graph-Hessian modulus, failed C1 predecessor, strict/equality class and bunching, and dimensions $1,4,5,6,100$.
- `MODEL_SELECTION`: no fitted model; admit only the fully closed affine coupled theorem.
- `REVISION_TRIGGER`: a missing inverse-map or Hessian product term forces revision before implementation.
- `CLAIM_CEILING`: conditional affine coupled C2 theorem/apparatus only; no nonaffine/local C2, C3+, biology, consciousness, or 4--6 selection.

## Exactness and validation

All inputs use exact integers, `Fraction`, or canonical rational strings.
Binary floats, Booleans, negative moduli, and invalid iteration inputs fail
closed. Run the focused coupled C2 test first, then adjacent coupled C1/C2,
triangular reduction, and dimensionless tests. No full suite, benchmark,
remote call, or empirical analysis is authorized.
