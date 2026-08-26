# Mathematics lane

Status: COMPLETE

## AIG.1 Infinite majorants and quantitative inverse radius

Work on the complexification of a finite-dimensional base space.  Write

$$F(x)=Ax+N(x),$$

where A is bijective and `||A^-1||<=alpha^-1`.  Uniformly over the graph class,
assume the centered holomorphic Taylor coefficients obey

$$
\|D^jN(0)\|\le A_F B_F^j j!\quad(j\ge2).
$$

For an input radius r with `x_F=B_F r<1`, absolute Taylor summation gives

$$
N_r:=\sup_{\|x\|\le r}\|N(x)\|
\le A_F\frac{x_F^2}{1-x_F},
$$

$$
\Theta_r:=\sup_{\|x\|\le r}\|DN(x)\|
\le A_FB_F\left(\frac1{(1-x_F)^2}-1\right).
$$

If `Theta_r<alpha`, then for fixed y the map

$$Q_y(x)=A^{-1}(y-N(x))$$

is a contraction with factor `Theta_r/alpha`.  It maps the r-ball into itself
whenever

$$
\|y\|<\rho_{\rm avail}:=\alpha r-N_r.
$$

Consequently F has a unique holomorphic inverse on every strictly smaller
output ball `rho<rho_avail`.  Both strict inequalities are necessary for this
closed-ball contraction proof.

## AIG.2 Fiber composition and analytic class

Assume uniformly

$$
\|D^jY(0)\|\le A_YB_Y^j j!\quad(j\ge1),
\qquad \|Y(0)\|\le Y_0,
$$

with `x_Y=B_Yr<1`.  Then

$$
M_T:=\sup_{\|x\|\le r}\|Y(x)\|
\le Y_0+A_Y\frac{x_Y}{1-x_Y}.
$$

Thus `T=Y compose F^-1` is holomorphic and bounded by M_T on the requested
complex output ball.  If the graph class sup bound M_G satisfies `M_T<=M_G`,
the analytic class is invariant.  Equality is allowed but has no robust class
margin.

Assume additionally that the graph transform is a strict contraction with
factor `q_C<1` in the sup norm on this same complex holomorphic class.  Banach
iteration converges uniformly on the common complex ball.  Its limit is
holomorphic, so the fixed point is genuinely analytic rather than merely Cn
for every separately tested finite n.

## AIG.3 Safe Fréchet Cauchy and Gevrey consequences

One-dimensional Cauchy bounds control diagonal directional derivatives.
Passing to the full symmetric n-linear operator norm by complex polarization
costs at most `n^n/n!`; hence

$$
\|D^nT(0)\|\le \frac{n^nM_T}{\rho^n}
\le M_T\left(\frac3\rho\right)^n n!,
$$

where the last inequality uses `n^n<=3^n n!`.  This deliberately safe bound
avoids silently identifying diagonal and full multilinear norms.

The factorial envelope proves C-infinity.  Since

$$n!\le(n!)^s\qquad(s\ge1),$$

the same amplitude and exponential rate also give a Gevrey-s envelope for
every real `s>=1`.  The code prints exact finite prefixes and exact integer-s
weakenings, while the theorem covers all real s at least one.

## AIG.4 Exact fixture and non-promotion counterexample

For

`alpha=1`, `r=1/4`, `A_F=A_Y=1/10`, `B_F=B_Y=1`,
`rho=1/5`, `Y0=0`, `M_G=1/20`, and `q_C=1/2`,

$$
N_r=\frac1{120},\quad
\Theta_r=\frac7{90},\quad
\rho_{\rm avail}=\frac{29}{120},\quad
M_T=\frac1{30}.
$$

All strict margins are positive and the safe analytic rate is `3/rho=15`.

Conversely, the real smooth function `exp(-1/x^2)` for positive x, extended
by zero for nonpositive x, is C-infinity with every derivative zero at the
origin but is not analytic there.  Therefore neither an arbitrary finite jet
tuple nor even the full pointwise Taylor jet can replace the uniform complex
majorant hypotheses.
