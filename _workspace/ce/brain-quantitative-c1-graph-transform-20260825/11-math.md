# Mathematics lane

Status: COMPLETE

## D1. Derivative graph transform

For $x=A_t^{-1}(x'-a_t)$, the triangular graph transform satisfies

$$
D(\mathcal Th)(x')
=\{B_tDh(x)+D_xg_t(x,h(x))+D_yg_t(x,h(x))Dh(x)\}A_t^{-1}.
\tag{D7}
$$

The predecessor slope condition bounds its norm by $\kappa$.

## D2. Difference recurrence

At the same base preimage $x$, subtract (D7) for $h$ and $\widehat h$. The terms multiplying $Dh-D\widehat h$ are bounded by $q\mu=\beta$. The change in $D_yg$ is at most $H_y\|h-\widehat h\|_\infty$ and multiplies a derivative bounded by $\kappa$; the change in $D_xg$ is at most $H_x\|h-\widehat h\|_\infty$. This proves (D5) with $c_D=\mu(H_y\kappa+H_x)$.

Iteration gives (D6). If $q,\beta<1$, the finite convolution tends to zero, including the repeated-root case $q=\beta$, where it is $nq^{n-1}$. Thus graph-transform iterates from C1 initial graphs are Cauchy in both value and derivative. The uniform derivative-limit theorem shows that the already unique $C^0$ fixed graph is $C^1$.

## D3. Equality boundary

For $(x,y)\mapsto(qx,qy)$, $\mu=1/q$ and $\beta=1$. On a local interval, $h_c(x)=c|x|$ is invariant because $h_c(qx)=q h_c(x)$, is Lipschitz, and is nondifferentiable at zero for $c\ne0$. Therefore the strict bunching condition cannot be replaced by equality in a theorem asserting forced C1 regularity.

Verdict: affine triangular C1 promotion and exact derivative recurrence are proved. Coupled/nonaffine/higher-smooth and empirical routes remain open.

