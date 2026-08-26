# Quantitative affine coupled-base C2 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The affine coupled C1 theorem left the graph-dependent inverse-map Hessian
unresolved. This successor expands that Hessian and every two-graph product
term. A C2,1 graph modulus is necessary precisely when the base depends on the
graph. The resulting second-order diagonal factor is $Q/\alpha^2$, with exact
lower-order cross coefficients. Focused validation passed 22 tests and graph
integration passed 223. This is a conditional theorem, not a neural or
consciousness result.

## 1. Definitions

For

$$
F_h(x)=A_tx+a_t+f_t(x,h(x)),
\qquad
Y_h(x)=B_th(x)+g_t(x,h(x)),
$$

put $L=DF_h$, $J=L^{-1}$, $K=DY_h$, $T=KJ$, $P=D^2F_h$, and
$R=D^2Y_h$. The second derivative of the graph transform is

$$
D^2(\mathcal Th)[u,v]
=N[J u,J v],
\qquad
N=R-TP.
$$

The C1 predecessor supplies $\|J\|\le\alpha^{-1}$,
$\|T\|\le\rho=s/\alpha$, $\|P\|\le C_F$, and $\|R\|\le C_Y$.
Thus $\|N\|\le C_Y+\rho C_F=:N_0$, and the output Hessian bound
$N_0/\alpha^2$ is exactly the predecessor's invariant-class bound.

## 2. C2,1 class

When $L_{fy}>0$, the two graph preimages differ. In addition to
$\|D^2h\|\le\Lambda$, require
$\operatorname{Lip}(D^2h)\le\Xi$ and normalized map-Hessian moduli
$T_f,T_g$. Direct expansion gives

$$
C_P=T_f(1+\kappa)^3+3H_f(1+\kappa)\Lambda+L_{fy}\Xi,
$$

$$
C_R=q\Xi+3H_g(1+\kappa)\Lambda+T_g(1+\kappa)^3,
$$

$$
C_T=\frac{C_Y}{\alpha}+\frac{sC_F}{\alpha^2},
\qquad
C_N=C_R+C_TC_F+\rho C_P.
$$

Changing $N$, both outer inverse Jacobians, and then the preimage yields

$$
\Xi_{\rm out}
=\frac{C_N}{\alpha^3}+\frac{2N_0C_F}{\alpha^4}.
$$

The class gate is $\Xi_{\rm out}\le\Xi$. At $L_{fy}=0$, the two
preimages coincide and this extra gate is not needed.

## 3. Coupled C2 theorem

Let $\delta,d,e$ denote value, first-derivative, and Hessian distances.
The predecessor bounds the state displacement by $Z\delta$, graph-tangent
displacement by $d+\Lambda r_x\delta$, and inverse-Jacobian displacement by
$\alpha^{-2}(L_{fy}d+A_\delta\delta)$. Expanding $P$ and $R$ gives

$$
\|P_1-P_2\|\le L_{fy}e+P_dd+P_\delta\delta,
$$

$$
\|R_1-R_2\|\le qe+R_dd+R_\delta\delta.
$$

With $\|T_1-T_2\|\le\beta_1d+c_1\delta$,

$$
\|N_1-N_2\|\le Qe+N_dd+N_\delta\delta,
$$

where

$$
N_d=R_d+C_F\beta_1+\rho P_d,
\qquad
N_\delta=R_\delta+C_Fc_1+\rho P_\delta.
$$

**Conditional theorem.** If the coupled C1 certificate passes, the required
C2,1 class gate passes, and

$$
\beta_{2,c}=\frac{Q}{\alpha^2}<1,
$$

then the unique invariant graph is C2 and

$$
e_{n+1}\le\beta_{2,c}e_n+c_{21,c}d_n+c_{20,c}\delta_n,
$$

where

$$
c_{21,c}=\frac{N_d}{\alpha^2}
+\frac{2N_0L_{fy}}{\alpha^3},
\qquad
c_{20,c}=\frac{N_\delta}{\alpha^2}
+\frac{2N_0A_\delta}{\alpha^3}.
$$

Proof. The displayed $P,R,T$ differences bound the middle tensor
$N=R-TP$. The inverse-Jacobian identity bounds each outer argument. Changing
the middle tensor and then the two outer arguments gives the stated three
coefficients. Together with the predecessor value and derivative recurrences,
the system is upper triangular with diagonal $Q,\beta_1,\beta_{2,c}<1$.
Uniform convergence through Hessians makes the fixed graph C2. □

## 4. Reduction and boundary

At full zero coupling, $\alpha=1/\mu$, $Q=q$, $r_x=0$, and the
coefficients reduce exactly to the triangular C2 result:

$$
\beta_{2,c}=q\mu^2,
\quad
c_{21,c}=2\mu^2K_2(1+\kappa),
\quad
c_{20,c}=\mu^2\{K_2\Lambda+K_3(1+\kappa)^2\}.
$$

At equality, $x'=x/2$, $y'=y/4$ and $h_c(x)=cx|x|$ retain the
C1/non-C2 counterexample.

## 5. Evidence ceiling and reproducibility

The exact apparatus preserves supplied dimensions $1,4,5,6,100$ but selects
none. It does not establish nonaffine/local C2, C3+, a biological chart,
measured neural constants, consciousness, or 4--6 dimensions. Commands and
raw counts are recorded in `31-validation.md`; the focused seam is
`tests/test_quantitative_coupled_c2_graph_transform.py`.

## References

Formal dependencies are the repository's final-gated affine coupled C1 and
affine triangular C2 runs. No external empirical source is used.
