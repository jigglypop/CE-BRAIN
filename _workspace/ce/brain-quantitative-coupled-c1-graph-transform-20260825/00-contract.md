# Quantitative coupled-base C1,1 graph-transform contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-quantitative-coupled-graph-transform-20260825`

## Objective

Promote the affine coupled-base Lipschitz invariant graph to C1 under explicit C1,1 class invariance and derivative bunching. Unlike the triangular theorem, graph-dependent base preimages and inverse Jacobians must be compared quantitatively.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | New gap |
|---|---|---|---|---|
| Coupled Lipschitz graph | predecessor C1--C3; focused 26/26 | PASS | $\alpha>0$, tube/slope gates and $Q<1$ give a unique Lipschitz graph. | No derivative class or inverse-Jacobian difference bound. |
| Triangular C1 | C1 and nonaffine successors | PASS | Graph-independent preimages need $q\mu<1$. | Coupled preimages differ between graphs. |
| General smooth route | ledger CE-GRAPH-004 | OPEN | Coupled derivative terms were explicitly unclosed. | Requires at least C1,1 control. |

## Norm and regularity convention

Use the predecessor normalized affine coupled chart

$$
x'=A_tx+a_t+f_t(x,y),\qquad
y'=B_ty+g_t(x,y).
\tag{J1}
$$

The product-state norm is $\|(u,v)\|_\oplus=\|u\|+\|v\|$. Assume $f_t,g_t$ are C1 with partial blocks bounded by the predecessor constants and with all first-derivative blocks jointly Lipschitz:

$$
\|D_\bullet f_t(z)-D_\bullet f_t(z')\|
\le H_f\|z-z'\|_\oplus,
$$

$$
\|D_\bullet g_t(z)-D_\bullet g_t(z')\|
\le H_g\|z-z'\|_\oplus,
\tag{J2}
$$

for $\bullet=x,y$. $H_f,H_g$ are declared dimensionless constants in the already normalized chart. Work on graph families with
$\|h\|_\infty\le R$, $\|Dh\|_\infty\le\kappa$, and
$\operatorname{Lip}(Dh)\le\Lambda$.

## C1,1 class invariance

Retain predecessor

$$
q=b+L_{gy},\quad
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa>0,\quad
s=q\kappa+L_{gx},
$$

and its $Q$. Define

$$
C_F=H_f(1+\kappa)^2+L_{fy}\Lambda,
\qquad
C_Y=q\Lambda+H_g(1+\kappa)^2.
\tag{J3}
$$

Then the derivative-Lipschitz output bound is

$$
\Lambda_{out}
=\frac{C_Y}{\alpha^2}
+\frac{sC_F}{\alpha^3}.
\tag{J4}
$$

Require

$$
\Lambda_{out}\le\Lambda.
\tag{J5}
$$

Equality preserves the class but is non-robust.

## Coupled derivative contraction

For two graphs at C0 distance $\delta$ and derivative distance $d$, put

$$
r_x=\frac{L_{fy}}{\alpha},qquad
Z=1+(1+\kappa)r_x,
\tag{J6}
$$

$$
A_\delta=H_fZ(1+\kappa)+L_{fy}\Lambda r_x,
$$

$$
Y_\delta=q\Lambda r_x+H_gZ(1+\kappa).
\tag{J7}
$$

The derivative recurrence constants are

$$
\beta_c=rac q\alpha+rac{sL_{fy}}{\alpha^2}
=\frac Q\alpha,
$$

$$
c_c=\frac{Y_\delta}{\alpha}
+\frac{sA_\delta}{\alpha^2}.
\tag{J8}
$$

Require $\beta_c<1$. Then

$$
\delta_{n+1}\le Q\delta_n,qquad
d_{n+1}\le\beta_c d_n+c_c\delta_n
\tag{J9}
$$

forces C1 convergence. The unique Lipschitz fixed graph is C1 and belongs to the declared C1,1 class.

## Controls and ceiling

Controls cover strict pass, C1,1 boundary, class failure, derivative bunching equality/above, predecessor failure, zero second-derivative constants, zero base coupling reduction, exact recurrence, normalized-unit invariance, invalid inputs, and dimensions 1/4/5/6/100.

At zero base coupling, $\alpha=1/\mu$, $Q=q$, and $\beta_c=q\mu$, recovering the triangular bunching boundary and its invariant $c|x|$ counterexample.

This theorem is affine coupled C1 with a C1,1 graph-class bound. It does not handle nonaffine coupled bases, local boundaries, C2 graph regularity, empirical neural constants, consciousness, or dimension selection.

