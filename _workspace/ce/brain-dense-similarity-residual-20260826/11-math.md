# Mathematics

Status: COMPLETE

## DSR.1 Exact similarity and uncertainty transport

Let `T in Q(i)^(n x n)` be invertible and set
\[
 A'_0=T^{-1}A_0T,\qquad B'=T^{-1}BT.
\tag{DSR-1}
\]
If the normalized uncertainty satisfies `|Delta| <= D` componentwise, then
\[
 |T^{-1}\Delta T|\le |T^{-1}|D|T|.
\tag{DSR-2}
\]
With outward rational magnitude matrices `C^- >= |T^-1|` and `C^+ >= |T|`, the
checker therefore uses
\[
 D'^+=C^-D^+C^+.
\tag{DSR-3}
\]
This is valid for full dense and block matrices; diagonal weighting is the special
case in which every product reduces entrywise.

## DSR.2 Rigorous original-norm condition bound

For any nonnegative magnitude upper `C`,
\[
 \|T\|_2\le\sqrt{\|C^+\|_1\|C^+\|_\infty}=:\tau^+,
 \quad
 \|T^{-1}\|_2\le\sqrt{\|C^-\|_1\|C^-\|_\infty}=:\iota^+.
\]
Outward dyadic square-root uppers give the exact rational certificate
\[
 \kappa_T^+=\tau^+\iota^+\ge\kappa_2(T).
\tag{DSR-4}
\]
If the transformed residual theorem yields
`||(A'_0+Delta')^-1||_2 <= M'_2`, then
\[
 \|(A_0+\Delta)^{-1}\|_2
 \le \kappa_T^+M'_2,
 \qquad
 \ell_T=1/(\kappa_T^+M'_2).
\tag{DSR-5}
\]

## DSR.3 Full-circle theorem

At every one of the four exact nodes, apply the predecessor residual contraction to
`A'_0`, `B'`, and (DSR-3).  Translate its node lower by (DSR-5).  The untransformed
lower and translated dense lower are both original-coordinate lower bounds, so
\[
 \ell_k^*=\max(\ell_{uk},\ell_{Tk}),\qquad
 \delta_T^*=\min_k\ell_k^*-\chi^+.
\tag{DSR-6}
\]
Only `delta_T^* > 0` proves the entire original contour free of the interval-family
spectrum and admits the predecessor common-rank, resolvent, and projector bounds.
The dense transform itself has the stronger diagnostic
\[
 \delta_{T,\mathrm{only}}=\min_k\ell_{Tk}-\chi^+,
\tag{DSR-7}
\]
which is reported separately.

Proof.  Equation (DSR-2) follows by the triangle inequality entry by entry.  The
induced `1/infinity` product bounds the spectral norm, giving (DSR-4).  Similarity
gives `(A_0+Delta)^-1=T(A'_0+Delta')^-1T^-1`, hence (DSR-5).  The predecessor chord
is already measured in the original normalized spectral units, so subtracting the
unchanged `chi+` in (DSR-6) is valid.  The predecessor contour and Riesz theorem
then applies.  QED.

## DSR.4 Reductions and counterexamples

- `T=I` exactly reproduces the untransformed certificate.
- For positive diagonal `T=W`, (DSR-3)--(DSR-5) reduce exactly to the existing
  diagonal weighted theorem, including `kappa_2(W)`.
- A nonidentity exact rational rotation close to identity has a positive
  dense-only full-circle fixture, proving the route is not merely syntactic.
- Omitting (DSR-4) is invalid: the predecessor shear family makes the original
  inverse norm grow without bound.
- Singular `T`, dimension mismatch, floats, booleans, and noncanonical numeric
  strings fail before any certificate is issued.
