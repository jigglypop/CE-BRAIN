# Quantitative nonaffine coupled-base C1 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The affine coupled C1 theorem is extended to a graph-independent nonaffine
base diffeomorphism. Base curvature changes the one-graph Jacobian class and,
because coupled graphs have different preimages, adds a separate value-level
Jacobian difference. Both terms are derived explicitly and reduce exactly at
zero curvature. The result supplies the necessary C1 predecessor for
nonaffine coupled C2; it is not a neural or consciousness result.

## 1. Base curvature

For

$$
F_h(x)=\phi_t(x)+f_t(x,h(x)),
$$

assume $\phi_t$ is co-Lipschitz with inverse bound $\mu$ and
$\|D^2\phi_t\|\le H_\phi$. The coupled Lipschitz constants
$\alpha,Q,r_x,Z$ are unchanged. The base-Jacobian modulus becomes

$$
C_F^{\rm na}
=H_\phi+H_f(1+\kappa)^2+L_{fy}\Lambda.
$$

Consequently

$$
\Lambda_{\rm out}^{\rm na}
=\frac{C_Y}{\alpha^2}
+\frac{sC_F^{\rm na}}{\alpha^3}.
$$

## 2. Two-graph recurrence

Different graphs have preimages separated by at most $r_x\delta$. Hence

$$
\|D\phi_t(x_1)-D\phi_t(x_2)\|
\le H_\phi r_x\delta,
$$

which changes the value coefficient to

$$
A_\delta^{\rm na}
=H_\phi r_x+H_fZ(1+\kappa)+L_{fy}\Lambda r_x.
$$

The derivative recurrence is

$$
d_{n+1}
\le\frac Q\alpha d_n
+\left(\frac{Y_\delta}{\alpha}
+\frac{sA_\delta^{\rm na}}{\alpha^2}\right)\delta_n.
$$

Class invariance and strict $Q/\alpha<1$ therefore yield a unique C1 graph.

## 3. Exact witness and reduction

For $\phi_{\lambda,a}(x)=\lambda x+a\sin x$,

$$
\mu=(\lambda-a)^{-1},
\qquad
H_\phi=a.
$$

At $(\lambda,a)=(1001/1000,1/1000)$ and the strict predecessor fixture,

$$
C_F^{\rm na}=\frac{147}{2000},
\quad
\Lambda_{\rm out}^{\rm na}=\frac{69388}{253265},
\quad
A_\delta^{\rm na}=\frac{351}{18500},
$$

$$
\beta_1=\frac{308}{1369},
\qquad
c_{10}^{\rm na}=\frac{41212}{1266325}.
$$

At $H_\phi=0$, every coefficient is exactly the affine coupled C1 result.

## 4. Evidence ceiling

This closes global graph-independent-base nonaffine coupled C1. Nonaffine
coupled C2 still requires a modulus for $D^2\phi_t$ and the resulting modified
Hessian terms. Local domain composition, C3+, measured neural dynamics,
consciousness, and dimension selection remain open. Validation counts are
recorded in `31-validation.md`; no external source or empirical input was used.

## References

Formal dependencies are the final-gated affine coupled C1 and nonaffine
triangular calculus repository runs.

