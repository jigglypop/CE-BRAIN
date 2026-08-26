# Quantitative affine coupled-base C1 graph transform

Status: COMPLETE

Date: 2026-08-25

## Abstract

The affine coupled-base Lipschitz graph transform is promoted to $C^1$ on an explicitly
invariant $C^{1,1}$ graph class. The proof controls both the graph-dependent base preimage
and the inverse-Jacobian difference. Its derivative recurrence has factor
$\beta_c=Q/\alpha$ and an explicit value-to-derivative cross coefficient. Exact software
certificates and boundary controls pass 21 focused tests and 177 integrated tests.

## Result

Let

$$
x'=A_tx+a_t+f_t(x,y),\qquad y'=B_ty+g_t(x,y)
$$

satisfy the predecessor coupled-Lipschitz gates, with
$q=b+L_{gy}$, $\alpha=\mu^{-1}-L_{fx}-L_{fy}\kappa>0$,
$s=q\kappa+L_{gx}$, and
$Q=q+sL_{fy}/\alpha<1$. On the graph class
$\|Dh\|\le\kappa$, $\operatorname{Lip}(Dh)\le\Lambda$, define

$$
C_F=H_f(1+\kappa)^2+L_{fy}\Lambda,\qquad
C_Y=q\Lambda+H_g(1+\kappa)^2,
$$

$$
\Lambda_{\rm out}=\frac{C_Y}{\alpha^2}
+\frac{sC_F}{\alpha^3}.
$$

If $\Lambda_{\rm out}\le\Lambda$ and $\beta_c=Q/\alpha<1$, the graph
transform preserves that $C^{1,1}$ class and the unique Lipschitz fixed graph is $C^1$.
For two iterates,

$$
\delta_{n+1}\le Q\delta_n,\qquad
d_{n+1}\le\beta_cd_n+c_c\delta_n,
$$

where $c_c$ is the explicit coefficient frozen in `11-math.md` and returned exactly by
the implementation. If $L_{fx}=L_{fy}=H_f=0$, the factor reduces to $q\mu$ exactly.
At $q\mu=1$, the local family $h_c(x)=c|x|$ prevents any non-strict promotion.

## Evidence ceiling

This closes the affine coupled-base first-derivative gap only under supplied uniform
constants. It does not establish a nonaffine or local coupled chart, $C^2$ or higher
regularity, estimate any constant from neural observations, identify consciousness, or
select dimension 4--6. The tests verify exact implications of declared inputs; they do not
show that a biological brain satisfies those inputs.
