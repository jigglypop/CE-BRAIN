# Mathematics lane

Status: COMPLETE

## M1. Local graph-transform domain

Let $U_t=\overline B(c_t,r_t)$ be convex base domains. Assume $\phi_t$ and
$\psi_t=\phi_t^{-1}$ extend as C2 maps to open neighborhoods of the relevant
compact sets, and

$$
\psi_t(U_{t+1})\subseteq U_t.
$$

For every graph $h_t:U_t\to Y$, define

$$
(\mathcal T_th_t)(x')
=B_th_t(\psi_t(x'))
+g_t(\psi_t(x'),h_t(\psi_t(x'))),
\qquad x'\in U_{t+1}.
$$

The coverage inclusion makes every evaluation legal. Convexity lets the
uniform derivative bounds imply the same Lipschitz estimates used by the
global predecessor. Therefore the radius/slope-bounded graph families over
$U_t$ remain complete in the sup norm and $\mathcal T_t$ has the same factor
$q<1$.

This yields overflow invariance, not retention of the whole input graph:

$$
F_t(\operatorname{graph}h_t)
\cap(U_{t+1}\times Y)
=\operatorname{graph}h_{t+1}
$$

for the part of the image whose base coordinate lies in $U_{t+1}$. A forward
claim for every $x\in U_t$ would additionally require
$\phi_t(U_t)\subseteq U_{t+1}$.

## M2. Exact coverage gate

If

$$
\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|
\le r_{\rm pre,t}\le r_t,
$$

then coverage follows immediately. In normalized coordinates,

$$
m_{\rm cov}=r_x-r_{\rm pre}\ge0.
$$

Equality is mathematically sufficient but is not robust to an increase of the
certified inverse-image radius. A negative margin leaves some required graph
evaluation outside the declared domain.

## M3. C2 localization

All predecessor identities are pointwise on $U_{t+1}$. In particular,

$$
D^2(\mathcal T_th_t)
=D^2S_{h_t}[D\psi_t,D\psi_t]+DS_{h_t}D^2\psi_t.
$$

Uniform local bounds therefore give exactly

$$
\Lambda_{2,\mathrm{out}}^{\rm loc}
=\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}
+(q\kappa+L_x)\nu,
$$

and for two graph iterates

$$
e_{n+1}\le q\mu^2e_n
+\{2\mu^2K_2(1+\kappa)+q\nu\}d_n
+\left[\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}
+\nu(H_y\kappa+H_x)\right]\delta_n.
$$

The common local inverse is still graph-independent. Thus no comparison
modulus for two different inverse maps appears. If the predecessor C1 gates,
the local coverage gate, the Hessian-class gate, and strict $q\mu^2<1$ pass,
the local fixed graph is C2 in the overflow sense of M1.

## M4. Expanding sine witness

Let

$$
\phi_{\lambda,a}(x)=\lambda x+a\sin x,
\qquad \lambda>a\ge0.
$$

Then

$$
\phi_{\lambda,a}'(x)
=\lambda+a\cos x\ge\lambda-a>0,
$$

so the map is a global diffeomorphism and

$$
\mu=\frac1{\lambda-a},
\qquad
\nu=\frac{a}{(\lambda-a)^3}.
$$

Because $\phi_{\lambda,a}(0)=0$ and
$|\phi_{\lambda,a}(x)|\ge(\lambda-a)|x|$,

$$
|\psi_{\lambda,a}(x')|
\le\mu|x'|.
$$

For centered radius $r_x$, one may therefore certify
$r_{\rm pre}=\mu r_x$. At $(\lambda,a)=(2,1/4)$ the contract values are

$$
\mu=\frac47,
\quad
\nu=\frac{16}{343},
\quad
m_{\rm cov}=\frac37,
$$

and direct substitution gives

$$
\Lambda_{2,\mathrm{out}}^{\rm loc}=\frac{94}{343},
\quad
\beta_2=\frac8{49},
\quad
c_{21}=\frac{36}{343},
\quad
c_{20}=\frac{37}{343}.
$$

## M5. Counterexamples and claim boundary

On $U=[-1,1]$, $\phi(x)=x/2$ has $\psi(x')=2x'$. At $x'=3/4$ the formula
requires $h(3/2)$, which is outside $U$. Hence local derivative bounds alone
cannot define the graph transform over all of $U$.

Conversely, $\phi(x)=2x$ has $\psi(U)=[-1/2,1/2]\subset U$, so the local
graph transform is well-defined with a strict coverage margin. But the input
point $x=3/4$ maps to $3/2\notin U$. Thus inverse coverage cannot be promoted
to full forward retention.

Verdict: backward-covered/overflow local graph-independent nonaffine
triangular C2 is proved. Exact matched-domain forward invariance, nonaffine
coupled C2, C3+, and empirical neural identification remain open.

