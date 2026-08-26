# Mathematics

Status: COMPLETE

## RMESH.1 Admissible ordered mesh

Let `d_0,...,d_(N-1) in Q(i)` be distinct with `|d_k|^2=1`, `N>=3`.  Relative to
`d_0`, their polar order must make exactly one counterclockwise traversal.  For
every cyclic pair define
\[
 c_k=\operatorname{Re}(\overline d_kd_{k+1}),\qquad
 s_k=\operatorname{Im}(\overline d_kd_{k+1}).
\]
Require `s_k>0`, or `s_k=0,c_k=-1`.  Thus every oriented gap
`theta_k` lies in `(0,pi]`.  Duplicate, reversed, skipped-order, and multiple-winding
lists fail before node evaluation.

## RMESH.2 Exact maximum-gap chord

On the arc from `d_k` to `d_(k+1)`, the farthest point from its nearer endpoint is
the midpoint.  Its unit-circle distance is
\[
 h_k=2\sin(\theta_k/4)
     =\sqrt{2-\sqrt{2+2c_k}}.
\tag{RMESH-1}
\]
An outward computation first takes a lower dyadic bound for
`sqrt(2+2c_k)`, then an upper dyadic bound for the outer square root.  With
`h^+=max_k h_k^+` and normalized radius `r`, every contour point is within
\[
 \chi_{\mathcal M}^+=r h^+
\tag{RMESH-2}
\]
of a sampled node.

## RMESH.3 Residual full-circle theorem

For each node `z_k=c+r d_k`, check one supplied rational witness `B_k` using the
unchanged componentwise contraction theorem.  If all node lower bounds `ell_k`
exist and
\[
 \delta_{\mathcal M}=\min_k\ell_k-\chi_{\mathcal M}^+>0,
\tag{RMESH-3}
\]
then the entire interval family is invertible on the circle, its Riesz rank is
common, and
\[
 \sup_{z\in\Gamma,U}\|(zI-U)^{-1}\|_2\le\delta_{\mathcal M}^{-1}.
\]
The projector perturbation bound uses the same normalized radius, the tighter of
the Frobenius and induced `1/infinity` uncertainty uppers, and
`delta_M^-2`.

Proof.  Singular values are 1-Lipschitz under scalar shifts, so the lower at any arc
point is at least its nearer endpoint lower minus the distance in (RMESH-2).
Taking the minimum gives (RMESH-3).  The predecessor resolvent identity and Riesz
rank argument then apply on the complete geometric circle.  QED.

## RMESH.4 Exact reductions and counterexamples

- Four cardinal directions have `c_k=0`, so (RMESH-1) is exactly
  `sqrt(2-sqrt(2))`, reproducing every legacy residual node and chord output.
- For `U_0=0`, radius one, and scalar uncertainty `1/2`, the four-node chord makes
  (RMESH-3) nonpositive.  The ordered rational eight-node mesh using cardinal
  points and `(+-3/5,+-4/5)` has a smaller maximum gap and a positive margin on the
  unchanged box.
- A semicircle gap is valid but has a large conservative chord and need not pass.
- A node coinciding with the nominal spectrum fails exact witness construction at
  that node; this is separate from interval-family failure.
