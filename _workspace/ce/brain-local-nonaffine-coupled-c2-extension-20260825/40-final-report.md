# Local nonaffine coupled-base C2 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The global nonaffine coupled C2 theorem requires a graph-dependent inverse but
does not by itself certify that this inverse stays inside a local chart. A
uniform inverse-image radius gate closes that domain seam without changing any
differential coefficient. A sine-perturbed expanding base with nonzero fiber
coupling gives an exact strict witness with domain margin $2/5$. The result is
a conditional backward-covered local C2 theorem, not a matched full-forward,
neural, consciousness, or dimension-selection result.

## 1. Introduction

On a global base space, the transform may evaluate $F_h^{-1}$ wherever needed.
On a compact local chart, every such evaluation must first be shown to return
to the input domain. This issue is sharper in the coupled model because
$F_h=\phi+f(\cdot,h)$ varies with the graph; coverage of $\phi^{-1}$ is not the
required statement.

## 2. Definitions and notation

Let $U_t=\overline B(c_t,R_t)$ and
$U_{t+1}=\overline B(c_{t+1},R_{t+1})$. The normalized uniform coverage
margin is

$$
m_{\rm dom}=\frac{R_t-R_{\rm pre}}{X_0},
$$

where

$$
R_{\rm pre}\ge
\sup_h\sup_{x'\in U_{t+1}}
\|F_{t,h}^{-1}(x')-c_t\|.
$$

## 3. Adopted axiom

**Axiom L1: uniform local inverse collar.** Every admissible $F_{t,h}$ has the
selected C2 inverse branch on an open collar of $U_{t+1}$, all differential
bounds of the global theorem hold uniformly on the relevant collars, and
$R_{\rm pre}\le R_t$.

This is a supplied local-domain premise. The certificate checks its declared
radius bound; it does not infer the premise from point samples.

## 4. Conditional theorem and proof

**Theorem L2.** If Axiom L1 and every gate of the global nonaffine coupled C2
theorem hold, the local graph transform is well-defined on $U_{t+1}$, has the
same exact value/derivative/Hessian recurrence, and has a unique C2 invariant
graph family in the backward-covered overflow sense.

**Proof.** Axiom L1 places $F_h^{-1}(x')$ inside $U_t$ for every admissible
graph and every $x'\in U_{t+1}$. Hence all $Y_h,P_h,R_h,N_h,J_h$ evaluations
used by the global proof are defined inside their collars. Restricting their
domains changes no chain-rule identity or uniform bound. The global
contraction and upper-triangular C0/C1/C2 recurrence therefore apply without
new coefficients. Completeness of the restricted graph class gives the
unique fixed graph. The image identity is

$$
\operatorname{graph}(h_{t+1})
=\Phi_t(\operatorname{graph}(h_t))
\cap(U_{t+1}\times Y),
$$

which proves overflow invariance but not forward retention. $\square$

## 5. Exact derivation and controls

For

$$
F_h(x)=\lambda x+a\sin x+\varepsilon h(x),
\qquad |h(x)|\le R_y,
$$

co-Lipschitzness gives

$$
R_{\rm pre}
=\frac{R_{t+1}+\varepsilon R_y}{\lambda-a}.
$$

At $\lambda=2$, $a=1/4$, $\varepsilon=1/20$, and unit radii,

$$
\mu=\frac47,\qquad \|DF_h^{-1}\|\le\frac{40}{69},\qquad
R_{\rm pre}=\frac35,\qquad
m_{\rm dom}=\frac25,qquad
\beta_{2,c}=\frac{7520}{109503}.
$$

The coupling is nonzero. At $\varepsilon=0$, the coverage bound reduces to
the graph-independent expression $\mu R_{t+1}$.

The rejected shortcut has a complete counterexample. For
$\phi(x)=2x$, $f(x,y)=y$, and $h=-2$ on unit intervals,
$\phi^{-1}(1)=1/2$ lies inside but $F_h^{-1}(1)=3/2$ lies outside. Separately,
$\phi(x)=2x$ shows that inverse coverage does not imply full forward
retention.

## 6. Observation comparison

No measured chart, neural vector field, or observational constant enters this
run. Consequently the theorem cannot be compared numerically with brain data
and does not identify consciousness or a preferred dimension.

## 7. Incomplete tasks and limitations

Exact matched full-forward composition remains open because it requires a
boundary-compatible admissible graph class and uniform forward as well as
inverse contact for every graph-dependent base map. C3 and higher regularity,
a concrete brain field, held-out uniform constants, and the proposed 4--6
dimension identification also remain open.

## 8. Reproducibility

The focused, adjacent, dimensionless, and integration results are recorded in
`31-validation.md`. The exact implementation and test paths are recorded in
`30-implementation.md`. No external data or network action was used.

## 9. References

The formal dependencies are the final-gated global nonaffine coupled C2 and
overflow-local graph-independent nonaffine C2 repository runs, both accessed
on 2026-08-25.
