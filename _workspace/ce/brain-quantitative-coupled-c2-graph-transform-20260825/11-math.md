# Mathematics lane

Status: COMPLETE

## L1. Second derivative through a graph-dependent inverse

On a normalized convex base chart, define

$$
F_h(x)=A_tx+a_t+f_t(x,h(x)),
\qquad
Y_h(x)=B_th(x)+g_t(x,h(x)).
$$

At $x=F_h^{-1}(x')$, write

$$
L_h=DF_h,
\quad J_h=L_h^{-1},
\quad K_h=DY_h,
\quad T_h=K_hJ_h,
$$

$$
P_h=D^2F_h,
\qquad
R_h=D^2Y_h,
\qquad
N_h=R_h-T_hP_h.
$$

The inverse-function Hessian identity gives

$$
D^2(\mathcal Th)(x')[u,v]
=N_h(x)[J_hu,J_hv].
$$

The coupled C1 predecessor supplies
$\|J_h\|\le\alpha^{-1}$, $\|K_h\|\le s$,
$\|T_h\|\le\rho=s/\alpha$, $\|P_h\|\le C_F$, and
$\|R_h\|\le C_Y$. Hence

$$
\|N_h\|\le N:=C_Y+\rho C_F,
$$

and the output Hessian bound is $N/\alpha^2$, exactly the predecessor's
$\Lambda_{\mathrm{out}}$.

## L2. Invariance of the graph-Hessian modulus

When $L_{fy}>0$, different graphs have different preimages. A bound on
$D^2h$ alone therefore does not control
$D^2h(x_1)-D^2h(x_2)$. Freeze the stronger class

$$
\|D^2h\|\le\Lambda,
\qquad
\operatorname{Lip}(D^2h)\le\Xi.
$$

Along one graph, direct product-rule expansion gives

$$
C_P=T_f(1+\kappa)^3
+3H_f(1+\kappa)\Lambda+L_{fy}\Xi,
$$

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda
+T_g(1+\kappa)^3.
$$

These are input-base Lipschitz bounds for $P_h$ and $R_h$. The first-derivative
transform obeys

$$
C_T=\frac{C_Y}{\alpha}+\frac{sC_F}{\alpha^2}.
$$

Thus

$$
C_N=C_R+C_TC_F+\rho C_P
$$

bounds the input-base variation of $N_h$. Varying both outer inverse
Jacobians and then reparameterizing by $F_h^{-1}$ gives

$$
\Xi_{\mathrm{out}}
=\frac{C_N}{\alpha^3}
+\frac{2NC_F}{\alpha^4}.
$$

Therefore $\Xi_{\mathrm{out}}\le\Xi$ preserves the C2,1 graph class. If
$L_{fy}=0$, the base map is graph-independent and both graph transforms use
the same preimage. The two-graph C2 proof below then needs no $\Xi$ gate, so
the exact graph-independent reduction is retained.

## L3. Two-graph base and fiber Hessian differences

For two graphs at the same output base point, the predecessor gives

$$
\|x_1-x_2\|\le r_x\delta,
\qquad
\|z_1-z_2\|_\oplus\le Z\delta.
$$

The graph tangent and Hessian changes obey

$$
\|(I,Dh_1(x_1))-(I,Dh_2(x_2))\|
\le d+\Lambda r_x\delta,
$$

$$
\|D^2h_1(x_1)-D^2h_2(x_2)\|
\le e+\Xi r_x\delta.
$$

Expanding
$P_h=D^2f[J_h^{\rm gr},J_h^{\rm gr}]+D_yfD^2h$
therefore yields

$$
\|P_1-P_2\|
\le L_{fy}e+P_dd+P_\delta\delta,
$$

where

$$
P_d=2H_f(1+\kappa),
$$

$$
P_\delta=L_{fy}\Xi r_x+H_fZ\Lambda
+2H_f(1+\kappa)\Lambda r_x
+T_fZ(1+\kappa)^2.
$$

The analogous expansion of
$R_h=(B+D_yg)D^2h+D^2g[J_h^{\rm gr},J_h^{\rm gr}]$
gives

$$
\|R_1-R_2\|
\le qe+R_dd+R_\delta\delta,
$$

where

$$
R_d=2H_g(1+\kappa),
$$

$$
R_\delta=q\Xi r_x+H_gZ\Lambda
+2H_g(1+\kappa)\Lambda r_x
+T_gZ(1+\kappa)^2.
$$

## L4. Hessian recurrence

Use

$$
\|T_1-T_2\|\le\beta_1d+c_1\delta
$$

and $N_h=R_h-T_hP_h$. Then

$$
\|N_1-N_2\|
\le Qe+N_dd+N_\delta\delta,
$$

with

$$
N_d=R_d+C_F\beta_1+\rho P_d,
\qquad
N_\delta=R_\delta+C_Fc_1+\rho P_\delta.
$$

The inverse-Jacobian identity and the predecessor base derivative bound give

$$
\|J_1-J_2\|
\le\frac{L_{fy}d+A_\delta\delta}{\alpha^2}.
$$

Finally compare
$N_1[J_1,J_1]$ and $N_2[J_2,J_2]$, changing the middle tensor and then each
outer inverse Jacobian. This proves

$$
e_{n+1}
\le\beta_{2,c}e_n+c_{21,c}d_n+c_{20,c}\delta_n,
$$

where

$$
\beta_{2,c}=\frac{Q}{\alpha^2},
$$

$$
c_{21,c}=\frac{N_d}{\alpha^2}
+\frac{2NL_{fy}}{\alpha^3},
\qquad
c_{20,c}=\frac{N_\delta}{\alpha^2}
+\frac{2NA_\delta}{\alpha^3}.
$$

The passing predecessor supplies $Q,\beta_1<1$. If
$\beta_{2,c}<1$, the value/derivative/Hessian recurrence is a stable
nonnegative upper-triangular system. Consecutive graph-transform iterates
converge uniformly through second derivatives, so the unique Lipschitz fixed
graph is C2.

## L5. Reduction and strict boundary

If $L_{fx}=L_{fy}=L_{gx}=H_f=T_f=0$, then
$\alpha=1/\mu$, $Q=q$, $r_x=0$. Identifying $H_g=K_2$ and $T_g=K_3$ gives

$$
\beta_{2,c}=q\mu^2,
$$

$$
c_{21,c}=2\mu^2K_2(1+\kappa),
\qquad
c_{20,c}=\mu^2\{K_2\Lambda+K_3(1+\kappa)^2\},
$$

which are exactly the affine triangular C2 coefficients. At
$q\mu^2=1$, the local map $x'=x/2$, $y'=y/4$ and invariant
$h_c(x)=cx|x|$ remain a complete C1/non-C2 boundary witness.

Verdict: affine coupled C2 is proved under the passing coupled C1 class,
finite map-Hessian moduli, strict $Q/\alpha^2<1$, and—only when the base
depends on the graph—an invariant graph-Hessian modulus. Nonaffine/local,
C3+, and empirical promotions remain open.
