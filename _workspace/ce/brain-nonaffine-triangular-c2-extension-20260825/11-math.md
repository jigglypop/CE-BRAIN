# Mathematics lane

Status: COMPLETE

## K1. Nonaffine second-order chain rule

Put

$$
S_h(x)=B_th(x)+g_t(x,h(x)),\qquad \mathcal Th=S_h\circ\psi_t,
$$

where $\psi_t=\phi_t^{-1}$ is common to every graph and
$\|D\psi_t\|\le\mu$, $\|D^2\psi_t\|\le\nu$. The exact chain rule is

$$
D^2(\mathcal Th)=D^2S_h[D\psi_t,D\psi_t]+DS_hD^2\psi_t.
$$

For $q=b+L_y$, $s=q\kappa+L_x$, $\|D^2h\|\le\Lambda_2$ and
$\|D^2g\|\le K_2$, the predecessor estimates give

$$
\|DS_h\|\le s,
\qquad
\|D^2S_h\|\le q\Lambda_2+K_2(1+\kappa)^2.
$$

Consequently

$$
\Lambda_{2,\mathrm{out}}^{\rm na}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}+s\nu.
$$

Thus $\Lambda_{2,\mathrm{out}}^{\rm na}\le\Lambda_2$ is sufficient for
invariance of the normalized Hessian-bounded graph class. The added $s\nu$
term is mandatory whenever the inverse base is curved.

## K2. Two-graph recurrence

At a common output base point both graph transforms use the same preimage,
$x=\psi_t(x')$, and the same $D\psi_t,D^2\psi_t$. For

$$
\delta=\|h_1-h_2\|_\infty,
\quad d=\|Dh_1-Dh_2\|_\infty,
\quad e=\|D^2h_1-D^2h_2\|_\infty,
$$

the affine predecessor proves

$$
\|D^2S_1-D^2S_2\|
\le qe+2K_2(1+\kappa)d
+\{K_2\Lambda_2+K_3(1+\kappa)^2\}\delta.
$$

The first-derivative difference is

$$
\|DS_1-DS_2\|
\le qd+(H_y\kappa+H_x)\delta.
$$

Multiplying the first estimate by $\mu^2$ and the second by $\nu$ yields

$$
e_{n+1}\le\beta_2e_n+c_{21}^{\rm na}d_n+c_{20}^{\rm na}\delta_n,
$$

with

$$
\beta_2=q\mu^2,
$$

$$
c_{21}^{\rm na}=2\mu^2K_2(1+\kappa)+q\nu,
$$

$$
c_{20}^{\rm na}
=\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}
+\nu(H_y\kappa+H_x).
$$

Together with the passing nonaffine C1 recurrence this is upper triangular.
Class invariance and strict $q\mu^2<1$ therefore close global triangular C2.
No modulus of $D^2\psi_t$ is required here because the base inverse and its
derivatives are common to both graphs; that simplification fails in the
coupled case.

## K3. Exact nonaffine witness

For $\phi_a(x)=x+a\sin x$ with $0\le a<1$,

$$
\phi_a'(x)=1+a\cos x\ge1-a>0,
$$

so it is a global orientation-preserving diffeomorphism. Its inverse obeys

$$
\psi_a'=\frac1{\phi_a'\circ\psi_a},
\qquad
\psi_a''=-\frac{\phi_a''\circ\psi_a}
{(\phi_a'\circ\psi_a)^3}.
$$

Since $|\phi_a''|\le a$,

$$
\mu_a=\frac1{1-a},\qquad \nu_a=\frac{a}{(1-a)^3}.
$$

At $a=1$, $\phi_1'(\pi)=0$, so the inverse derivative certificate fails.
For $a=1/4$, $(\mu,\nu)=(4/3,16/27)$. With the contract's exact baseline,

$$
\Lambda_{2,\mathrm{out}}^{\rm na}=\frac{214}{27}<8,
\quad \beta_2=\frac89,
\quad c_{21}^{\rm na}=\frac{20}{27},
\quad c_{20}^{\rm na}=\frac{38}{27}.
$$

## K4. Reduction and boundary

When $\nu=0$, every new term vanishes and all class and recurrence
coefficients reduce exactly to the affine triangular C2 theorem. Hessian-class
equality may pass but is non-robust. Bunching equality cannot pass: with
$q=1/4$, $\mu=2$, and zero cross terms, C1 has $q\mu=1/2<1$ while C2 has
$q\mu^2=1$. The predecessor invariant $h_c(x)=cx|x|$ is C1 but not C2.

Verdict: global graph-independent nonaffine triangular C2 is proved under the
declared inverse derivative and inverse Hessian bounds. Nonaffine coupled or
local C2, C3+, empirical neural fields, and consciousness-dimension selection
remain open.

