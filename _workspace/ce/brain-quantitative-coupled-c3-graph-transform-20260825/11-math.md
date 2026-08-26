# Mathematics lane

Status: COMPLETE

## M1. Third derivative through the graph-dependent inverse

At $x=F_h^{-1}(x')$, write

$$
L=DF_h,\quad J=L^{-1},\quad T=DY_hJ,
$$

$$
P=D^2F_h,\quad R=D^2Y_h,\quad N=R-TP.
$$

Let $U=D^3F_h$ and $V=D^3Y_h$. Differentiating
$Y_h=(\mathcal Th)\circ F_h$ three times gives

$$
D^3(\mathcal Th)[La,Lb,Lc]
=V[a,b,c]-TU[a,b,c]
-\sum_{\rm cyc}N[JP(a,b),c].
$$

Define the tensor on the right as $M_h$. Then

$$
D^3(\mathcal Th)[u,v,w]=M_h[Ju,Jv,Jw].
$$

This identity displays the terms hidden by the triangular formula: the base
third derivative $U$, the modified Hessian $N$, the inverse Jacobian $J$, and
the base Hessian $P$.

## M2. One-graph C3 and C3,1 classes

Put $r=1+\kappa$, $\|D^2h\|\le\Lambda_2$,
$\|D^3h\|\le\Lambda_3$. With $H_f,H_g$ bounding map Hessians and
$T_f,T_g$ bounding map third derivatives,

$$
C_U=L_{fy}\Lambda_3+3H_f\Lambda_2r+T_fr^3,
$$

$$
C_V=q\Lambda_3+3H_g\Lambda_2r+T_gr^3.
$$

If $\|J\|\le\alpha^{-1}$, $\|T\|\le\rho$,
$\|P\|\le C_F$, and $\|N\|\le N$, then

$$
M=C_V+\rho C_U+\frac{3NC_F}{\alpha},\qquad
\Lambda_{3,\mathrm{out}}=\frac{M}{\alpha^3}.
$$

When the base depends on graph height, two graphs at one output point have
different preimages. The class must then also bound
$\operatorname{Lip}(D^3h)\le\Xi_3$. Let $U_f,U_g$ be D4-level map moduli.
The fourth-order composition coefficients are

$$
C_{U,1}=L_{fy}\Xi_3+4H_fr\Lambda_3+3H_f\Lambda_2^2
+6T_f\Lambda_2r^2+U_fr^4,
$$

$$
C_{V,1}=q\Xi_3+4H_gr\Lambda_3+3H_g\Lambda_2^2
+6T_g\Lambda_2r^2+U_gr^4.
$$

Using the predecessor bounds $C_T,C_N,C_P$ gives

$$
C_{M,1}=C_{V,1}+C_TC_U+\rho C_{U,1}
+3\left(\frac{C_NC_F}{\alpha}
+\frac{NC_F^2}{\alpha^2}+\frac{NC_P}{\alpha}\right),
$$

$$
\Xi_{3,\mathrm{out}}=rac{C_{M,1}}{\alpha^4}
+\frac{3MC_F}{\alpha^5}.
$$

Thus $\Lambda_{3,\mathrm{out}}\le\Lambda_3$ is always required, while
$\Xi_{3,\mathrm{out}}\le\Xi_3$ is required exactly when $L_{fy}>0$.

## M3. Two-graph recurrence

At the two preimages, the predecessor supplies
$\|x_1-x_2\|\le r_x\delta$ and
$\|z_1-z_2\|\le Z\delta$. Hence graph third derivatives differ by at most
$f+\Xi_3r_x\delta$. Direct multilinear expansion gives

$$
\|U_1-U_2\|\le L_{fy}f+U_ee+U_dd+U_\delta\delta,
$$

$$
\|V_1-V_2\|\le qf+V_ee+V_dd+V_\delta\delta,
$$

where

$$
U_e=3H_fr,\quad U_d=3H_f\Lambda_2+3T_fr^2,
$$

$$
U_\delta=L_{fy}\Xi_3r_x+H_fZ\Lambda_3
+3H_fr\Lambda_3r_x+3H_f\Lambda_2^2r_x
+3T_fZ\Lambda_2r+3T_fr^2\Lambda_2r_x+U_fZr^3,
$$

and $V_e,V_d,V_\delta$ follow by
$(L_{fy},H_f,T_f,U_f)\mapsto(q,H_g,T_g,U_g)$.

For the cyclic correction, let

$$
E_e=\frac{QC_F+NL_{fy}}{\alpha},
$$

$$
E_d=\frac{N_dC_F}{\alpha}
+N\left(\frac{P_d}{\alpha}+\frac{C_FL_{fy}}{\alpha^2}\right),
$$

$$
E_\delta=\frac{N_\delta C_F}{\alpha}
+N\left(\frac{P_\delta}{\alpha}
+\frac{C_FA_\delta}{\alpha^2}\right).
$$

Then the modified third-derivative difference coefficients are

$$
M_e=V_e+\rho U_e+3E_e,
$$

$$
M_d=V_d+\rho U_d+C_U\beta_1+3E_d,
$$

$$
M_\delta=V_\delta+\rho U_\delta+C_Uc_{10}+3E_\delta.
$$

Changing the three outer inverse Jacobians finally proves

$$
f'\le\beta_{3,c}f+c_{32,c}e+c_{31,c}d+c_{30,c}\delta,
$$

$$
\beta_{3,c}=\frac{Q}{\alpha^3},\qquad
c_{32,c}=\frac{M_e}{\alpha^3},
$$

$$
c_{31,c}=\frac{M_d}{\alpha^3}+\frac{3ML_{fy}}{\alpha^4},\qquad
c_{30,c}=\frac{M_\delta}{\alpha^3}+\frac{3MA_\delta}{\alpha^4}.
$$

Together with the passing C0/C1/C2 recurrences, strict
$Q/\alpha^3<1$ gives convergence through third derivatives and a C3 fixed
graph.

## M4. Reduction, missing modulus, and boundary

At zero base coupling, $P=U=C_F=0$ and the formulas reduce coefficient by
coefficient to the affine triangular C3 theorem. If $L_{fy}>0$ but $\Xi_3$
is omitted, $D^3h(x_1)-D^3h(x_2)$ is uncontrolled; if $U_f,U_g$ are omitted,
the map third derivatives at $z_1,z_2$ are uncontrolled. Both shorter
candidates are therefore rejected.

At $x'=x/2$, $y'=y/8$, $Q/\alpha^3=1$, while the lower-order factors are
$1/4$ and $1/2$. The invariant $h_c(x)=c|x|^3$ is C2 but not C3 at zero.
The strict C3 bunching boundary is therefore necessary.

