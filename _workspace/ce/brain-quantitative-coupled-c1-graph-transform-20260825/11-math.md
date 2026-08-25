# Mathematics lane

Status: COMPLETE

## J1. Derivative and inverse-Jacobian bounds

For $F_h(x)=A_tx+a_t+f_t(x,h(x))$ and
$Y_h(x)=B_th(x)+g_t(x,h(x))$,

$$
D(\mathcal Th)(x')=DY_h(x)[DF_h(x)]^{-1},
\quad x=F_h^{-1}(x').
$$

The predecessor gives $\|[DF_h]^{-1}\|\le\alpha^{-1}$ and
$\|DY_h\|\le s$. Along one graph, block expansion with the product norm gives
$\operatorname{Lip}(DF_h)\le C_F$ and
$\operatorname{Lip}(DY_h)\le C_Y$. Reparameterizing by $F_h^{-1}$ and using
$J_1-J_2=J_1(DF_2-DF_1)J_2$ gives
$\operatorname{Lip}(J\circ F_h^{-1})\le C_F/\alpha^3$. The product rule proves (J4).

## J2. Two-graph recurrence

At the same output base point, predecessor inversion gives
$\|x_1-x_2\|\le r_x\delta$. Hence

$$
\|(x_1,h_1(x_1))-(x_2,h_2(x_2))\|_\oplus
\le Z\delta.
$$

The C1,1 graph bound gives
$\|Dh_1(x_1)-Dh_2(x_2)\|\le d+\Lambda r_x\delta$.
Expanding $DF_1-DF_2$ yields

$$
\|DF_1-DF_2\|
\le L_{fy}d+A_\delta\delta,
$$

and expanding $DY_1-DY_2$ yields

$$
\|DY_1-DY_2\|
\le qd+Y_\delta\delta.
$$

Substitution in
$DY_1J_1-DY_2J_2=(DY_1-DY_2)J_1+DY_2(J_1-J_2)$ proves (J8)--(J9). Since $Q,\beta_c<1$, the same finite-convolution argument as in the triangular theorem gives derivative convergence and a C1 fixed graph.

## J3. Reduction and boundary

If $L_{fx}=L_{fy}=H_f=0$, then $\alpha=1/\mu$, $Q=q$, and
$\beta_c=q\mu$. Thus the coupled theorem reduces to the triangular C1 theorem. At $q\mu=1$, the local invariant $c|x|$ family remains a complete counterexample to forced differentiability.

Verdict: affine coupled C1 promotion is proved under an invariant C1,1 graph-class bound. Nonaffine coupled and C2/higher routes remain open.

