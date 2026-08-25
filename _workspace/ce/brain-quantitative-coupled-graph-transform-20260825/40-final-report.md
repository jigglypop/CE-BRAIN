# Quantitative coupled-base Lipschitz graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The prior executable theorem assumed that base dynamics did not depend on the fiber. This successor admits a Lipschitz fiber-to-base perturbation of an invertible affine base and derives explicit conditions for graph-dependent base inversion, tube and slope invariance, and graph-transform contraction. The resulting factor includes the reparameterization cost and reduces exactly to the triangular factor when base coupling vanishes. Focused validation passed 26 tests, adjacent triangular regression 52, dimensionless checks 26, and graph/scale integration 101. The theorem is Lipschitz and conditional on supplied uniform constants; it is not the full smooth normal-hyperbolicity theorem or a neural-data result.

## 1. Coupled chart

Consider

$$
x'=A_tx+a_t+f_t(x,y),\qquad
y'=B_ty+g_t(x,y),
$$

with $\|A_t^{-1}\|\le\mu$, $\|B_t\|\le b$ and normalized Lipschitz constants $L_{fx},L_{fy},L_{gx},L_{gy}$. Graphs have radius $R$ and slope at most $\kappa$. Put

$$
q=b+L_{gy},\qquad
\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa.
$$

If $\alpha>0$, the fixed-point map through $A_t^{-1}$ has factor
$\mu(L_{fx}+L_{fy}\kappa)<1$, so each graph-dependent base map has a unique inverse. Its lower Lipschitz bound is $\alpha$.

## 2. Invariance and contraction

The graph family is preserved when

$$
qR+G\le R,
\qquad
q\kappa+L_{gx}\le\kappa\alpha.
$$

At a common output base point, the preimages associated with two graphs at distance $\delta$ differ by at most $(L_{fy}/\alpha)\delta$. Therefore the graph transform has factor

$$
Q=q+(q\kappa+L_{gx})\frac{L_{fy}}{\alpha}.
$$

The strict condition $Q<1$ gives a unique invariant Lipschitz graph family. The apparatus reports all four margins, treating zero tube or slope margin as theorem-valid but non-robust, while $\alpha=0$ and $Q=1$ are non-certificates.

At $\alpha=0$, the example $A=I$, $f(x,y)=-x$ makes the base map constant. At $Q=1$, the uncoupled identity fiber admits nonunique constant invariant graphs. These are complete boundary controls for this sufficient theorem.

## 3. Relation to the triangular theorem

When $L_{fx}=L_{fy}=0$, $\alpha=1/\mu$ and $Q=q$. The slope condition becomes

$$
\mu(q\kappa+L_{gx})\le\kappa,
$$

which is exactly the earlier triangular condition. Thus the new theorem genuinely extends that executable subcase rather than replacing it with a different convention.

The same passing constants accept base dimensions 1, 4, 5, 6, and 100. They preserve a supplied dimension and do not select a consciousness dimension.

## 4. Evidence and limits

The exact certificate passed 26/26 focused tests, 52/52 adjacent triangular tests, 26/26 dimensionless tests, and 101/101 graph/scale integration tests. Cross-unit constants $L_{fy}$, $L_{gx}$, and $\kappa$ are normalized before entering $\alpha,Q$, so all contraction cores are dimensionless.

The affine base is global and the theorem is Lipschitz. A nonaffine or local bounded chart needs an independently certified inverse and boundary mapping. A $C^{r-1}$ manifold needs derivative graph transforms, invariant splitting, and bunching. No such constants are estimated from a brain trajectory; no consciousness identification or 4--6 selection follows.

