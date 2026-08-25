# Math lane — infinite history and certified circles

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

This lane proves conditional operator statements and records their exact
domains.  It does not validate a neural mechanism, a whole-brain geometry,
consciousness, or any preferred rank.  All predecessor P0 retirements remain
active: edge terms without a coercive baseline, generic skew neutrality,
loop-forced rank 4--6, and oblique-projector concentration are not revived.

## M1 — zero-fill history is a particular, not coupled, semigroup

Fix one edge, write $H_\rho=L^2(( -\infty,0],e^{2\alpha s}ds;\mathbb R^q)$
with $\alpha>0$, and define, for $t\geq0$,

$$
(T_0(t)h)(s)=
\begin{cases}
h(s+t),&s+t\leq0,\\
0,&-t<s\leq0.
\end{cases}
$$

**Theorem M1.1 (zero-fill shift).** $T_0$ is a $C_0$ semigroup on $H_\rho$,
its exact operator norm is $\|T_0(t)\|=e^{-\alpha t}$, and its generator is

$$
Gh=\partial_sh,
\qquad D(G)=\{h\in W^{1,2}_\rho(( -\infty,0];\mathbb R^q):h(0)=0\}.
$$

In particular $D(G)$ is dense and $G$ is closed.

*Derivation.* The isometry $Jh=e^{\alpha s}h$ maps $H_\rho$ to ordinary
$L^2(( -\infty,0])$.  Direct substitution gives

$$
\|T_0(t)h\|_\rho^2=e^{-2\alpha t}\|h\|_\rho^2.
$$

Thus the stated norm is attained in the essential-supremum sense.  After
conjugation, $JT_0(t)J^{-1}=e^{-\alpha t}S(t)$, where $S(t)f(s)=f(s+t)$ for
$s+t\le0$ and is zero otherwise.  The standard killed left-translation
semigroup is strongly continuous, with generator $f'$ on
$\{f\in W^{1,2}:f(0)=0\}$.  Conjugating gives $J GJ^{-1}=\partial_s-\alpha$
and hence the displayed $G$.  Density follows because
$C_c^\infty(( -\infty,0);\mathbb R^q)\subset D(G)$ is dense; closedness
follows from the closed-generator theorem (equivalently from this conjugacy).

**Boundary/sign counterexamples (P0).** This is not the history equation with
a node-supplied boundary.  If $x(t)\equiv1$ and $h_t(s)=x(t+s)$, then
$h_t\equiv1\in H_\rho$ and $h_t(0)=1$, whereas $h_t\notin D(G)$ and
$T_0(t)h_0$ is zero on $(-t,0]$.  A coupled delay system instead needs an
extended state $(x,h)$ and a trace condition $h(0)=B x$ (with compatibility
and a specified node equation); it cannot be replaced by $h(0)=0$.
Moreover, assigning $-\partial_s$ with this same outflow boundary has the
wrong transport direction.  The un-killed right translation
$h(s)\mapsto h(s-t)$ has norm $e^{\alpha t}$ and requires no boundary value
at $0$.  Thus both an unproved boundary condition and the reversed sign break
the claimed forgetting semigroup.

For the full direct sum, the coordinatewise product semigroup has a uniform
exponential bound only when the chosen edge rates have a common lower bound,
for example $\inf_e\alpha_e\ge\alpha_*>0$; then
$\|\bigoplus_eT_{0,e}(t)\|\le e^{-\alpha_*t}$.  Without it, it remains a
coordinatewise contraction semigroup under the usual direct-sum construction,
but no positive common decay rate follows.

## M1 — unbounded edge forms live on a form domain

Let $\mathcal H$ be a real Hilbert space and $V\hookrightarrow\mathcal H$
be dense and continuous.  The following are sufficient hypotheses, not
automatic consequences of writing $D_e^*K_eD_e$:

1. $a_{0,x}$ is a densely defined, symmetric, closed form on a common $V$ and
   $a_{0,x}(u,u)\ge m\|u\|_\mathcal H^2$ for $m>0$.
2. $B_e(x)=K_e(x)^{1/2}D_e:V\to E_e$ is well-defined and closed in the
   relevant graph/form topology, $K_e(x)\succeq0$, and $b_e\ge0$.
3. The series $\sum_e b_e\|B_e(x)u\|^2$ is finite on $V$, and the norm

$$
\|u\|_{V,x}^2=\|u\|_\mathcal H^2+a_{0,x}(u,u)+
\sum_e b_e\|B_e(x)u\|^2
$$

   is complete (locally uniformly in $x$).  A usable sufficient check is a
   locally uniform summable form bound
   $\sum_e b_e\|B_eu\|^2\le C_x[a_{0,x}(u,u)+\|u\|^2]$ together with
   closedness of the summed form.
4. Any asserted $C^k$ dependence is in form sense on this fixed $V$, with
   locally uniform derivative bounds; it is not inferred from pointwise
   matrix notation.

**Theorem M1.2 (form representation, conditional).** Under these hypotheses

$$
a_x^{(b)}(u,v)=a_{0,x}(u,v)+\sum_e b_e\langle B_e(x)u,B_e(x)v\rangle
$$

is a densely defined closed lower-bounded form.  The closed-form
representation theorem supplies one self-adjoint $A_x\ge mI$ with
$D(A_x)\subset V$ and
$a_x^{(b)}(u,v)=\langle A_xu,v\rangle$ for $u\in D(A_x),v\in V$.

This is a Hilbert/form-scale metric on $V$ (or on $D(A_x^{1/2})$), not yet a
strong Riemannian metric on $\mathcal H$.  The latter requires a bilinear form
defined and bounded on all $\mathcal H$, equivalently in this positive setting
$mI\preceq A_x\preceq MI$ for some finite $M$, or a separately specified
bounded transform/model space with equivalent norm.

**Counterexample (P0).** Take $\mathcal H=L^2(0,1)$,
$V=H_0^1(0,1)$, and $a(u,v)=\int_0^1(u'v'+uv)ds$.  It is densely defined,
closed, and coercive, but its representative is $A=I-\partial_s^2$ with
Dirichlet domain $H^2\cap H_0^1$, an unbounded operator.  The form is not even
defined on arbitrary $L^2$ vectors, so calling it a strong metric on
$\mathcal H$ is false.  Likewise, merely taking a closed unbounded $D_e$
without a common complete form domain can make the displayed edge sum
undefined or nonclosed.

## M2 — a circle certificate needs verified lower inputs

Use the complex Euclidean vector norm and induced matrix $2$-norm.  For
$z_k=c+re^{2\pi ik/N}$, every $z\in\Gamma$ has a nearest node satisfying

$$
|z-z_k|\le2r\sin\frac{\pi}{2N}.
$$

This is the chord at angular separation at most $\pi/N$, not the arc length.
Since $\sigma_{\min}$ is 1-Lipschitz in the matrix $2$-norm,

$$
\sigma_{\min}(zI-U)\ge
\min_k\sigma_{\min}(z_kI-U)-2r\sin\frac{\pi}{2N}
=\widehat\delta_N.
$$

**Theorem M2.1 (full-circle lower certificate).** If the node singular-value
lower bounds and the chord term are rigorous lower/upper enclosures and
$\widehat\delta_N>0$, then the contour is resolvent-free and

$$
\inf_{z\in\Gamma}\sigma_{\min}(zI-U)\ge\widehat\delta_N,
\qquad
R_\Gamma:=\sup_{z\in\Gamma}\|(zI-U)^{-1}\|_2\le\widehat\delta_N^{-1}.
$$

The second conclusion uses the exact square-matrix identity
$\|A^{-1}\|_2=1/\sigma_{\min}(A)$.  A negative or zero sampled expression is
only a failed certificate, not evidence of a contour crossing.

Ordinary float64 SVD/trigonometric output gives an estimate of
$\widehat\delta_N$, not a rigorous certificate: rounded node locations or an
overestimated $\sigma_{\min}$ can produce a false positive.  Exact-real
arithmetic would suffice if every required quantity were exactly enclosed;
in executable work the practical sufficient route is outward-rounded interval
arithmetic (including node coordinates, matrix entries, singular-value lower
bounds, and an upper enclosure of the chord).  The label `verified finite
arithmetic` is unavailable to unvalidated float64 output.

## M2 — annular analytic-strip bound

Let $r_-=re^{-a}$ and $r_+=re^a$.  Suppose $a>0$, the closed annulus
$r_-\le|z-c|\le r_+$ contains no spectrum, and each boundary circle has a
rigorous full-circle lower certificate $\delta_\pm>0$.  Set

$$
f(\theta)=re^{i\theta}(c+re^{i\theta}I-U)^{-1}.
$$

For complex $\theta+i y$, its circle radius is $re^{-y}$: $y=a$ is the inner
circle and $y=-a$ the outer.  The matrix resolvent is analytic on the closed
strip under the annulus hypothesis.  The maximum principle, applied to scalar
matrix elements (or the subharmonic operator norm), gives

$$
\sup_{|\Im\theta|\le a}\|f(\theta)\|_2
\le M_a:=\max\left\{\frac{r_-}{\delta_-},\frac{r_+}{\delta_+}\right\}.
$$

The radius factors are necessary because $f$ contains $re^{i\theta}$.
For a $2\pi$-periodic analytic function bounded by $M_a$ on this closed
strip, its Fourier coefficients obey $\|f_j\|\le M_ae^{-a|j|}$.  Aliasing of
the trapezoid average therefore yields

$$
\left\|P_N-P\right\|_2
\le2M_a\sum_{\ell\ge1}e^{-a\ell N}
=\frac{2M_a}{e^{aN}-1},
$$

where $P=(2\pi)^{-1}\int_0^{2\pi}f(\theta)d\theta$ and $P_N$ is the
contract's trapezoid sum.  This theorem is conditional on *both* certified
boundaries and a spectrum-free annulus; boundary certificates alone do not
exclude an eigenvalue in the annulus.

**Adverse fixtures.** (i) $U=\operatorname{diag}(0.9,1.4)$ with $c=.5,r=.4$
has a contour eigenvalue: any positive certificate is invalid.  (ii) For
$U=\begin{pmatrix}0&M\\0&1\end{pmatrix}$ and $c=0,r=.4$, eigenvalue distance
is positive while the resolvent norm grows with $M$; eigenvalue margins alone
do not control pseudospectra.  (iii) An eigenvalue with
$r_-<|\lambda-c|<r_+$ makes the annular analytic proof unavailable even if
both boundaries are clear.  (iv) coarse $N$ can make the chord subtraction
nonpositive despite a clear contour.  (v) float64 values near zero can
overstate a lower singular-value bound; they require interval replacement.

## Findings and reproducibility

- **P0:** zero-fill and boundary-coupled history are distinct; coercive
  unbounded forms are not strong ambient metrics; float64 sampled certificates
  are not rigorous finite-arithmetic certificates.
- **P1:** none remaining under the explicit hypotheses above.
- **P2:** verified singular-value enclosures and a source-locked empirical
  model remain implementation/source tasks; no biological identification is
  inferred here.

No numerical artifact is needed: all counterexamples are exact finite or
functional-analytic witnesses.  The displayed derivations are independently
checkable from substitution, the Lipschitz singular-value inequality, and
Fourier aliasing; no executable result is claimed.
