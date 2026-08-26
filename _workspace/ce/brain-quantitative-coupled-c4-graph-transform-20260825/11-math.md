# Mathematics lane

Status: COMPLETE

## Exact modified fourth tensor

Let $Y_h=(\mathcal Th)\circ F_h$ and use the contract's $J,P,U,W$ and
$K,R,V,Z$. Write $L=J^{-1}$. Differentiating the composition four times gives

$$
\begin{aligned}
Z={}&D^4(\mathcal Th)[J,J,J,J]
+6D^3(\mathcal Th)[P,J,J]\\
&+3D^2(\mathcal Th)[P,P]
+4D^2(\mathcal Th)[U,J]+TW.
\end{aligned}
$$

Substitution of the predecessor identities
$D^2(\mathcal Th)=N[L,L]$ and $D^3(\mathcal Th)=M[L,L,L]$ yields

$$
O=Z-TW-4N[LU,\cdot]-3N[LP,LP]-6M[LP,\cdot,\cdot],
$$

$$
D^4(\mathcal Th)=O[L,L,L,L].
$$

An exact scalar inverse-series computation independently reproduces this
identity.

## One-graph C4 class

Let $r=1+\kappa$. Denote the D2, D3, D4 map bounds by
$H_f,T_f,U_f$ and $H_g,T_g,U_g$. Then

$$
C_W=L_{fy}\Lambda_4+4H_f\Lambda_3r+3H_f\Lambda_2^2
+6T_f\Lambda_2r^2+U_fr^4,
$$

$$
C_Z=q\Lambda_4+4H_g\Lambda_3r+3H_g\Lambda_2^2
+6T_g\Lambda_2r^2+U_gr^4.
$$

With predecessor sizes $\rho,C_N,C_M,C_F$,

$$
C_O=C_Z+\rho C_W+\frac{4C_NC_U}{\alpha}
+\frac{3C_NC_F^2}{\alpha^2}+\frac{6C_MC_F}{\alpha},
$$

$$
\Lambda_{4,\mathrm{out}}=\frac{C_O}{\alpha^4}.
$$

Thus $\Lambda_{4,\mathrm{out}}\le\Lambda_4$ preserves the C4 class.

## Conditional C4,1 class

Let $V_f,V_g$ bound the fiber/input Lipschitz increments of the fourth map
derivatives, and let $\Xi_4=\operatorname{Lip}(D^4h)$. The exact order-five
partition bound is

$$
\begin{aligned}
C_{W,1}={}&L_{fy}\Xi_4+5H_f\Lambda_4r
+10H_f\Lambda_3\Lambda_2+10T_f\Lambda_3r^2\\
&+15T_f\Lambda_2^2r+10U_f\Lambda_2r^3+V_fr^5,
\end{aligned}
$$

with $f$ replaced by $g$ and $L_{fy}$ by $q$ for $C_{Z,1}$. If
$C_T,C_N^{(1)},C_M^{(1)},C_P,C_U^{(1)}$ are predecessor point moduli, put

$$
C_{LP}=\frac{C_F^2}{\alpha^2}+\frac{C_P}{\alpha}.
$$

Then

$$
\begin{aligned}
C_{O,1}={}&C_{Z,1}+C_TC_W+\rho C_{W,1}\\
&+4\left(\frac{C_N^{(1)}C_U}{\alpha}
+\frac{C_NC_FC_U}{\alpha^2}+\frac{C_NC_U^{(1)}}{\alpha}\right)\\
&+3\left(\frac{C_N^{(1)}C_F^2}{\alpha^2}
+\frac{2C_NC_FC_{LP}}{\alpha}\right)\\
&+6\left(\frac{C_M^{(1)}C_F}{\alpha}+C_MC_{LP}\right),
\end{aligned}
$$

$$
\Xi_{4,\mathrm{out}}=\frac{C_{O,1}}{\alpha^5}
+\frac{4C_OC_F}{\alpha^6}.
$$

When $L_{fy}>0$, require $\Xi_{4,\mathrm{out}}\le\Xi_4$. When
$L_{fy}=0$, all graphs share the same inverse and this gate is bypassed.

## Five-layer difference recurrence

Order the distance vector as $(j,f,e,d,\delta)$. The exact predecessor
coefficient vectors are

$$
\Delta L\preceq(0,0,0,L_{fy}/\alpha^2,A_\delta/\alpha^2),
$$

$$
\Delta P\preceq(0,0,L_{fy},P_d,P_\delta),
$$

$$
\Delta U\preceq(0,L_{fy},U_e,U_d,U_\delta),
$$

$$
\Delta T\preceq(0,0,0,\beta_1,c_{10}),
$$

$$
\Delta N\preceq(0,0,Q,N_d,N_\delta),
\qquad
\Delta M\preceq(0,Q,M_e,M_d,M_\delta).
$$

The new map vectors have the form

$$
\Delta W\preceq(L_{fy},W_f,W_e,W_d,W_\delta),
$$

$$
\Delta Z\preceq(q,Z_f,Z_e,Z_d,Z_\delta),
$$

where slotwise telescoping gives all displayed implementation coefficients.
Let $A=LP$ and
$\Delta A\preceq C_F\Delta L+\alpha^{-1}\Delta P$. Applying the product rule
to the five terms of $O$ gives the coefficient vector

$$
\begin{aligned}
\Delta O\preceq{}&\Delta Z+\rho\Delta W+C_W\Delta T\\
&+4\left(\frac{C_U}{\alpha}\Delta N+C_NC_U\Delta L
+\frac{C_N}{\alpha}\Delta U\right)\\
&+3\left(\frac{C_F^2}{\alpha^2}\Delta N
+\frac{2C_NC_F}{\alpha}\Delta A\right)\\
&+6\left(\frac{C_F}{\alpha}\Delta M+C_M\Delta A\right).
\end{aligned}
$$

Write its entries as $(Q,O_f,O_e,O_d,O_\delta)$. The output recurrence is

$$
j'\le\beta_{4,c}j+c_{43,c}f+c_{42,c}e+c_{41,c}d+c_{40,c}\delta,
$$

$$
\beta_{4,c}=\frac{Q}{\alpha^4},\quad
c_{43,c}=\frac{O_f}{\alpha^4},\quad
c_{42,c}=\frac{O_e}{\alpha^4},
$$

$$
c_{41,c}=\frac{O_d}{\alpha^4}+\frac{4C_OL_{fy}}{\alpha^5},
\quad
c_{40,c}=\frac{O_\delta}{\alpha^4}+\frac{4C_OA_\delta}{\alpha^5}.
$$

Strict $Q/\alpha^4<1$ plus all lower gates proves C4 regularity.

## Reductions, boundary, and findings

At zero base coupling and zero base nonlinear derivative bounds, every
$J,P,U,W$ correction vanishes and the complete class/recurrence certificate
equals triangular C4 coefficient-by-coefficient. At $Q/\alpha^4=1$, the
$cx|x|^3$ invariant family remains C3/non-C4.

- P0: none.
- P1: none under the declared D5 and C4,1 premises.
- P2: vector ordering is frozen as $(j,f,e,d,\delta)$; changing it silently
  would permute recurrence coefficients.
- The theorem contains no neural or observational input.

Reproduction uses `artifacts/coupled_c4_math_audit.py`.
