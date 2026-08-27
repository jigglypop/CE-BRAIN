# Constructive affine-fiber correspondence contract

Status: COMPLETE

Mode: light successor within the same CE program

## Objective

The predecessor proved why an unrestricted arrow fails and gave abstract
conditional routes.  This successor must not stop there.  It must exhibit a
nontrivial local-circuit class in which the circuit update determines, rather
than assumes, an invariant manifold and its restricted dynamics.

## Frozen circuit class

Let $Z$ be a compact $C^1$ manifold, let $P:Z\to Z$ be a $C^1$ diffeomorphism,
and let $Y=\mathbb R^m$.  The population state is $x=(z,y)\in Z\times Y$.  Freeze
the block-triangular local update

$$
\Phi(z,y)=\bigl(Pz,Ay+c(z)\bigr),
$$

where $A\in\mathbb R^{m\times m}$ and $c:Z\to\mathbb R^m$ is $C^1$; both are determined by the
declared circuit graph, weights and local constitutive laws.  Missing graph
edges impose the corresponding zero/dependency restrictions in $A$ and $c$.

## Frozen assumptions

1. $\|A\|_2\le q<1$.
2. $\kappa=\sup_z\|DP^{-1}_z\|<\infty$ and $q\kappa<1$ for the $C^1$ theorem.
3. For the continuous-time lift, $P=\rho_\Delta$ is the time-$\Delta$ map of a
   supplied complete $C^1$ base vector field $f$ on $Z$.
4. For the exact stable lift, $A$ is symmetric positive definite with spectrum
   in $(0,1)$, so $\Lambda=-\Delta^{-1}\log A\succ0$ is uniquely fixed by the
   principal logarithm.
5. A metric statement must expose its extra cost/observation input.  Freeze a
   continuous base Riemannian metric field $G_Z(z)$ and the Euclidean fiber cost
   $I_m$; do not call them
   consequences of connectivity alone.

## Theorems to close

**C1 — explicit invariant graph.** Prove uniform convergence and uniqueness of

$$
h(z)=\sum_{k=1}^{\infty}A^{k-1}c(P^{-k}z),
$$

prove $h(Pz)=Ah(z)+c(z)$, and hence construct the closed invariant manifold
$M=\{(z,h(z)):z\in Z\}$.

**C2 — attraction and exact dimension.** Prove

$$
y_n-h(z_n)=A^n\bigl(y_0-h(z_0)\bigr),
$$

global fiber attraction at rate $q^n$, uniqueness of the bounded invariant
graph, and $\dim M=\dim Z$.

**C3 — differentiability and restricted discrete dynamics.** Under
$q\kappa<1$, prove $h\in C^1$, give a convergent formula for $Dh$, and prove
$\Phi|_M$ is conjugate to $P$.

**C4 — exact continuous-time lift and $b$.** With assumptions 3--4, define

$$
F(z,y)=\left(f(z),Dh(z)f(z)-\Lambda\bigl(y-h(z)\bigr)\right).
$$

Prove its time-$\Delta$ map is exactly $\Phi$, prove $M$ is invariant and
globally fiber-wise exponentially attracting, and construct

$$
b(z,h(z))=\bigl(f(z),Dh(z)f(z)\bigr).
$$

State precisely which generator/logarithm assumptions make this lift unique.
Do not call it an NHIM without an additional tangent/normal domination bound.

**C5 — stability sensitivity.** Prove explicit sup-norm perturbation bounds for
$h$ under changes of $A$ and $c$ with a common contraction ceiling $q_*<1$.

**C6 — derived metric with exposed axiom.** Define the discrete Lyapunov matrix

$$
H=\sum_{k=0}^{\infty}(A^\top)^kA^k,
$$

prove $H-A^\top HA=I$, and construct the induced metric

$$
g_M(u,v)=u^\top G_Zv+(Dh(z)u)^\top H(Dh(z)v).
$$

Prove it is a continuous SPD metric and distinguish this cost-conditioned
metric from an identified biological metric.  Do not claim higher smoothness
without stronger regularity of $G_Z$ and $h$.

## Falsifiers and boundaries

- If $q\ge1$, bounded invariant-graph uniqueness and attraction are not claimed.
- If $q\kappa\ge1$, continuity may survive but the frozen $C^1$ proof is killed.
- If $P$ lacks a supplied flow generator or $A$ lacks the declared positive
  logarithm, no unique continuous-time $b$ is claimed from the sampled map.
- If $G_Z$ or the fiber cost is not supplied, $g_M$ is not identified.
- No simulator or theorem is biological evidence.  A real-neural bridge remains
  conditional on source-locked state, measurement and intervention models.

## Validation ceiling

Use deterministic exact/finite binary64 fixtures for series convergence,
invariance, attraction, time-step parity, sensitivity and Lyapunov identities.
They are regression witnesses, not proofs or empirical neural endpoints.
