# Matched local nonaffine coupled-base C2 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The overflow-local nonaffine coupled C2 theorem is upgraded to exact
full-forward/backward invariance by adding independently certified forward and
inverse contacts and a boundary-compatible graph class. Zero graph-boundary
and fiber-boundary residuals make that class invariant. A boundary-fixed cubic
with nonzero fiber-to-base coupling gives an exact witness with derivative gap
$39/40$. The result is conditional compact-domain mathematics, not a neural,
consciousness, or dimension-selection result.

## 1. Introduction

Inverse coverage lets the local transform evaluate every requested output
point, but it does not retain every input point. Exact matched invariance needs
both directions. In a graph-dependent base, exact domain equality is still
not enough by itself: the graph class must also survive at the boundary.

## 2. Definitions and notation

Let $U_t,U_{t+1}$ be compact base balls. Define the boundary-anchored graph
class by

$$
\mathcal H_0
=\{h:h|_{\partial U_t}=0\}
$$

intersected with every value, slope, Hessian, and C2,1 bound of the local
predecessor. The four independently supplied matched quantities are the exact
uniform inverse and forward radii, the graph-boundary value bound, and the
fiber-boundary forcing bound.

## 3. Adopted axioms

**Axiom M1: exact domain contacts.** The actual graph-dependent maps satisfy

$$
R_{\rm pre}^{\rm exact}=R_t,
\qquad
R_{\rm fwd}^{\rm exact}=R_{t+1}.
$$

**Axiom M2: boundary compatibility.** Every admissible graph vanishes on
$\partial U_t$, and $g_t(x,0)=0$ there. These are uniform functional premises,
not conclusions inferred from samples.

## 4. Conditional theorem and proof

**Theorem M3.** Under Axioms M1--M2 and every overflow-local nonaffine coupled
C2 gate, the graph transform preserves $\mathcal H_0$, has the same exact
C0/C1/C2 recurrence, and its unique C2 graph is fully forward/backward
invariant over the matched domains.

**Proof.** The forward contact certifies
$F_h(U_t)\subseteq U_{t+1}$. The inverse contact certifies
$F_h^{-1}(U_{t+1})\subseteq U_t$; applying $F_h$ gives the reverse inclusion.
Thus $F_h(U_t)=U_{t+1}$ for each admissible graph. A diffeomorphism between
compact balls maps boundary to boundary. If $x'\in\partial U_{t+1}$ and
$x=F_h^{-1}(x')$, Axiom M2 gives

$$
(\mathcal Th)(x')=B_t h(x)+g_t(x,h(x))=0.
$$

Hence the transform preserves the anchored class. Domain restriction changes
no differential coefficient, so the predecessor contraction and
upper-triangular recurrence prove the unique C2 fixed graph. $\square$

Exact equality reaches compact boundaries. Therefore both domain-contact
margins are zero and domain-contact robust interior is structurally false,
even when every differential margin is strict.

## 5. Exact derivation and controls

On the unit interval take

$$
F_h(x)=x+a x(1-x^2)+\varepsilon h(x),
\qquad h(-1)=h(1)=0.
$$

If $\|h'\|\le\kappa$, then

$$
F_h'(x)
=1+a-3ax^2+\varepsilon h'(x)
\ge1-2a-\varepsilon\kappa.
$$

At $a=1/100$, $\varepsilon=1/100$, and $\kappa=1/2$,

$$
1-2a-\varepsilon\kappa=\frac{39}{40},
\qquad
\mu=\frac{50}{49},
\qquad
\|DF_h^{-1}\|\le\frac{40}{39},
$$

and $F_h(\pm1)=\pm1$. Every admissible $F_h$ is therefore strictly increasing
and maps the interval exactly onto itself. With $Y_h=h/10$ the graph boundary
also remains zero. The differential coefficients include

$$
H_\phi=T_\phi=\frac3{50},
\quad
\Xi_{\rm out}=\frac{4085248}{30074733},
\quad
\beta_{2,c}=\frac{6272}{59319},
$$

$$
c_{21,c}=\frac{37888}{3855735},
\qquad
c_{20,c}=\frac{1021312}{751868325}.
$$

At $\varepsilon=0$, the witness reduces to the graph-independent matched
cubic. Without graph anchoring, a constant graph moves the base endpoint.
Without zero fiber-boundary forcing, the transform exits the anchored class.
Removing forward contact leaves only the valid overflow theorem.

## 6. Observation comparison

No measured chart, neural vector field, boundary observable, or empirical
constant enters this run. The result cannot identify a brain manifold,
consciousness, or a preferred dimension.

## 7. Incomplete tasks and limitations

The differential/domain hierarchy is now closed through matched local
nonaffine coupled C2 under explicit uniform premises. C3 and higher regularity
still needs fourth-order map moduli, a higher graph class, and a new
Faà di Bruno recurrence. Concrete brain fields, empirical uniformity,
interventions, and the proposed 4--6 dimension identification remain open.

## 8. Reproducibility

Focused, adjacent, dimensionless, and integration results are recorded in
`31-validation.md`. Exact implementation paths are recorded in
`30-implementation.md`. No external data or network action was used.

## 9. References

The formal dependencies are the final-gated overflow-local nonaffine coupled
C2 and matched graph-independent nonaffine C2 repository runs, both accessed
on 2026-08-25.
