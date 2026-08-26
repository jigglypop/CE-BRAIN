# Mathematics lane

Status: COMPLETE

## N1. Exact third-order nonaffine chain rule

Let

$$
S_h(x)=Bh(x)+g(x,h(x)),\qquad \mathcal Th=S_h\circ\psi,
$$

where the inverse base $\psi=\phi^{-1}$ is common to every graph. Put

$$
\|D\psi\|\le\mu,\qquad \|D^2\psi\|\le\nu,
\qquad \|D^3\psi\|\le\tau.
$$

The exact chain rule is

$$
D^3(S_h\circ\psi)
=D^3S_h[D\psi,D\psi,D\psi]
+3D^2S_h[D^2\psi,D\psi]+DS_hD^3\psi.
$$

For $r=1+\kappa$ and $s=q\kappa+L_x$, define

$$
A_2=q\Lambda_2+K_2r^2,
$$

$$
A_3=q\Lambda_3+3K_2\Lambda_2r+K_3r^3.
$$

Then

$$
\Lambda_{3,\mathrm{out}}^{\rm na}
=\mu^3A_3+3\mu\nu A_2+s\tau.
$$

The middle term is the interaction of inverse curvature with the fiber
Hessian; the final term is the inverse third derivative acting on the fiber
slope. Both vanish in the affine limit.

## N2. Four-level recurrence

At a common output point, both transforms use the same preimage and the same
$D\psi,D^2\psi,D^3\psi$. Therefore no modulus of inverse derivatives is
needed for the two-graph comparison. The affine predecessor gives

$$
\|D^3S_1-D^3S_2\|
\le qf+3K_2re
+3(K_2\Lambda_2+K_3r^2)d
+(K_2\Lambda_3+3K_3\Lambda_2r+K_4r^3)\delta.
$$

The nonaffine C2 predecessor supplies

$$
\|D^2S_1-D^2S_2\|
\le qe+2K_2rd+(K_2\Lambda_2+K_3r^2)\delta,
$$

and

$$
\|DS_1-DS_2\|\le qd+(H_y\kappa+H_x)\delta.
$$

Substitution into the exact chain rule proves

$$
f'\le\beta_3f+c_{32}^{\rm na}e+c_{31}^{\rm na}d
+c_{30}^{\rm na}\delta,
$$

where

$$
\beta_3=q\mu^3,
$$

$$
c_{32}^{\rm na}=3\mu^3K_2r+3\mu\nu q,
$$

$$
c_{31}^{\rm na}
=3\mu^3(K_2\Lambda_2+K_3r^2)+6\mu\nu K_2r+\tau q,
$$

$$
c_{30}^{\rm na}
=\mu^3(K_2\Lambda_3+3K_3\Lambda_2r+K_4r^3)
+3\mu\nu(K_2\Lambda_2+K_3r^2)
+\tau(H_y\kappa+H_x).
$$

Together with the passing C0/C1/C2 recurrences, class invariance and strict
$q\mu^3<1$ make the four-level nonnegative triangular system converge.
Hence the unique invariant graph is C3.

## N3. Exact sine-inverse bound

For $\phi_a(x)=x+a\sin x$, $0\le a<1$, inverse differentiation gives

$$
\psi_a'''=
\frac{3(\phi_a''\circ\psi_a)^2
-(\phi_a'''\circ\psi_a)(\phi_a'\circ\psi_a)}
{(\phi_a'\circ\psi_a)^5}.
$$

Since $\phi_a'\ge1-a$, $|\phi_a''|\le a$,
$|\phi_a'''|\le a$, and $|\phi_a'|\le1+a$,

$$
\mu_a=\frac1{1-a},\qquad
\nu_a=\frac{a}{(1-a)^3},\qquad
\tau_a=\frac{a+4a^2}{(1-a)^5}.
$$

At $a=1/10$ these equal $10/9$, $100/729$, and $14000/59049$.
The strict fixture has $\beta_3=500/729<1$. At $a=1$, the inverse derivative
already fails at $x=\pi$, so no C3 certificate exists.

## N4. Reduction and strict boundary

At $\nu=\tau=0$, every class and recurrence coefficient reduces exactly to
the affine triangular C3 theorem. Omitting $\tau$ from a nonaffine base leaves
$DS_hD^3\psi$ uncontrolled; it is therefore not a valid candidate.

At $q=1/8$, $\mu=2$, the lower-order factors are $1/4$ and $1/2$, while
$q\mu^3=1$. The invariant $h_c(x)=c|x|^3$ is C2 but not C3 at zero, proving
that the third-order boundary must remain strict.

