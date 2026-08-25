# Nonaffine triangular C1 extension contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-quantitative-c1-graph-transform-20260825`

## Objective

Audit whether the predecessor's affine-base restriction is mathematically necessary. Extend the same exact C1 bunching theorem to a graph-independent nonaffine $C^1$ diffeomorphism base when its inverse derivative has a uniform bound. Supply one exact analytic nonaffine fixture.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | Re-audit question |
|---|---|---|---|---|
| Triangular Lipschitz graph | predecessor and graph run | PASS | Base inverse is graph-independent and has Lipschitz upper $\mu$. | Does differentiation require affine base? |
| Affine triangular C1 | predecessor D1--D3; focused 20/20 | PASS | $q\mu<1$ gives the derivative recurrence and C1 fixed graph. | Which step uses constant $D\phi^{-1}$? |
| Nonaffine route | predecessor `12-routes.md` | OPEN | Certified inverse derivatives were listed as missing. | Is a uniform inverse-derivative bound sufficient? |

## Frozen generalized base

Replace $x'=A_tx+a_t$ by

$$
x'=\phi_t(x),
\tag{N1}
$$

where each $\phi_t:X\to X$ is a $C^1$ diffeomorphism and

$$
\sup_{t,x'}\|D\phi_t^{-1}(x')\|\le\mu.
\tag{N2}
$$

Retain the triangular fiber equation and every predecessor Lipschitz, tube, slope, derivative-variation, and strict bunching condition.

## Generalized theorem

For the graph-independent preimage $x=\phi_t^{-1}(x')$,

$$
D(\mathcal Th)(x')
=\{B_tDh(x)+D_xg_t(x,h(x))+D_yg_t(x,h(x))Dh(x)\}
D\phi_t^{-1}(x').
\tag{N3}
$$

When comparing two graphs at the same $x'$, both use the same $x$ and the same right factor. Thus the predecessor recurrence, $\beta=q\mu$, $c_D=\mu(H_y\kappa+H_x)$, and C1 conclusion are unchanged. No derivative-Lipschitz bound for $D\phi^{-1}$ is needed at the C1 level because no two base points are compared in this recurrence.

## Exact nonaffine fixture

For

$$
\phi_a(x)=x+a\sin x,
\qquad 0\le a<1,
\tag{N4}
$$

$1-a\le\phi_a'(x)\le1+a$. The map is strictly increasing and proper, hence a global $C^1$ diffeomorphism, and

$$
\|D\phi_a^{-1}\|_\infty\le\frac1{1-a}.
\tag{N5}
$$

The executable helper accepts exact $a\in[0,1)$ and returns this exact rational bound. At $a=1$, the derivative vanishes at odd multiples of $\pi$, so the strict inverse bound is unavailable.

## Ceiling

This removes affine dependence only for graph-independent triangular C1 dynamics. Coupled-base inverse derivatives, local boundary mapping, C2/higher regularity, actual neural charts, consciousness, and dimension selection remain open.

