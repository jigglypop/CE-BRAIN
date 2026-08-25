# Mathematics lane

Status: COMPLETE

## C1. Graph-dependent base inversion

For a graph $h$ with $\operatorname{Lip}h\le\kappa$, solve
$x'=A_tx+a_t+f_t(x,h(x))$ by the fixed-point map

$$
\Psi_{x'}(x)=A_t^{-1}\{x'-a_t-f_t(x,h(x))\}.
$$

Its Lipschitz factor is at most $\mu(L_{fx}+L_{fy}\kappa)<1$, equivalent to $\alpha>0$. Banach's theorem gives one preimage. For two inputs on the same graph,

$$
\|x'_1-x'_2\|\ge\alpha\|x_1-x_2\|.
\tag{C7}
$$

For graphs $h_1,h_2$ and the same output base point, adding and subtracting $h_1(x_2)$ gives

$$
\|x_1-x_2\|\le\frac{L_{fy}}{\alpha}
\|h_1-h_2\|_\infty.
\tag{C8}
$$

## C2. Tube, slope, and transform contraction

The fiber image norm is bounded by $qR+G$, proving (C4). Along one graph, its fiber-output difference is at most
$(q\kappa+L_{gx})\|x_1-x_2\|$. Dividing by the base lower (C7) proves the slope condition (C5).

For two graphs at the same output base point, the fiber outputs differ by at most

$$
q\|h_1-h_2\|_\infty
+(q\kappa+L_{gx})\|x_1-x_2\|.
$$

Using (C8) proves the factor $Q$ in (C6). If $Q<1$, Banach's theorem on the complete graph-family space gives a unique invariant Lipschitz family.

## C3. Boundaries and triangular recovery

At $\alpha=0$, take $A=I$, $f(x,y)=-x$, so the base map is constant and cannot be reparameterized. At $Q=1$, the uncoupled identity fiber $y'=y$ has nonunique constant invariant graphs. Thus both strict inequalities are necessary for this sufficient theorem.

If $L_{fy}=L_{fx}=0$, then $\alpha=1/\mu$ and $Q=q$. The slope condition becomes $\mu(q\kappa+L_{gx})\le\kappa$, exactly the triangular predecessor after identifying $L_{gx}=L_x$.

Verdict: coupled-base Lipschitz theorem proved for the affine full-space chart; smooth/nonaffine/local-boundary extensions remain open.

