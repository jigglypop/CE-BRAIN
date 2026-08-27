# Constructive affine-fiber mathematics

Status: COMPLETE

## Setup

Let $Z$ be a compact $C^1$ manifold, $P:Z\to Z$ a $C^1$ diffeomorphism,
$c\in C^1(Z,\mathbb R^m)$, and $A\in\mathbb R^{m\times m}$ with
$\|A\|_2\le q<1$.  The circuit update is

$$
\Phi(z,y)=\bigl(Pz,Ay+c(z)\bigr).
$$

The graph and weights determine the dependency pattern and the concrete objects
$P,A,c$.  The invariant graph below is not an additional input.

## C1 — explicit construction of the invariant graph

**[Theorem C1].** The series

$$
h(z)=\sum_{k=1}^{\infty}A^{k-1}c(P^{-k}z)
\tag{C1}
$$

converges uniformly to a continuous function and is the unique bounded solution
of

$$
h(Pz)=Ah(z)+c(z).
\tag{C2}
$$

Consequently $M=\{(z,h(z)):z\in Z\}$ is a compact closed invariant graph.

**Proof.** Compactness gives $C_0=\|c\|_\infty<\infty$, and the $k$th term is
bounded by $q^{k-1}C_0$.  The Weierstrass test gives uniform convergence and
continuity.  Reindexing the uniformly convergent series gives

$$
h(Pz)=c(z)+\sum_{k=2}^{\infty}A^{k-1}c(P^{-(k-1)}z)=c(z)+Ah(z).
$$

Thus $\Phi(z,h(z))=(Pz,h(Pz))$.  The graph is the continuous image of compact
$Z$, hence compact and closed in the Hausdorff ambient space.  If bounded $g$
also satisfies (C2), then $d=g-h$ satisfies $d(z)=A^nd(P^{-n}z)$.  Therefore
$\|d\|_\infty\le q^n\|d\|_\infty$ for every $n$, so $d=0$.  $\square$

## C2 — exact attraction and dimension

**[Theorem C2].** For $z_{n+1}=Pz_n$ and $y_{n+1}=Ay_n+c(z_n)$,

$$
y_n-h(z_n)=A^n\bigl(y_0-h(z_0)\bigr),
\tag{C3}
$$

and hence

$$
\|y_n-h(z_n)\|\le q^n\|y_0-h(z_0)\|.
\tag{C4}
$$

**Proof.** Put $e_n=y_n-h(z_n)$.  Equation (C2) gives
$e_{n+1}=Ay_n+c(z_n)-h(Pz_n)=Ae_n$.  Induction yields (C3), and the norm bound
yields (C4).  Once C3 below establishes $h\in C^1$, the map
$e:Z\to Z\times\mathbb R^m$, $e(z)=(z,h(z))$, is a $C^1$ embedding with inverse
the first-coordinate projection.  Therefore $\dim M=\dim Z$.  $\square$

## C3 — differentiability and conjugacy

Let

$$
\kappa=\sup_{z\in Z}\|DP^{-1}_z\|<\infty,
\qquad q\kappa<1.
$$

**[Theorem C3].** The invariant graph is $C^1$ and

$$
Dh_z=\sum_{k=1}^{\infty}
A^{k-1}Dc_{P^{-k}z}DP^{-k}_z.
\tag{C5}
$$

Moreover $\Phi|_M$ is conjugate to $P$.

**Proof.** The chain rule gives the displayed derivative for every partial sum.
Because $\|DP^{-k}_z\|\le\kappa^k$, the $k$th derivative term is bounded by

$$
q^{k-1}\|Dc\|_\infty\kappa^k
=\kappa\|Dc\|_\infty(q\kappa)^{k-1}.
$$

The derivative series converges uniformly in a finite atlas, so termwise
differentiation proves (C5).  With $e(z)=(z,h(z))$, equation (C2) gives
$\Phi\circ e=e\circ P$, which is the conjugacy.  $\square$

## C4 — exact continuous-time lift and restricted vector field

### Dimensionless gate

Take the state coordinates $z,y,h(z)$ in fixed declared state units (or normalize
each coordinate by its reference scale before applying the formulas).  Then $A$
is a dimensionless one-step gain, $\Delta$ and $t$ have time dimension, and
$\Lambda=-\Delta^{-1}\log A$ has inverse-time dimension.  Consequently every
transcendental argument used here is dimensionless:

| core argument | dimensions | gate |
|---|---:|---|
| eigenvalues of $A$ in $\log A$ | $1$ | PASS |
| $-\Lambda t$ in $e^{-\Lambda t}$ | $T^{-1}T=1$ | PASS |
| $-\Lambda\Delta$ in $e^{-\Lambda\Delta}=A$ | $T^{-1}T=1$ | PASS |

The validation fixture likewise uses an angular coordinate in
radians, hence a dimensionless argument.  This check establishes dimensional
consistency only; it is not evidence that the circuit class is biologically
realized.

Assume $P=\rho_\Delta$ is the time-$\Delta$ map of a supplied complete $C^1$
vector field $f$ on $Z$.  Assume also that $A$ is symmetric positive definite
with spectrum in $(0,1)$ and set

$$
\Lambda=-\Delta^{-1}\log_{\rm principal}A\succ0.
\tag{C6}
$$

Define

$$
F(z,y)=\left(f(z),Dh_zf(z)-\Lambda(y-h(z))\right).
\tag{C7}
$$

**[Theorem C4].** The unique flow defined explicitly by (C7) is

$$
z(t)=\rho_tz_0,
\qquad
y(t)=h(\rho_tz_0)+e^{-\Lambda t}\bigl(y_0-h(z_0)\bigr).
\tag{C8}
$$

Its time-$\Delta$ map is exactly $\Phi$.  The derived manifold $M$ is invariant
and globally fiber-wise exponentially attracting.  Its restricted vector field
is

$$
b(z,h(z))=\bigl(f(z),Dh_zf(z)\bigr).
\tag{C9}
$$

**Proof.** Let $r=y-h(z)$.  Along (C7), the chain rule gives
$\dot r=\dot y-Dh_z\dot z=-\Lambda r$, while $\dot z=f(z)$.  This proves (C8)
and uniqueness through the $C^1$ coordinate change $(z,y)\leftrightarrow(z,r)$,
even though no unnecessary Picard claim for $F$ is used.  At $t=\Delta$,
$e^{-\Lambda\Delta}=A$, and (C2) gives

$$
y(\Delta)=h(Pz)+A(y-h(z))=Ay+c(z).
$$

If $r(0)=0$, then $r(t)=0$, proving invariance and (C9).  In general,

$$
\|r(t)\|\le e^{-\lambda_{\min}(\Lambda)t}\|r(0)\|.
$$

This is fiber-wise exponential attraction.  It is not called normal
hyperbolicity without a separate tangent/normal domination bound.  $\square$

For fixed supplied $f$ and the ansatz of a constant symmetric positive fiber
generator, the principal symmetric logarithm makes $\Lambda$ unique.  The
sampled map alone does not identify a unique unrestricted real logarithm,
off-manifold vector field, or autonomous embedding.

## C5 — quantitative sensitivity

Let $(A,c)$ and $(\widetilde A,\widetilde c)$ share $P$ and satisfy
$\|A\|,\|\widetilde A\|\le q_*<1$.  Write
$\delta_A=\|A-\widetilde A\|$ and
$\delta_c=\|c-\widetilde c\|_\infty$.

**[Theorem C5].** Their invariant graphs obey

$$
\|h-\widetilde h\|_\infty
\le
\frac{\delta_c}{1-q_*}
+\frac{\|\widetilde c\|_\infty\delta_A}{(1-q_*)^2}.
\tag{C10}
$$

The same bound with $c$ and $\widetilde c$ exchanged is also valid.

**Proof.** Split the series difference into a forcing difference and a matrix
power difference.  The first geometric sum gives $\delta_c/(1-q_*)$.  For
$n\ge1$,

$$
A^n-\widetilde A^n
=\sum_{j=0}^{n-1}A^{n-1-j}(A-\widetilde A)\widetilde A^j,
$$

so $\|A^n-\widetilde A^n\|\le n q_*^{n-1}\delta_A$.  Summing
$\sum_{n\ge1}nq_*^{n-1}=(1-q_*)^{-2}$ proves (C10).  $\square$

## C6 — cost-conditioned Lyapunov metric

Freeze a continuous SPD base metric $G_Z(z)$ and Euclidean fiber cost.  Define

$$
H=\sum_{k=0}^{\infty}(A^\top)^kA^k.
\tag{C11}
$$

**[Theorem C6].** The series converges, $H\succeq I$, and

$$
H-A^\top HA=I.
\tag{C12}
$$

The pullback

$$
g_{M,z}(u,v)=G_{Z,z}(u,v)+\langle Dh_zu,H Dh_zv\rangle
\tag{C13}
$$

is a continuous SPD metric on $M$.

**Proof.** The $k$th summand has norm at most $q^{2k}$, giving convergence.
Also $u^\top Hu=\sum_{k\ge0}\|A^ku\|^2\ge\|u\|^2$.  Multiplication by
$A^\top$ and $A$ shifts the convergent series by one term, proving (C12).
Finally (C13) is continuous and its first term is strictly positive for every
nonzero tangent vector; the second is nonnegative.  Hence it is SPD.  $\square$

This metric is derived only after the base metric and fiber cost are supplied.
It is not identified from connectivity alone and is not a biological metric
without an independent measurement/cost bridge.

## Final constructive statement

For the frozen local affine-fiber circuit class, the circuit data determine the
unique invariant graph $M$, exact discrete restricted dynamics, exponential
fiber attraction and stability bounds.  With a supplied base generator and the
declared positive symmetric logarithm they also determine the exact lift and
$b$.  With exposed cost inputs they determine the continuous SPD metric (C13).
This is a positive construction, not merely a counterexample classification.
