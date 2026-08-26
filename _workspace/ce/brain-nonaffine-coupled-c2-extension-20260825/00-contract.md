# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-nonaffine-coupled-c1-extension-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-quantitative-coupled-c2-graph-transform-20260825`

## Question and additional modulus

For the nonaffine coupled chart

$$
F_h(x)=\phi_t(x)+f_t(x,h(x)),
\qquad
Y_h(x)=B_th(x)+g_t(x,h(x)),
$$

retain the predecessor bound $\|D^2\phi_t\|\le H_\phi$ and add

$$
\|D^2\phi_t(x_1)-D^2\phi_t(x_2)\|
\le T_\phi\|x_1-x_2\|.
$$

All $f,g$, graph C2,1, and coupled Lipschitz constants retain the affine
coupled C2 meanings.

## Frozen one-graph layers

Let $C_F^{\rm na}$ and the nonaffine C1 recurrence come from the predecessor.
Put

$$
N=C_Y+\rho C_F^{\rm na},
\qquad
C_T=\frac{C_Y}{\alpha}
+\frac{sC_F^{\rm na}}{\alpha^2}.
$$

The base-Hessian modulus becomes

$$
C_P^{\rm na}
=T_\phi+T_f(1+\kappa)^3
+3H_f(1+\kappa)\Lambda+L_{fy}\Xi.
$$

With the unchanged

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda
+T_g(1+\kappa)^3,
$$

freeze

$$
C_N^{\rm na}=C_R+C_TC_F^{\rm na}+\rho C_P^{\rm na},
$$

$$
\Xi_{\rm out}^{\rm na}
=\frac{C_N^{\rm na}}{\alpha^3}
+\frac{2NC_F^{\rm na}}{\alpha^4}.
$$

As in the affine theorem, the $\Xi$ gate is required only when $L_{fy}>0$.

## Frozen two-graph recurrence

The base-Hessian difference is

$$
\|P_1-P_2\|
\le L_{fy}e+P_dd+P_\delta^{\rm na}\delta,
$$

where

$$
P_d=2H_f(1+\kappa),
$$

$$
P_\delta^{\rm na}
=T_\phi r_x+L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x
+T_fZ(1+\kappa)^2.
$$

$R_d,R_\delta$ are unchanged. With predecessor coefficients
$\beta_1,c_{10}^{\rm na},A_\delta^{\rm na}$, freeze

$$
N_d^{\rm na}=R_d+C_F^{\rm na}\beta_1+\rho P_d,
$$

$$
N_\delta^{\rm na}
=R_\delta+C_F^{\rm na}c_{10}^{\rm na}
+\rho P_\delta^{\rm na}.
$$

Then

$$
e_{n+1}
\le\beta_{2,c}e_n+c_{21,c}^{\rm na}d_n
+c_{20,c}^{\rm na}\delta_n,
$$

$$
\beta_{2,c}=\frac Q{\alpha^2},
$$

$$
c_{21,c}^{\rm na}
=\frac{N_d^{\rm na}}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3},
$$

$$
c_{20,c}^{\rm na}
=\frac{N_\delta^{\rm na}}{\alpha^2}
+\frac{2NA_\delta^{\rm na}}{\alpha^3}.
$$

Promotion requires the passing nonaffine coupled C1 certificate, the
conditional C2,1 class gate, and strict $Q/\alpha^2<1$.

## Exact curved fixture

Use $\phi_{\lambda,a}(x)=\lambda x+a\sin x$ with
$(\lambda,a)=(1001/1000,1/1000)$. Then

$$
\mu=1,
\qquad
H_\phi=T_\phi=\frac1{1000}.
$$

With the affine coupled C2 baseline, freeze

$$
C_F^{\rm na}=\frac{147}{2000},
\quad
N=\frac{17347}{74000},
\quad
C_T=\frac{17347}{68450},
$$

$$
C_P^{\rm na}=\frac{159}{1600},
\quad
C_R=\frac{1987}{8000},
\quad
C_N^{\rm na}=\frac{77517343}{273800000},
$$

$$
\Xi_{\rm out}^{\rm na}=\frac{701739032}{1733598925},
\quad
P_\delta^{\rm na}=\frac{163}{9250},
$$

$$
N_d^{\rm na}=\frac{8796}{171125},
\quad
N_\delta^{\rm na}=\frac{4895179}{158290625},
$$

$$
\beta_{2,c}=\frac{12320}{50653},
\quad
c_{21,c}^{\rm na}=\frac{840496}{9370805},
\quad
c_{20,c}^{\rm na}=\frac{410712208}{8667994625}.
$$

## Required reductions

- $H_\phi=T_\phi=0$: exact affine coupled C2 coefficients.
- $f\equiv0$: exact graph-independent nonaffine triangular C2 coefficients
  after identifying $\nu=H_\phi\mu^3$; the $\Xi$ gate is unused.
- $Q/\alpha^2=1$: predecessor C1/non-C2 counterexample remains active.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| global nonaffine coupled C2 with $H_\phi,T_\phi$ | SELECTED | Full $P,N,J$ expansion closes. |
| reuse affine $C_P,P_\delta$ | REJECTED | Misses $T_\phi$ and $T_\phi r_x$. |
| use $H_\phi$ without $T_\phi$ | REJECTED | Cannot control the C2,1 class or two-preimage Hessian difference. |
| graph-independent reduction with mandatory $\Xi$ | REJECTED | Preimages coincide when $L_{fy}=0$. |
| local matched-domain nonaffine coupled C2 | DEFERRED | Compose independent domain gates afterward. |
| C3 and higher | DEFERRED | Requires fourth-order moduli and Faà di Bruno layers. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities and rational fixtures.
- `FALSIFIER`: missing $T_\phi$ or $T_\phi r_x$; affine/nonaffine-triangular
  reduction mismatch; equality bunching.
- `MATCHED_CONTROLS`: strict curved fixture, both exact reductions, conditional
  $\Xi$ bypass, class/bunching equality, dimensions 1/4/5/6/100.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: any missing base-curvature propagation or failed
  reduction forces revision.
- `CLAIM_CEILING`: conditional global nonaffine coupled C2 theorem/apparatus;
  no local domain composition, C3+, biology, consciousness, or dimension
  selection.

## Exactness and validation

Exact rational inputs only. Floats, Booleans, negative moduli, invalid
iterations, and predecessor failures fail closed. Run focused, both reductions,
dimensionless, and graph integration only. No full suite or empirical action.
