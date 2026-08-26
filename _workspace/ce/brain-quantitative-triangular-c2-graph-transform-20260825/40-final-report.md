# Quantitative affine triangular C2 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The prior triangular theorem established a unique C1 invariant graph but left
second derivatives qualitative. This successor differentiates the graph
transform twice on a normalized affine-base chart. An invariant Hessian class,
a fiber modulus for the map Hessian, and strict $q\mu^2<1$ close an exact
three-level recurrence. The equality case has an invariant C1/non-C2 witness,
so strictness is necessary. Exact validation passed 22 focused and 200
integrated tests. The result is a conditional mathematical theorem, not a
neural or consciousness finding.

## 1. Definitions and assumptions

Consider

$$
x'=A_tx+a_t,\qquad y'=B_ty+g_t(x,y),
$$

in a normalized product chart. Let $P_t=A_t^{-1}$ with $\|P_t\|\le\mu$.
The passing predecessor supplies $q<1$, graph slope $\|Dh\|\le\kappa$,
strict first-order bunching $q\mu<1$, and the exact value/derivative
recurrence. The C2 graph class additionally has $\|D^2h\|\le\Lambda_2$.
The map obeys

$$
\|D^2g_t\|\le K_2,
\qquad
\|D^2g_t(x,y_1)-D^2g_t(x,y_2)\|
\le K_3\|y_1-y_2\|.
$$

These constants are dimensionless only in the declared normalized chart.

## 2. Hessian-class lemma

For $S_h(x)=B_th(x)+g_t(x,h(x))$, put $J_h=(I,Dh)$. The affine base gives

$$
D^2(\mathcal Th)[u,v]=D^2S_h[P_tu,P_tv],
$$

while the second-order chain rule gives

$$
D^2S_h=(B_t+D_yg_t)D^2h+D^2g_t[J_h,J_h].
$$

Since $\|B_t+D_yg_t\|\le q$ and $\|J_h\|\le1+\kappa$,

$$
\Lambda_{2,\mathrm{out}}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}.
$$

Thus $\Lambda_{2,\mathrm{out}}\le\Lambda_2$ preserves the declared class.

## 3. C2 theorem and proof

**Conditional theorem.** If the predecessor C1 certificate passes,
$\Lambda_{2,\mathrm{out}}\le\Lambda_2$, $K_3<\infty$, and

$$
\beta_2=q\mu^2<1,
$$

then the unique invariant Lipschitz graph is C2. For value, derivative, and
Hessian distances $\delta_n,d_n,e_n$,

$$
\delta_{n+1}\le q\delta_n,
$$

$$
d_{n+1}\le\beta_1d_n+c_{10}\delta_n,
$$

$$
e_{n+1}\le\beta_2e_n+c_{21}d_n+c_{20}\delta_n,
$$

where

$$
c_{21}=2\mu^2K_2(1+\kappa),
\qquad
c_{20}=\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}.
$$

Proof. Triangularity makes the two graph preimages identical. Splitting the
first Hessian term gives $qe+K_2\Lambda_2\delta$. Adding and subtracting the
second map Hessian evaluated on the other graph Jacobian gives
$2K_2(1+\kappa)d+K_3(1+\kappa)^2\delta$. Two inverse-base arguments multiply
the sum by $\mu^2$, producing the third recurrence. The resulting nonnegative
upper-triangular recurrence has diagonal factors $q,\beta_1,\beta_2<1$.
Repeated substitution sends value, derivative, and Hessian differences to
zero. Uniform convergence through second derivatives therefore makes the
unique fixed graph C2. □

## 4. Boundary and reduction

When $K_2=K_3=0$, the Hessian recurrence reduces exactly to
$e_{n+1}\le q\mu^2e_n$. Equality cannot pass. For

$$
x'=x/2,\qquad y'=y/4,
$$

one has $q\mu=1/2$ but $q\mu^2=1$. The local family
$h_c(x)=cx|x|$ is invariant and C1, yet is not C2 at zero for $c\ne0$.

## 5. Apparatus and evidence ceiling

The implementation returns exact declared-input implications and preserves
dimensions $1,4,5,6,100$. This does not select a dimension. It does not supply
a coupled/nonaffine/local C2 chart, C3 or higher bounds, a neural vector field,
measured derivative constants, consciousness, or a biological interpretation.

## 6. Reproducibility

The focused test is `tests/test_quantitative_c2_graph_transform.py`. The
required validation commands and raw counts are recorded in `31-validation.md`.

## References

The only formal dependency is the repository's final-gated quantitative
triangular C1 predecessor run; no external empirical source is used.
