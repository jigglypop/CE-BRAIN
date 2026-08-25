# Quantitative C1 triangular graph-transform contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-quantitative-nonlinear-graph-transform-20260825`

## Objective

Replace the predecessor's qualitative smooth-bootstrap sentence by an explicit $C^1$ sufficient condition and derivative-iteration bound in an affine triangular subcase. The existing Lipschitz graph certificate remains mandatory. This run does not claim $C^{r-1}$, a nonaffine/local chart, or a neural manifold.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | No-retry condition |
|---|---|---|---|---|
| Triangular Lipschitz graph | predecessor G1--G2; focused 26/26 | PASS | $q<1$, tube and slope conditions give a unique invariant Lipschitz graph. | C1 promotion may occur only after this full gate passes. |
| Affine coupled-base extension | coupled successor | PASS | Base-fiber coupling has a separate Lipschitz theorem. | This run is triangular and does not silently claim coupled C1 regularity. |
| $C^{r-1}$ bootstrap | parent Theorem 9 | CONDITIONAL/QUALITATIVE | Normal hyperbolicity plus higher derivative control can yield smoothness. | Do not cite “standard bootstrap” as an executable bound. |

## Frozen C1 chart

Use the predecessor chart with affine base

$$
x'=A_tx+a_t,
\qquad y'=B_ty+g_t(x,y),
\tag{D1}
$$

where $A_t$ is bijective, $\|A_t^{-1}\|\le\mu$, and $g_t$ is $C^1$. Retain all predecessor normalized constants and conditions with
$q=b+L_y<1$, $qR+G\le R$, and
$\mu(q\kappa+L_x)\le\kappa$.

Additionally require finite normalized constants $H_x,H_y\ge0$ such that

$$
\|D_xg_t(x,y)-D_xg_t(x,y')\|
\le H_x\|y-y'\|,
$$

$$
\|D_yg_t(x,y)-D_yg_t(x,y')\|
\le H_y\|y-y'\|.
\tag{D2}
$$

For raw base/fiber scales $X_*,Y_*$, normalize
$H_x=X_*H_{x,raw}$ and $H_y=Y_*H_{y,raw}$.

## Derivative bunching and recurrence

Define

$$
\beta=\mu q,
\qquad
c_D=\mu(H_y\kappa+H_x),
\tag{D3}
$$

and require

$$
\beta<1.
\tag{D4}
$$

For two $C^1$ graph iterates, let
$\delta_n=\|h_n-\widehat h_n\|_\infty$ and
$d_n=\|Dh_n-D\widehat h_n\|_\infty$. The executable theorem must expose

$$
\delta_n\le q^n\delta_0,
\qquad
d_{n+1}\le\beta d_n+c_D\delta_n.
\tag{D5}
$$

Hence

$$
d_n\le
\beta^n d_0+c_D\delta_0
\sum_{j=0}^{n-1}\beta^{n-1-j}q^j.
\tag{D6}
$$

Both terms tend to zero when $q,\beta<1$. Uniform convergence of graphs and derivatives makes the unique Lipschitz fixed graph $C^1$.

## Boundary counterexample and controls

At $q\mu=1$, take the local map $(x,y)\mapsto(qx,qy)$ with $0<q<1$. Every graph $h_c(x)=c|x|$ satisfies $h_c(qx)=qh_c(x)$ and is Lipschitz but not $C^1$ at zero when $c\ne0$. Thus equality does not force C1 regularity or uniqueness in the Lipschitz local invariant class.

Controls cover strict pass, predecessor failure, $\beta=1$ and above, zero derivative variation, exact recurrence including $n=0$, $q=0$, normalization invariance, invalid inputs, and dimension nonselection.

## Ceiling

The result is a quantitative affine triangular $C^1$ theorem. It does not handle coupled-base derivatives, nonaffine inverse derivatives, chart boundaries, $C^2$ or $C^{r-1}$ regularity, empirical uniform bounds, consciousness, or dimension 4--6 selection.

