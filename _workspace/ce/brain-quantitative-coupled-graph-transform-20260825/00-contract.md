# Quantitative coupled-base graph-transform contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-quantitative-nonlinear-graph-transform-20260825`

## Objective

Replace the predecessor's triangular base-independence by an explicit Lipschitz fiber-to-base coupling in a rigorous affine-base subcase. The result is a Lipschitz invariant-graph theorem, not the full $C^{r-1}$ normally hyperbolic manifold theorem and not a brain-data claim.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | No-retry condition |
|---|---|---|---|---|
| Triangular graph transform | predecessor G1--G2; focused 26/26 | PASS | Explicit tube, slope, contraction, uniqueness, and tracking for base independent of fiber. | Recover exactly when base coupling is zero. |
| General coupled base | predecessor `12-routes.md`, CE-GRAPH-004 | OPEN | Same-base proof is unavailable once base depends on fiber. | Do not reuse triangular $q$ as the coupled transform factor. |
| Smooth normal hyperbolicity | parent Theorem 9 | CONDITIONAL | Higher regularity needs invariant splitting and bunching. | Do not promote a Lipschitz subcase to $C^{r-1}$. |

## Frozen chart and normalized constants

On finite-dimensional base Banach space $X$ and complete fiber $Y$, use

$$
x'=A_tx+a_t+f_t(x,y),\qquad
y'=B_ty+g_t(x,y),
\tag{C1}
$$

where $A_t$ is bijective and $\|A_t^{-1}\|\le\mu$. Uniformly,

$$
\|f_t(x,y)-f_t(x',y')\|
\le L_{fx}\|x-x'\|+L_{fy}\|y-y'\|,
$$

$$
\|g_t(x,0)\|\le G,\qquad
\|g_t(x,y)-g_t(x',y')\|
\le L_{gx}\|x-x'\|+L_{gy}\|y-y'\|,
$$

and $\|B_t\|\le b$. Normalize positive scales $X_*,Y_*$ by
$R=R_{raw}/Y_*$, $G=G_{raw}/Y_*$,
$L_{fy}=L_{fy,raw}Y_*/X_*$,
$L_{gx}=L_{gx,raw}X_*/Y_*$, and
$\kappa=\kappa_{raw}X_*/Y_*$. The constants $\mu,b,L_{fx},L_{gy}$ are dimensionless.

## Exact sufficient conditions

Put

$$
q=b+L_{gy},\qquad
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa,
\tag{C2}
$$

and require

$$
\alpha>0,
\tag{C3}
$$

$$
qR+G\le R,
\tag{C4}
$$

$$
q\kappa+L_{gx}\le\kappa\alpha.
\tag{C5}
$$

For two graphs at uniform distance $\delta$, their reparameterized base preimages differ by at most $(L_{fy}/\alpha)\delta$. Therefore the graph transform factor is

$$
Q=q+(q\kappa+L_{gx})\frac{L_{fy}}{\alpha},
\qquad Q<1.
\tag{C6}
$$

Expose margins $m_\alpha=\alpha$, $m_R=R-(qR+G)$,
$m_\kappa=\kappa\alpha-(q\kappa+L_{gx})$, and $m_Q=1-Q$.
Strict $m_\alpha,m_Q>0$ and nonnegative tube/slope margins are mandatory.

## Theorem and controls

On the complete space of radius-$R$, slope-$\kappa$ graph families, (C3) makes each graph-dependent base map bijective by the contraction mapping theorem applied through $A_t^{-1}$. Conditions (C4)--(C5) preserve tube and slope. Condition (C6) makes the graph transform a $Q$-contraction, giving a unique invariant Lipschitz graph family of the supplied base dimension.

Controls must cover strict pass, boundary tube/slope, $\alpha=0$, $Q=1$, each independent failure, zero coupling recovery of the triangular formulas, exact unit rescaling, invalid inputs, and nonselection across dimensions 1/4/5/6/100.

## Ceiling

The run does not provide higher differentiability, nonaffine base global inversion, local chart boundary handling, source-locked uniform constants, a neural manifold, consciousness identification, or dimension 4--6 selection.

