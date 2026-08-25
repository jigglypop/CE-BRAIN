# Interval-family contour and projector mathematics

Status: COMPLETE

## Findings first

I1--I3 are valid under the contract's strict hypotheses. The bridge is robust
over every complex matrix in the declared rectangular box, not merely over
rational members. Its empirical limitation is equally strict: no theorem here
shows that an estimator's unknown error lies in that box.

## Lemma I0 -- rectangular box to operator-norm ball

For $U=U_0+\Delta\in\mathcal U(U_0;a,b)$, let

$$
S=\sum_{ij}(a_{ij}^2+b_{ij}^2).
$$

Then

$$
\|\Delta\|_2\le\|\Delta\|_F
=\left(\sum_{ij}|\Delta_{ij}|^2\right)^{1/2}
\le\sqrt S.
$$

Proof: each rectangular constraint gives
$|\Delta_{ij}|^2=(\Re\Delta_{ij})^2+(\Im\Delta_{ij})^2
\le a_{ij}^2+b_{ij}^2$. Sum and use
$\|\Delta\|_2\le\|\Delta\|_F$. No rationality of $\Delta$ is used. Therefore
an exact rational upper enclosure $\varepsilon^+\ge\sqrt S$ covers irrational
members as well. For a scalar complex interval the inequality is attained at
$\Delta=a+ib$, so the rectangular-to-radial step cannot be uniformly reduced.

## Theorem I1 -- uniform contour separation

Assume the predecessor proves

$$
\inf_{z\in\Gamma}\sigma_{\min}(zI-U_0)\ge\delta_0>0
$$

and every admitted perturbation satisfies $\|\Delta\|_2\le\varepsilon^+<
\delta_0$. For any unit vector $x$,

$$
\|(zI-U_0-\Delta)x\|
\ge\|(zI-U_0)x\|-\|\Delta x\|
\ge\sigma_{\min}(zI-U_0)-\|\Delta\|_2.
$$

Taking the infimum over unit $x$, then over $z\in\Gamma$, proves

$$
\inf_{U\in\mathcal U,z\in\Gamma}\sigma_{\min}(zI-U)
\ge\delta_0-\varepsilon^+>0.
$$

Thus every family member is resolvent-free on the whole circle and

$$
\sup_{U\in\mathcal U,z\in\Gamma}\|(zI-U)^{-1}\|_2
\le(\delta_0-\varepsilon^+)^{-1}.
$$

The strict inequality is necessary for a positive certificate. In the scalar
sharp model $U_0=0$, $\Gamma=\{|z|=1\}$, and $\Delta=1$, the exact nominal
margin and perturbation norm both equal one and $z=1$ becomes singular. Hence
replacing `<` by `<=` would be false.

## Theorem I2 -- Riesz rank and projector perturbation

For a fixed admitted $\Delta$, set $U_t=U_0+t\Delta$. Since
$\|t\Delta\|_2\le\varepsilon^+<\delta_0$, Theorem I1 keeps $\Gamma$ in the
resolvent set for every $t\in[0,1]$. The Riesz projection

$$
P_t=\frac{1}{2\pi i}\oint_\Gamma(zI-U_t)^{-1}\,dz
$$

depends continuously on $t$. In finite dimension $P_t^2=P_t$ and
$\operatorname{tr}P_t=\operatorname{rank}P_t$ is integer-valued. A continuous
integer-valued function on the connected interval is constant, proving

$$
\operatorname{rank}P(U)=\operatorname{rank}P(U_0).
$$

Let $R=(zI-U)^{-1}$ and $R_0=(zI-U_0)^{-1}$. The exact resolvent identity is

$$
R-R_0=R\Delta R_0.
$$

For a circle of radius $r$, its length is $2\pi r$, so

$$
\begin{aligned}
\|P(U)-P(U_0)\|_2
&\le\frac{1}{2\pi}(2\pi r)
\sup_{z\in\Gamma}\|R\|_2\,\|\Delta\|_2\,\|R_0\|_2\\
&\le\frac{r\varepsilon^+}{\delta_0(\delta_0-\varepsilon^+)}.
\end{aligned}
$$

The result is valid for nonnormal matrices because it uses singular values
and resolvents, not eigenvector orthogonality or eigenvalue distance alone.

## Corollary I3 -- one computable nominal approximation for the family

If the predecessor strip theorem supplies
$\eta_4^+\ge\|P_4(U_0)-P(U_0)\|_2$, then for every admitted $U$,

$$
\|P(U)-P_4(U_0)\|_2
\le\|P(U)-P(U_0)\|_2+\|P(U_0)-P_4(U_0)\|_2
\le\rho_P^++\eta_4^+.
$$

This explicitly separates uncertainty error from quadrature error. Omitting
either term would conflate two independent approximation mechanisms.

## Dimension and rescaling audit

$U,c,r,s_*,a,b,\delta_0,\varepsilon$ all carry one spectral unit. Their
normalized versions are dimensionless. Resolvent bounds have reciprocal
spectral unit in raw form and are dimensionless after multiplication by
$s_*$. The projector bound contains $r\varepsilon/\delta^2$ and is
dimensionless. If every raw spectral quantity is multiplied by $\lambda>0$,
then $S$ is multiplied by $\lambda^2$, $\sqrt S$, $\delta_0$, and
$\varepsilon$ by $\lambda$, while normalized inputs, status, resolvent after
normalization, and projector bounds remain invariant.

The executable route must normalize each radius before applying a fixed
dyadic grid. Rounding $\sqrt S$ in raw units first would make the normalized
certificate depend on the chosen unit and is therefore forbidden.

## Exact nonnormal spot-check family

Let

$$
U_0=\begin{pmatrix}0&0\\0&2\end{pmatrix},\qquad
U_e=\begin{pmatrix}0&e\\0&2\end{pmatrix},\qquad 0<e<1.
$$

On a circle centered at zero that separates $0$ from $2$, the exact spectral
projectors are

$$
P(U_0)=\begin{pmatrix}1&0\\0&0\end{pmatrix},\qquad
P(U_e)=\begin{pmatrix}1&-e/2\\0&0\end{pmatrix}.
$$

Thus $\|P(U_e)-P(U_0)\|_2=e/2$. This confirms that a matrix can keep exactly
the same eigenvalues and rank while its nonorthogonal spectral projector moves;
rank stability alone is not a small-projector-error theorem.

## Status audit

- P0: none in I0--I3.
- P1: no mathematical gap under the frozen finite-dimensional hypotheses.
- P2: the Frobenius box bound can be conservative. A candidate tightening is
  $\|\Delta\|_2\le\sqrt{\|C\|_1\|C\|_\infty}$ with
  $C_{ij}=\sqrt{a_{ij}^2+b_{ij}^2}$ and outward-rounded entry bounds; a
  residual/Krawczyk route could be sharper still. Neither is required for the
  correctness of the admitted I0 route.
- Empirical status: `UNVERIFIED`; coverage calibration for $a,b$ is absent.
