# Mathematics lane -- verified rational four-node contour enclosure

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-verified-contour-enclosure-20260825`

Scope: finite rational V1--V3 only. No float promotion, neural result,
biological metric, consciousness, or rank claim is made here.

## Exact field, normalization, and projector convention

Use $\mathbb Q(i)=\{a+ib:a,b\in\mathbb Q\}$, represented as pairs of
exact `Fraction`s. Exact Gaussian elimination remains in this field; a pivot
is zero exactly when both rational components are zero. For $w=a+ib$,
$|w|^2=a^2+b^2\in\mathbb Q$, so squared Frobenius norms are rational.
Binary `float` and Python `complex` are outside the input class.

Before any elimination or dyadic rounding, form exactly
$$
 \widetilde U=U/s_*,\quad\widetilde c=c/s_*,\quad\widetilde r=r/s_*,
$$
where $s_*>0$ shares the spectral unit of $U,c,r$. Thus every ensuing
calculation is dimensionless. Raw lower separation and resolvent upper are
recovered only as $\underline\delta=s_*\underline{\widetilde\delta}$
and $\overline R=\overline{\widetilde R}/s_*$.

The mandatory counterclockwise central quadrature is
$$
 z_k=c+ri^k,\qquad
 P_4=\frac14\sum_{k=0}^3(z_k-c)(z_kI-U)^{-1}.
$$
It approximates $P=(2\pi i)^{-1}\oint(zI-U)^{-1}dz$. The factor
$z_k-c$, its sign, and $1/4$ are essential: otherwise the strip theorem
does not bound the reported central Riesz projector. $P,P_4$, the strip
constant $M$, and its error are dimensionless; $\delta,r,\chi$ have
spectral unit, and a resolvent has inverse spectral unit.

## V1 -- exact inverse/Frobenius lower enclosure

Let $\widetilde A_k=(\widetilde c+\widetilde r i^k)I-\widetilde U$.
Exact elimination either proves a node singular or returns
$\widetilde A_k^{-1}\in\mathbb Q(i)^{n\times n}$. In the latter case set
$$
 \widetilde S_k=\|\widetilde A_k^{-1}\|_F^2\in\mathbb Q_{>0}.
$$

**Theorem V1.** If dyadics $q_k^-\le q_k^+$ satisfy
$(q_k^-)^2\le\widetilde S_k\le(q_k^+)^2$, then
$\ell_k=(q_k^+)^{-1}\le\sigma_{\min}(\widetilde A_k)$.

*Proof.* $\sigma_{\min}(A)=\|A^{-1}\|_2^{-1}\ge
\|A^{-1}\|_F^{-1}\ge(q_k^+)^{-1}$. $\square$

For $x=a/b\ge0$ and fixed $p\ge0$, take the unique integer $t$
with $t^2b\le a2^{2p}<(t+1)^2b$. Return $q^-=t/2^p$, and return
$q^+=q^-$ exactly when the left inequality is equality, otherwise
$(t+1)/2^p$. Integer division and `isqrt` find $t$; recomputing both
squared inequalities as integer comparisons certifies the enclosure. Empty
matrices, negative precision, and a zero pivot must be rejected.

## V2 -- exact four-node chord

Every point of the four-node circle is within
$$
 \chi=2r\sin(\pi/8)=r\sqrt{2-\sqrt2}
$$
of a node. If $0\le s_2^-\le\sqrt2$ is a dyadic lower enclosure and
$h^+\ge\sqrt{2-s_2^-}$ a dyadic upper enclosure, then
$\widetilde\chi^+=\widetilde r h^+\ge\widetilde\chi$. Verify exactly
$(s_2^-)^2\le2$ and $(h^+)^2\ge2-s_2^-$, not decimal output.

Put $\underline{\widetilde\delta}_4=\min_k\ell_k-\widetilde\chi^+$.

**Theorem V2.** If every node is invertible and
$\underline{\widetilde\delta}_4>0$, then
$$
 \inf_{|z-\widetilde c|=\widetilde r}\sigma_{\min}(zI-\widetilde U)
 \ge\underline{\widetilde\delta}_4,\qquad
 \sup\|(zI-\widetilde U)^{-1}\|_2\le
 \underline{\widetilde\delta}_4^{-1}.
$$

*Proof.* $\sigma_{\min}$ is 1-Lipschitz and
$\|(z-z_k)I\|_2=|z-z_k|\le\chi$. Apply V1 at the nearest node. Positive
lower separation proves resolvent-freedom. $\square$

Zero or negative output is only `VERIFIED_LOWER_BOUND_NONPOSITIVE`, never a
claim of contour crossing.

## V3 -- rational expansion and witness

For rational $q>1$, set $r_-=r/q$, $r_+=rq$, and $a=\log q$. Both
$q,a$ are dimensionless and $e^{4a}=q^4$ exactly. An admissible witness
has $V,\Lambda\in\mathbb Q(i)^{n\times n}$, $\Lambda$ diagonal,
$UV=V\Lambda$ checked entrywise, and $V$ exactly invertible. With
$d_j^2=|\lambda_j-c|^2$, its closed-annulus test is, for every $j$,
$$
 d_j^2<(r/q)^2\quad\hbox{or}\quad d_j^2>(rq)^2.
$$
Equality or an interior value fails closed. This excludes central-contour
eigenvalues too, because $r/q<r<rq$. Repeated eigenvalues are harmless;
defective matrices simply have no witness. The exact projector is
$$
 P=V\operatorname{diag}(1_{d_j^2<r^2})V^{-1}.
$$

**Theorem V3.** With this witness and positive V2 certificates on both
boundaries, central $P_4$ above satisfies
$$
 \|P_4-P\|_2\le {2M^+\over q^4-1},\qquad
 M^+=\max\{r_-/\underline\delta_-,r_+/\underline\delta_+\}.
$$

*Proof.* $f(\theta)=re^{i\theta}(c+re^{i\theta}I-U)^{-1}$ is analytic
on $|\Im\theta|\le\log q$, since the witness excludes its poles. On
the two edges the V2 bounds give the displayed $M^+$, including mandatory
radius factors. The maximum principle gives $\|f_m\|\le M^+e^{-a|m|}$.
The four-node trapezoid aliases exactly $f_{4\ell}$, so its error is at
most $2M^+\sum_{\ell\ge1}e^{-4a\ell}=2M^+/(q^4-1)$. This is an error for
the central $P_4$, not an inner/outer discrete projector. $\square$

## Counterexamples, spot check, and disposition

Run the exact-only spot check:

```powershell
.codex\hooks\python.cmd python _workspace\ce\brain-verified-contour-enclosure-20260825\artifacts\math_spotchecks.py
```

It verifies $V=\begin{psmallmatrix}1&1\\0&1\end{psmallmatrix}$,
$\Lambda=\operatorname{diag}(0,3)$, $U=V\Lambda V^{-1}$, with
$c=0,r=1,q=2$:
$$
 P=\begin{pmatrix}1&-1\\0&0\end{pmatrix},\quad
 P_4=\begin{pmatrix}1&-81/80\\0&-1/80\end{pmatrix},\quad
 \|P_4-P\|_F^2=1/3200.
$$
The exact identity $\frac14\sum_{w^4=1}w/(w-\lambda)=1/(1-\lambda^4)$
checks the trapezoid factor/sign.

Required fail-closed fixtures: $U=[1]$ gives a singular central node;
$U=[1/2],c=0,r=1$ gives true sampled minimum $1/2<\sqrt{2-\sqrt2}$
and hence a nonpositive V2 expression; with $q=2$, $U=[1/2]$ and
$U=[2]$ lie on annulus boundaries, while $U=[3/4]$ lies inside; the
Jordan block $\begin{psmallmatrix}0&1\\0&0\end{psmallmatrix}$ is
defective; and $U=[0],V=[1],\Lambda=[1]$ fails $UV=V\Lambda$.

**P0:** none under stated V1--V3 hypotheses. In particular, multiplicity,
defectiveness, central-boundary eigenvalues, and the sign/factor of $P_4$
are explicitly constrained.

**P1 corrected and retired by contract revision:** raw-unit fixed-bit dyadic
rounding is not rescaling-invariant: scalar $U=c=0,r=s_*=1,p=0$ has
$S=1,q^+=1$; after multiplying all spectral quantities by 2,
$S'=1/4$ but raw-grid $q^{+'}=1$, changing its normalized lower bound
from 1 to 1/2. Both are safe but the invariance control fails. The revised
contract normalizes first; then the two normalized inputs are identically 1,
so all dyadic branches, certificate status, and normalized outputs agree
exactly, while raw $\delta$ and $R$ rescale covariantly.

**P2:** $N=4$ Frobenius bounds can be conservative, and V3 is incomplete
for defective or non-rational-spectrum matrices. A failed certificate is not
a spectral-crossing claim.

Minimum implementation contract: exact $\mathbb Q(i)$ parser; mandatory
normalize-first arithmetic; exact inverses and all squared residual checks;
central $P_4$ only after central inverses pass; named singular/nonpositive
outcomes; V3 label only after two boundary certificates, valid witness,
closed-annulus exclusion, and the displayed central error; test every fixture
above plus the rescaling pair. No retry with changed precision, mesh, q, or
witness may retain the same certificate label.
