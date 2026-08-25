# Mathematics lane: physical scale and mobility map

Status: COMPLETE

## M1. Mobility normalization theorem

Let $x=X_0\widetilde x$, $\mathcal V=V_0\widetilde{\mathcal V}$, and $t=t_0\tau$, where all reference scales are positive. The chain rule gives

$$
\frac{dx}{dt}=\frac{X_0}{t_0}\frac{d\widetilde x}{d\tau},
\qquad
\nabla_x\mathcal V=\frac{V_0}{X_0}
\nabla_{\widetilde x}\widetilde{\mathcal V}.
$$

Substitution in $\dot x=-\mu_{\rm phys}A^{-1}\nabla_x\mathcal V$ and multiplication by $t_0/X_0$ yield (S1), with
$\widetilde\mu=\mu_{\rm phys}V_0t_0/X_0^2$. Since

$$
[\mu_{\rm phys}]\frac{[\mathcal V][t]}{[x]^2}
=\frac{[x]^2}{[\mathcal V][t]}
\frac{[\mathcal V][t]}{[x]^2}=1,
$$

$\widetilde\mu$ is dimensionless. The earlier choice
$\mu_0=X_0^2/(V_0t_0)$ is exactly the slice $\widetilde\mu=1$, not a calibration of $\mu_{\rm phys}$.

## M2. Speed and dissipation scales

Taking norms in (S1) and restoring $dx/dt=(X_0/t_0)d\widetilde x/d\tau$ proves (S3). In the Euclidean subcase,

$$
\frac{d\mathcal V}{dt}
=\langle\nabla_x\mathcal V,\dot x\rangle
=-\mu_{\rm phys}\|\nabla_x\mathcal V\|^2.
$$

Using $\nabla_x\mathcal V=(V_0/X_0)\nabla\widetilde{\mathcal V}$ gives

$$
-\frac{d\mathcal V}{dt}
=\mu_{\rm phys}\frac{V_0^2}{X_0^2}
\|\nabla\widetilde{\mathcal V}\|^2
=\frac{V_0}{t_0}\widetilde\mu
\|\nabla\widetilde{\mathcal V}\|^2,
$$

which proves (S4). For a nontrivial metric operator the exact expression is
$P_0\widetilde\mu\langle\nabla\widetilde{\mathcal V},A^{-1}\nabla\widetilde{\mathcal V}\rangle$; a norm bound then additionally needs an operator bound for $A^{-1}$.

## M3. Exact logarithm enclosure

For $0<q<1$, let $z=(1-q)/(1+q)$. Solving for $q$ gives
$q=(1-z)/(1+z)$, hence

$$
-\log q=\log\frac{1+z}{1-z}
=2\operatorname{artanh}z
=2\sum_{k=0}^{\infty}\frac{z^{2k+1}}{2k+1}.
$$

All terms are positive, so $L_N\le-\log q$. For the remainder,

$$
2\sum_{k=N}^{\infty}\frac{z^{2k+1}}{2k+1}
\le
\frac{2z^{2N+1}}{2N+1}\sum_{j=0}^{\infty}z^{2j}
=\frac{2z^{2N+1}}{(2N+1)(1-z^2)}.
$$

This proves $L_N\le-\log q\le U_N$ and, because $\Delta t>0$, proves (S7). The upper-minus-lower width is positive and tends to zero as $N\to\infty$.

## M4. Boundary counterexamples and exclusions

At $q=1$, $q^n=1$ for every $n$ and no positive exponential decay rate can satisfy the same exact bound. This is a complete counterexample to extending the positive-rate conclusion to the closed boundary. At $q=0$, $q^n=0$ for $n\ge1$; $-\log0$ is not finite, so the correct statement is finite-window collapse, not a finite rate.

If $t_0$ or $\Delta\tau$ is not supplied, the transformation $t_0\mapsto c t_0$ changes every physical rate by $1/c$ while leaving $q$ unchanged. Therefore $q$ alone cannot identify seconds. Likewise, rescaling $V_0$ and compensating $\mu_{\rm phys}$ leaves $\widetilde\mu$ invariant, so the normalized dynamics alone cannot identify a physical energy scale or mobility separately.

Verdict: M1--M3 are conditional theorems under declared scales; M4 preserves the physical-identifiability gap.

