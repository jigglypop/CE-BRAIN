# Nonaffine triangular C1 extension

Status: COMPLETE

Date: 2026-08-25

## Abstract

The quantitative C1 theorem was initially stated for an affine triangular base. Re-auditing its proof shows that affine constancy is unused: graph independence supplies the same base preimage and inverse derivative for both graph comparisons. The theorem therefore extends to any C1 diffeomorphism with a uniform inverse-derivative bound. The nonaffine family $x+a\sin x$ supplies an exact analytic fixture with bound $(1-a)^{-1}$ for $0\le a<1$. Focused validation passed 10 tests, C1 regression 30, and complete graph/scale integration 155. Coupled-base derivatives, local boundaries, C2/higher regularity, and neural-data premises remain outside the result.

## 1. Affine restriction audit

For $x'=\phi_t(x)$, triangularity makes
$x=\phi_t^{-1}(x')$ independent of the graph. Differentiation gives

$$
D(\mathcal Th)(x')
=\{B_tDh+D_xg_t+D_yg_tDh\}D\phi_t^{-1}(x').
$$

When two graph transforms are subtracted at the same $x'$, the preimage and right factor are identical. Therefore the slope estimate and

$$
d_{n+1}\le q\mu d_n+\mu(H_y\kappa+H_x)\delta_n
$$

need only $\|D\phi_t^{-1}\|\le\mu$, not a constant derivative. The predecessor C1 conclusion and exact recurrence remain unchanged.

## 2. Exact nonaffine witness

For $\phi_a(x)=x+a\sin x$,

$$
1-a\le\phi_a'(x)=1+a\cos x\le1+a.
$$

If $0\le a<1$, the map is strictly increasing and proper, hence a global C1 diffeomorphism, and
$\|D\phi_a^{-1}\|_\infty\le(1-a)^{-1}$. At $a=1$, the derivative vanishes at $x=\pi$ and the uniform inverse-derivative gate fails.

With $a=1/4$, the exact helper gives $\mu=4/3$ and the declared graph fixture has bunching factor $2/3$. With $a=1/2$ and a separate zero-cross-coupling fixture, the Lipschitz graph gate still passes but C1 bunching reaches one and is correctly rejected.

## 3. Evidence and ceiling

The new fixture passed 10/10 focused tests, combined C1 regression 30/30, and complete graph/C1/scalar-tensor-scale/dimensionless integration 155/155. This removes the global nonaffine restriction for graph-independent triangular C1 bases.

It does not solve graph-dependent coupled inverse derivatives, local chart boundaries, C2 or higher derivative bunching, fit a neural chart, identify consciousness, or select 4--6 dimensions.

