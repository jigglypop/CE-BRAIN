# Mathematics lane

Status: COMPLETE

## K1. Normalized chart and second derivative

Write

$$
F_t(x)=A_tx+a_t,
\qquad
S_h(x)=B_th(x)+g_t(x,h(x)),
\qquad
\mathcal Th=S_h\circ F_t^{-1}.
$$

Let $P_t=A_t^{-1}$, so $\|P_t\|\le\mu$. For
$z_h(x)=(x,h(x))$ and $J_h=(I,Dh)$, the normalized product norm gives
$\|J_h\|\le1+\kappa$. Since $F_t^{-1}$ is affine,

$$
D^2(\mathcal Th)(x')[u,v]
=D^2S_h(x)[P_tu,P_tv].
$$

The second-order chain rule gives

$$
D^2S_h
=(B_t+D_yg_t)D^2h+D^2g_t(z_h)[J_h,J_h].
$$

Using $\|B_t+D_yg_t\|\le q$ therefore yields

$$
\|D^2(\mathcal Th)\|
\le\mu^2\{q\Lambda_2+K_2(1+\kappa)^2\}
=:\Lambda_{2,\mathrm{out}}.
$$

Hence $\Lambda_{2,\mathrm{out}}\le\Lambda_2$ is sufficient for invariance
of the declared Hessian-bounded graph class.

## K2. Two-graph Hessian recurrence

For two triangular graphs, the same output base point has the same preimage
$x=F_t^{-1}(x')$. Define

$$
\delta=\|h_1-h_2\|_\infty,
\qquad
d=\|Dh_1-Dh_2\|_\infty,
\qquad
e=\|D^2h_1-D^2h_2\|_\infty.
$$

The first Hessian term obeys

$$
\|(B+D_yg_1)D^2h_1-(B+D_yg_2)D^2h_2\|
\le qe+K_2\Lambda_2\delta.
$$

Indeed, the first contribution is bounded by $q e$, while the second uses
$\|D_yg_1-D_yg_2\|\le K_2\delta$ and $\|D^2h_2\|\le\Lambda_2$.
For the quadratic chain-rule term, add and subtract
$D^2g_1[J_2,J_2]$. The bilinear argument changes contribute
$2K_2(1+\kappa)d$, and the fiber-position change contributes
$K_3(1+\kappa)^2\delta$. Multiplication by the two inverse-base factors gives

$$
e_{n+1}
\le\beta_2e_n+c_{21}d_n+c_{20}\delta_n,
$$

where

$$
\beta_2=q\mu^2,
\qquad
c_{21}=2\mu^2K_2(1+\kappa),
\qquad
c_{20}=\mu^2\{K_2\Lambda_2+K_3(1+\kappa)^2\}.
$$

Together with the predecessor recurrences,

$$
\delta_{n+1}\le q\delta_n,
\qquad
d_{n+1}\le\beta_1d_n+c_{10}\delta_n,
$$

this is an upper-triangular nonnegative linear recurrence. The passing C1
certificate supplies $q,\beta_1<1$. If $\beta_2<1$, repeated substitution
shows that all three coordinates tend to zero. Starting from any graph in the
invariant C2 class, consecutive graph-transform iterates are Cauchy in value,
first derivative, and Hessian. Uniform convergence of functions and their first
two derivatives identifies the unique Lipschitz fixed graph as C2.

## K3. Necessity of the third-order modulus

A uniform $K_2$ bounds $D^2g$ itself and controls changes of $Dg$, but it does
not control $D^2g(x,h_1)-D^2g(x,h_2)$. Thus C2 convergence for two different
graph values needs the declared fiber modulus $K_3$ (equivalently a suitable
third-derivative bound). Omitting it leaves the $c_{20}\delta_n$ term
unbounded, so that broader candidate is not promoted.

## K4. Reduction and strict boundary

If $K_2=K_3=0$, then
$\Lambda_{2,\mathrm{out}}=q\mu^2\Lambda_2$ and the Hessian recurrence
decouples as $e_{n+1}\le q\mu^2e_n$.

Strictness cannot be weakened. For

$$
x'=\frac12x,
\qquad
y'=\frac14y,
$$

one has $q=1/4$, $\mu=2$, $q\mu=1/2<1$, but $q\mu^2=1$. Every local

$$
h_c(x)=c\,x|x|
$$

is invariant because $h_c(x/2)=h_c(x)/4$. It is C1, but for $c\ne0$ it is
not C2 at zero. Therefore equality at the second-order bunching boundary cannot
force C2 regularity.

Verdict: the affine triangular C2 subcase is proved with an invariant
Hessian-bounded graph class, a finite $K_3$ fiber modulus, and strict
$q\mu^2<1$. Coupled, nonaffine/local, higher-order, and empirical promotions
remain open.
