# Induced-norm interval tightening mathematics

Status: COMPLETE

## Theorem T1 -- entry box to induced norm

For a normalized perturbation satisfying
$|\Re\widetilde\Delta_{ij}|\le\widetilde a_{ij}$ and
$|\Im\widetilde\Delta_{ij}|\le\widetilde b_{ij}$, let exact outward
enclosures obey

$$
c_{ij}^+\ge\sqrt{\widetilde a_{ij}^2+widetilde b_{ij}^2}.
$$

Then $|\widetilde\Delta_{ij}|\le c_{ij}^+$. Therefore

$$
\|\widetilde\Delta\|_1
=\max_j\sum_i|\widetilde\Delta_{ij}|
\le L_1^+:=\max_j\sum_i c_{ij}^+,
$$

and analogously

$$
\|\widetilde\Delta\|_\infty
\le L_\infty^+:=\max_i\sum_jc_{ij}^+.
$$

For every complex square matrix $A$,

$$
\|A\|_2^2=\rho(A^*A)
\le\|A^*A\|_\infty
\le\|A^*\|_\infty\|A\|_\infty
=\|A\|_1\|A\|_\infty.
$$

Consequently any exact outward enclosure

$$
\varepsilon_{1\infty}^+
\ge\sqrt{L_1^+L_\infty^+}
$$

is a valid operator-norm upper for the entire rectangular family.

## Theorem T2 -- deterministic minimum remains an upper

If $x\le A$ and $x\le B$, then $x\le\min(A,B)$. Applying this elementary
order fact with $x=\|\widetilde\Delta\|_2$, the predecessor Frobenius upper
$\varepsilon_F^+$, and T1 gives

$$
\|\widetilde\Delta\|_2
\le\varepsilon_*^+
:=\min(\varepsilon_F^+,\varepsilon_{1\infty}^+).
$$

Thus every predecessor proof remains valid after substituting the smaller
upper. This is not post-hoc theorem selection: both valid bounds are always
computed from the same frozen box, and `min` itself is the preregistered
formula.

## Non-domination and strict improvement controls

Neither raw candidate should replace the other globally.

For $C=I_n$, the Frobenius radius is $\sqrt n$, while
$\sqrt{\|C\|_1\|C\|_\infty}=1$; T1 is strictly tighter. For

$$
C=\begin{pmatrix}1&1\\1&0\end{pmatrix},
$$

the Frobenius radius is $\sqrt3$, while the induced candidate is $2$;
Frobenius is strictly tighter. For a scalar or dense constant square matrix,
the exact unrounded candidates tie. Hence the frozen best-of-two rule is
necessary to guarantee no regression.

The tightening can change a certificate outcome legitimately. Suppose a
positive nominal margin is $\delta$ and a diagonal $n$-entry box has common
radius $c$ with

$$
\delta/\sqrt n<c<\delta.
$$

The Frobenius bound $\sqrt n c$ fails the strict margin while the induced
bound $c$ passes. The family is not changed between the two computations.

## Scale and rounding audit

Every $a,b,c,L_1,L_\infty,\varepsilon$ has spectral unit before
normalization. After division by $s_*$ all are dimensionless. The product
$L_1L_\infty$ is dimensionless squared, and its square root is dimensionless.
Applying fixed dyadic grids to normalized entry magnitudes and the normalized
product makes every bracket, selected method, margin decision, and projector
bound invariant under common positive rational unit rescaling.

Outward rounding is monotone through the construction: increasing any
$c_{ij}$ cannot decrease either max sum, their product, or its square-root
upper. Thus nested upper enclosures remain safe.

## Status audit

- P0/P1: none under the frozen finite exact-endpoint hypotheses.
- P2: per-entry dyadic rounding can make T1 conservative; increasing exposed
  precision can reduce but never invalidate the upper.
- Residual/Krawczyk and statistical coverage remain separate open routes.
- No empirical, neural, consciousness, or dimension claim follows.
