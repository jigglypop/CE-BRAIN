# Mathematics lane

Status: COMPLETE

## NC4.1 Modified fourth tensor

Put `J=DF_h`, `P=D2F_h`, `U=D3F_h`, `W=D4F_h`, and
`K=DY_h`, `R=D2Y_h`, `V=D3Y_h`, `Z=D4Y_h`. With `L=J^-1`, define

$$T=KL,$$

$$N=R-TP,$$

$$M=V-TU-3N[LP,\cdot],$$

where the final term denotes cyclic symmetrization. Four differentiations of
`Y_h=(T h) compose F_h` give

$$
O=Z-TW-4N[LU,\cdot]-3N[LP,LP]-6M[LP,\cdot,\cdot],
$$

$$D^4(T h)=O[L,L,L,L].$$

For the nonaffine base, the one-graph fourth derivative bound is

$$
C_W=U_\phi+L_{fy}\Lambda_4+4H_f\Lambda_3r
+3H_f\Lambda_2^2+6T_f\Lambda_2r^2+U_fr^4,
$$

while

$$
C_Z=q\Lambda_4+4H_g\Lambda_3r+3H_g\Lambda_2^2
+6T_g\Lambda_2r^2+U_gr^4.
$$

Thus

$$
C_O=C_Z+\rho C_W+\frac{4C_NC_U}{\alpha}
+\frac{3C_NC_F^2}{\alpha^2}+\frac{6C_MC_F}{\alpha},
$$

and the generic class output is `C_O/alpha^4`.

## NC4.2 D5 point modulus and conditional C4,1

The base point modulus gains the previously absent term `V_phi`:

$$
\begin{aligned}
C_{W,1}={}&V_\phi+L_{fy}\Xi_4+5H_f\Lambda_4r
+10H_f\Lambda_3\Lambda_2\\
&+10T_f\Lambda_3r^2+15T_f\Lambda_2^2r
+10U_f\Lambda_2r^3+V_fr^5.
\end{aligned}
$$

`C_Z,1` has the same partition coefficients without `V_phi`. With the
predecessor point bounds,

$$
\begin{aligned}
C_{O,1}={}&C_{Z,1}+C_TC_W+\rho C_{W,1}\\
&+4(C_{N,1}C_U/\alpha+C_NC_{L,1}C_U+C_NC_{U,1}/\alpha)\\
&+3(C_{N,1}C_{LP}^2+2C_NC_{LP}C_{LP,1})\\
&+6(C_{M,1}C_{LP}+C_MC_{LP,1}).
\end{aligned}
$$

Then `Xi4_out=C_O,1/alpha^5+4 C_O C_F/alpha^6`. It is required only
when `L_fy>0`; at `L_fy=0` every graph has the same inverse.

## NC4.3 Five-layer coefficient vector

Freeze vector order `(j,f,e,d,delta)`. The affine coupled C4 vector algebra
remains valid, except

`Delta W=(L_fy,W_f,W_e,W_d,V_phi*r_x+W_delta_affine)`

and the predecessor vectors now contain all `H_phi,T_phi,U_phi` terms. The
base inverse difference uses the predecessor's full nonaffine `A_delta`, not
the affine reconstruction. If `Delta O=(Q,O_f,O_e,O_d,O_delta)`, then for
`L_fy>0`

$$
j'\le\frac{Q}{\alpha^4}j+\frac{O_f}{\alpha^4}f
+\frac{O_e}{\alpha^4}e
+\left(\frac{O_d}{\alpha^4}+\frac{4C_OL_{fy}}{\alpha^5}\right)d
+\left(\frac{O_\delta}{\alpha^4}+\frac{4C_OA_\delta}{\alpha^5}\right)\delta.
$$

Strict `Q/alpha^4<1` is mandatory.

## NC4.4 Exact common-inverse bypass

The generic absolute-value envelope is valid but not sharp at `L_fy=0`:
expanding `N` and `M` separately changes the direct inverse-chain coefficient
15 of `P^2R` to the conservative value 21. At this structural boundary use
the common inverse directly. Let `mu=1/alpha` and

$$\nu=C_F\mu^3,$$

$$\tau=C_U\mu^4+3C_F^2\mu^5,$$

$$\upsilon=C_W\mu^5+10C_FC_U\mu^6+15C_F^3\mu^7.$$

Then

$$
\Lambda_{4,\mathrm{out}}^{\rm common}
=\mu^4C_Z+6\mu^2\nu C_V+(3\nu^2+4\mu\tau)C_R
+\upsilon C_K.
$$

The same linear combination of the raw `Delta Z,Delta V,Delta R,Delta K`
vectors gives the sharp recurrence. This route reduces exactly to the global
nonaffine triangular C4 theorem. Setting all base-map nonlinear derivative
bounds to zero instead reduces every output exactly to affine coupled C4.

At the strict boundary `Q/alpha^4=1`, `h_c(x)=c*x*abs(x)^3` remains an
invariant C3/non-C4 family.

For the frozen graph-dependent fixture:

`Lambda4_out=77166708988912/11866484641625`,
`Xi4_out=3149203994659911392/81226087371923125`, and
`beta4=19712000/69343957`.
