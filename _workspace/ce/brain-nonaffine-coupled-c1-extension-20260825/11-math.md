# Mathematics lane

Status: COMPLETE

## Q1. Nonaffine coupled base inversion

For a graph $h$, write

$$
F_h(x)=\phi_t(x)+f_t(x,h(x)).
$$

The co-Lipschitz premise and the graph slope give

$$
\|F_h(x_1)-F_h(x_2)\|
\ge\left(\mu^{-1}-L_{fx}-L_{fy}\kappa\right)
\|x_1-x_2\|
=\alpha\|x_1-x_2\|.
$$

Equivalently, solving
$x=\phi_t^{-1}(x'-f_t(x,h(x)))$ is a contraction whenever
$\mu(L_{fx}+L_{fy}\kappa)<1$. Thus the predecessor inversion, preimage
difference $r_x=L_{fy}/\alpha$, state factor
$Z=1+(1+\kappa)r_x$, and graph-transform factor $Q$ remain unchanged.

## Q2. One-graph C1,1 class

Let $J_h^{\rm gr}=(I,Dh)$. Then

$$
DF_h=D\phi_t+D f_t(x,h)J_h^{\rm gr}.
$$

For two input base points on one graph, the first term now varies. With
$\|D^2\phi_t\|\le H_\phi$,

$$
\operatorname{Lip}(DF_h)
\le H_\phi+H_f(1+\kappa)^2+L_{fy}\Lambda
=C_F^{\rm na}.
$$

The fiber bound is unchanged:

$$
C_Y=q\Lambda+H_g(1+\kappa)^2.
$$

For $J_h=(DF_h)^{-1}$ and $T_h=DY_hJ_h$, the inverse identity gives

$$
\operatorname{Lip}(T_h\circ F_h^{-1})
\le\frac{C_Y}{\alpha^2}
+\frac{sC_F^{\rm na}}{\alpha^3}
=\Lambda_{\rm out}^{\rm na}.
$$

Therefore $\Lambda_{\rm out}^{\rm na}\le\Lambda$ preserves the declared
C1,1 graph class.

## Q3. Two-graph derivative recurrence

At one output base point, the graph-dependent preimages obey
$\|x_1-x_2\|\le r_x\delta$. Expanding the base Jacobian difference adds

$$
\|D\phi_t(x_1)-D\phi_t(x_2)\|
\le H_\phi r_x\delta.
$$

Consequently

$$
\|DF_1-DF_2\|
\le L_{fy}d+A_\delta^{\rm na}\delta,
$$

where

$$
A_\delta^{\rm na}
=H_\phi r_x+H_fZ(1+\kappa)+L_{fy}\Lambda r_x.
$$

The fiber-Jacobian difference is unchanged:

$$
\|DY_1-DY_2\|
\le qd+Y_\delta\delta,
$$

$$
Y_\delta=q\Lambda r_x+H_gZ(1+\kappa).
$$

Using $J_1-J_2=J_1(DF_2-DF_1)J_2$ in
$DY_1J_1-DY_2J_2$ proves

$$
d_{n+1}\le\frac Q\alpha d_n
+\left(\frac{Y_\delta}{\alpha}
+\frac{sA_\delta^{\rm na}}{\alpha^2}\right)\delta_n.
$$

Together with $\delta_{n+1}\le Q\delta_n$, strict $Q/\alpha<1$ makes the
two-level nonnegative recurrence stable and the fixed graph C1.

## Q4. Exact witness and affine reduction

For $\phi_{\lambda,a}(x)=\lambda x+a\sin x$ with $\lambda>a\ge0$,

$$
\phi_{\lambda,a}'(x)\ge\lambda-a,
\qquad
|\phi_{\lambda,a}''(x)|\le a.
$$

Thus $\mu=(\lambda-a)^{-1}$ and $H_\phi=a$. At
$(\lambda,a)=(1001/1000,1/1000)$ the contract's exact constants follow by
direct substitution. Relative to the affine predecessor, the only increments
are

$$
\Delta C_F=H_\phi,
\qquad
\Delta\Lambda_{\rm out}=\frac{sH_\phi}{\alpha^3},
$$

$$
\Delta A_\delta=H_\phi r_x,
\qquad
\Delta c_{10}=\frac{sH_\phi r_x}{\alpha^2}.
$$

If $H_\phi=0$ on a connected chart, $D\phi$ is constant and the entire
apparatus reduces exactly to affine coupled C1. The strict equality boundary
$Q/\alpha=1$ retains the predecessor's invariant Lipschitz/non-C1 witness, so
nonaffinity cannot weaken the bunching gate.

Verdict: global nonaffine coupled C1 is proved with finite base curvature
$H_\phi$. Nonaffine coupled C2 additionally needs a modulus for $D^2\phi$ and
is the immediate successor.

