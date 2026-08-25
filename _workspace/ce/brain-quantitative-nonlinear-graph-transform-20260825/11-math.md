# Quantitative triangular graph-transform mathematics

Status: COMPLETE

## Theorem G1 -- invariant graph family

Let $\mathcal G$ be the contract's graph-family space. It is closed in the
uniform sup-norm space of bounded continuous graph families and is therefore
complete.

For $h\in\mathcal G$, write $x=\phi_t^{-1}(x')$. The graph transform obeys

$$
\|(\mathcal Th)_{t+1}(x')\|
\le bR+G+L_yR=qR+G\le R.
$$

Thus it remains in the fiber tube. For $x'_1,x'_2$ with preimages $x_1,x_2$,

$$
\begin{aligned}
\|(\mathcal Th)(x'_1)-(\mathcal Th)(x'_2)\|
&\le (b\kappa+L_x+L_y\kappa)\|x_1-x_2\|\\
&\le\mu(q\kappa+L_x)\|x'_1-x'_2\|\\
&\le\kappa\|x'_1-x'_2\|.
\end{aligned}
$$

Hence the slope class is invariant. For two graphs evaluated at the same base
preimage,

$$
\|\mathcal Th-\mathcal Tk\|_\infty
\le(b+L_y)\|h-k\|_\infty=q\|h-k\|_\infty.
$$

If $q<1$, Banach's theorem supplies a unique fixed graph family. The graph map
$x\mapsto(x,h_t(x))$ is bi-Lipschitz onto its image when the product chart uses
the standard product norm, so its real graph dimension is the base dimension
$d$. This proves G1--G2 for the stated Lipschitz triangular subcase.

## Corollary G2 -- exponential window tracking

Let $y_t$ and $h_t(x_t)$ share the same base orbit. Invariance gives

$$
\begin{aligned}
\|y_{t+1}-h_{t+1}(x_{t+1})\|
&\le b\|y_t-h_t(x_t)\|\\
&\quad+L_y\|y_t-h_t(x_t)\|\\
&=q\|y_t-h_t(x_t)\|.
\end{aligned}
$$

Induction yields the exact $q^n$ tracking bound. This is a window count, not a
physical time constant.

## Boundary audit and counterexamples

The tube and slope inequalities may hold at equality: they still define a
self-map of the closed graph class. Their zero margins remove robustness but
not existence. By contrast, $q<1$ is strict. With identity base, $B=I$, and
$g=0$, one has $q=1$ and every constant graph is invariant; uniqueness and
attraction both fail. This is a complete counterexample to replacing `<` by
`<=` in G1a.

Tube or slope failure is only a failure of this sufficient certificate. A
particular invariant graph may still exist, so those statuses must not be
reported as nonexistence.

## Dimension and rescaling proof

$R_{\rm raw},G_{\rm raw},Y_*$ share fiber unit. $L_{x,\rm raw}$ and
$\kappa_{\rm raw}$ carry fiber/base unit, so multiplication by $X_*/Y_*$
closes them to dimensionless values. $\mu,b,L_y,q$ are dimensionless. Every
sum and margin in G1 is therefore dimensionally homogeneous.

Under independent coordinate rescalings $X\mapsto\lambda_X X$ and
$Y\mapsto\lambda_Y Y$, raw radii scale by $\lambda_Y$, while raw cross-slopes
scale by $\lambda_Y/\lambda_X$. The four normalized quantities and all margins
are invariant.

## What the theorem does not prove

The result assumes triangular base dynamics. If $x_{t+1}$ depends on $y_t$,
the same-base inverse used in the contraction comparison changes with the
graph, and the displayed $q$ is incomplete. The general predecessor theorem
requires a full invariant splitting and normal-hyperbolicity estimates.

The theorem accepts every positive declared $d$. Its logic is identical for
$d=1,4,5,6,100$; it cannot select 4--6. It supplies Lipschitz regularity only,
not $C^{r-1}$ smoothness, and no empirical premise is verified.

## Status audit

- P0/P1: none for the exact triangular theorem.
- P2: general coupled-base, differentiable bunching, and empirical constant
  estimation remain open.
- Consciousness/dimension identification remains prohibited.
