# Quantitative C1 triangular graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The predecessor gave a quantitative Lipschitz invariant graph but left smooth promotion qualitative. In an affine triangular $C^1$ chart, this run derives an explicit derivative bunching condition $q\mu<1$ and a value/derivative iteration recurrence. Finite derivative-variation bounds control the off-diagonal forcing from graph-value differences into derivative differences. Uniform convergence of graph iterates and their derivatives makes the unique Lipschitz fixed graph $C^1$. Focused validation passed 20 tests, triangular regression 46, dimensionless checks 28, and graph/scale integration 123. The theorem is conditional on supplied uniform constants and does not reach coupled, nonaffine, local-boundary, $C^{r-1}$, or empirical neural claims.

## 1. Derivative transform

For the affine triangular chart

$$
x'=A_tx+a_t,
\qquad y'=B_ty+g_t(x,y),
$$

the base preimage $x=A_t^{-1}(x'-a_t)$ is graph-independent. Differentiation gives

$$
D(\mathcal Th)(x')
=\{B_tDh+D_xg_t+D_yg_tDh\}A_t^{-1}.
$$

The predecessor slope condition keeps this derivative norm at most $\kappa$.

Assume the partial derivatives vary in the fiber direction with normalized bounds $H_x,H_y$. For two graph iterates define their value and derivative distances $\delta_n,d_n$. Subtraction of the derivative transforms yields

$$
\delta_{n+1}\le q\delta_n,
\qquad
d_{n+1}\le\beta d_n+c_D\delta_n,
$$

where

$$
\beta=q\mu,
\qquad c_D=\mu(H_y\kappa+H_x).
$$

## 2. C1 promotion theorem

If the complete triangular Lipschitz gate passes and $\beta<1$, iteration gives

$$
d_n\le\beta^n d_0+c_D\delta_0
\sum_{j=0}^{n-1}\beta^{n-1-j}q^j.
$$

Because $q,\beta<1$, the right side tends to zero. The repeated-root case is $nq^{n-1}$ and also tends to zero. Starting from C1 graphs, the graph iterates and derivatives converge uniformly; the uniform derivative-limit theorem implies that the already unique Lipschitz fixed graph is C1.

At the equality boundary, the local linear map $(x,y)\mapsto(qx,qy)$ has $q\mu=1$ and invariant graphs $h_c(x)=c|x|$. These are Lipschitz but not differentiable at zero for $c\ne0$. Equality therefore cannot force C1 regularity.

## 3. Normalization, evidence, and ceiling

Raw derivative-variation constants normalize as $H_x=X_*H_{x,raw}$ and $H_y=Y_*H_{y,raw}$, making $\beta,c_D$ dimensionless. The exact apparatus passed 20/20 focused tests, 46/46 triangular regression tests, 28/28 dimensionless tests, and 123/123 graph/scale integration tests. Dimensions 1, 4, 5, 6, and 100 pass under the same constants, so the theorem preserves rather than selects dimension.

The result replaces one qualitative bootstrap step by an explicit C1 subtheorem. Coupled-base differentiation, nonaffine inverse derivatives, local chart boundaries, $C^2$ and higher bunching, a fitted neural vector field, consciousness identification, and 4--6 selection remain unproved.

