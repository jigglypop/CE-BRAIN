# Mathematics lane

Status: COMPLETE

## R1. Modified Hessian with a curved base

At $x=F_h^{-1}(x')$, write

$$
L_h=DF_h,
\quad J_h=L_h^{-1},
\quad K_h=DY_h,
\quad T_h=K_hJ_h,
$$

$$
P_h=D^2F_h,
\quad R_h=D^2Y_h,
\quad N_h=R_h-T_hP_h.
$$

The exact inverse-function identity remains

$$
D^2(\mathcal Th)(x')[u,v]
=N_h(x)[J_hu,J_hv].
$$

Nonaffinity changes

$$
P_h
=D^2\phi_t
+D^2f_t(x,h)[J_h^{\rm gr},J_h^{\rm gr}]
+D_yf_t(x,h)D^2h.
$$

Therefore the predecessor C1 bound $C_F^{\rm na}$ is also the one-graph
upper bound for $P_h$. With $\|T_h\|\le\rho$,

$$
\|N_h\|
\le C_Y+\rho C_F^{\rm na}
=N.
$$

The output Hessian class is exactly $N/\alpha^2$, equal to the nonaffine C1
output derivative-Lipschitz bound.

## R2. C2,1 class invariance

Assume

$$
\|D^2h\|\le\Lambda,
\qquad
\operatorname{Lip}(D^2h)\le\Xi,
$$

and

$$
\operatorname{Lip}(D^2\phi_t)\le T_\phi.
$$

Along one graph, expanding the three terms of $P_h$ gives

$$
C_P^{\rm na}
=T_\phi+T_f(1+\kappa)^3
+3H_f(1+\kappa)\Lambda+L_{fy}\Xi.
$$

The fiber-Hessian modulus remains

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda
+T_g(1+\kappa)^3.
$$

The first-derivative transform has input-base modulus

$$
C_T=\frac{C_Y}{\alpha}
+\frac{sC_F^{\rm na}}{\alpha^2}.
$$

Thus

$$
C_N^{\rm na}=C_R+C_TC_F^{\rm na}+\rho C_P^{\rm na}.
$$

Changing $N_h$, then both inverse-Jacobian arguments, and finally
reparameterizing by $F_h^{-1}$ yields

$$
\Xi_{\rm out}^{\rm na}
=\frac{C_N^{\rm na}}{\alpha^3}
+\frac{2NC_F^{\rm na}}{\alpha^4}.
$$

When $L_{fy}>0$, different graphs have different preimages and
$\Xi_{\rm out}^{\rm na}\le\Xi$ preserves the required C2,1 class. At exactly
$L_{fy}=0$, the preimages are graph-independent; the two-graph proof needs no
$\Xi$ modulus, so this extra gate is bypassed exactly as in the affine theorem.

## R3. Two-graph base-Hessian difference

For two graphs at the same output base point,
$\|x_1-x_2\|\le r_x\delta$. The new term satisfies

$$
\|D^2\phi_t(x_1)-D^2\phi_t(x_2)\|
\le T_\phi r_x\delta.
$$

Adding this to the affine product expansion gives

$$
\|P_1-P_2\|
\le L_{fy}e+P_dd+P_\delta^{\rm na}\delta,
$$

where

$$
P_d=2H_f(1+\kappa),
$$

$$
P_\delta^{\rm na}
=T_\phi r_x+L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x
+T_fZ(1+\kappa)^2.
$$

The fiber expansion is unchanged:

$$
\|R_1-R_2\|
\le qe+R_dd+R_\delta\delta.
$$

## R4. Modified-Hessian and graph-Hessian recurrences

The nonaffine coupled C1 predecessor gives

$$
\|T_1-T_2\|
\le\beta_1d+c_{10}^{\rm na}\delta.
$$

Therefore

$$
\|N_1-N_2\|
\le Qe+N_d^{\rm na}d+N_\delta^{\rm na}\delta,
$$

with

$$
N_d^{\rm na}=R_d+C_F^{\rm na}\beta_1+\rho P_d,
$$

$$
N_\delta^{\rm na}
=R_\delta+C_F^{\rm na}c_{10}^{\rm na}
+\rho P_\delta^{\rm na}.
$$

The inverse-Jacobian difference is

$$
\|J_1-J_2\|
\le\frac{L_{fy}d+A_\delta^{\rm na}\delta}{\alpha^2}.
$$

Comparing $N_1[J_1,J_1]$ and $N_2[J_2,J_2]$ now proves

$$
e_{n+1}
\le\frac Q{\alpha^2}e_n
+\left(\frac{N_d^{\rm na}}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3}\right)d_n
$$

$$
\quad
+\left(\frac{N_\delta^{\rm na}}{\alpha^2}
+\frac{2NA_\delta^{\rm na}}{\alpha^3}\right)\delta_n.
$$

The full recurrence is upper triangular with diagonal
$Q,Q/\alpha,Q/\alpha^2$. Passing C1 gates and strict $Q/\alpha^2<1$ make every
coordinate converge, so the unique invariant graph is C2.

## R5. Reductions and boundary

If $H_\phi=T_\phi=0$, every new quantity reduces term by term to affine
coupled C2.

For the graph-independent reduction set
$L_{fx}=L_{fy}=H_f=T_f=0$. Then $\alpha=\mu^{-1}$, $Q=q$, $r_x=0$, and

$$
\nu=H_\phi\mu^3
$$

is the inverse-base Hessian bound. Identifying $H_g=K_2$, $T_g=K_3$ gives

$$
\beta_2=q\mu^2,
$$

$$
c_{21}=2\mu^2K_2(1+\kappa)+q\nu,
$$

$$
c_{20}
=\mu^2\{K_2\Lambda+K_3(1+\kappa)^2\}
+\nu(H_g(1+\kappa)),
$$

which is the nonaffine triangular formula under the common block bound
$H_x,H_y\le H_g$. The sharper split form is recovered by supplying separate
blocks. The exact fixture using the predecessor's split-equal bounds matches
$20/27$ and $38/27$.

At $Q/\alpha^2=1$, the affine subcase remains embedded and the invariant
$h_c(x)=cx|x|$ blocks C2. Equality cannot pass.

Verdict: global nonaffine coupled C2 is proved with finite $H_\phi,T_\phi$,
the conditional C2,1 graph class, and strict second bunching. Local domain
composition, C3+, and empirical brain identification remain open.

