# Mathematics lane

Status: COMPLETE

## CIJ.1 Composition identity and the correct isolated partition

Work in normalized Banach coordinates and write

$$Y_h=T_h\circ F_h.$$

For `m=(m_1,...,m_n)` with `sum(j m_j)=n`, put

$$|m|=\sum_jm_j,\qquad
C_n(m)=\frac{n!}{\prod_j(j!)^{m_j}m_j!}.$$

The finite Faà di Bruno identity is

$$
D^nY_h=\sum_{m\in\mathfrak P_n}C_n(m)
D^{|m|}T_h\prod_{j=1}^n(D^jF_h)^{m_j}.
$$

The unknown `D^nT_h` occurs only when there are `n` singleton input blocks:

$$s_n=(n,0,\ldots,0).$$

This is not `e_n=(0,...,0,1)`: the latter is the known term
`DT_h D^nF_h`.  Confusing these two partitions invalidates the implicit
recursion.

## CIJ.2 Size recurrence

Let `alpha>0` be a common lower conorm of `DF_h`, and let `F_j`, `Y_j`, and
`X_j` bound `D^jF_h`, `D^jY_h`, and `D^jT_h`.  Define

$$
B_n=Y_n+\sum_{m\in\mathfrak P_n\setminus\{s_n\}}C_n(m)
X_{|m|}\prod_{j=1}^nF_j^{m_j}.
$$

Since `||A compose (DF_h)^{-tensor n}|| <= alpha^{-n}||A||`, isolation of
the leading term proves

$$X_n\le \alpha^{-n}B_n.$$

The recursion is well-founded because every retained partition has
`|m|<n`.  The first nontrivial numerators are

$$B_2=Y_2+X_1F_2,$$

$$B_3=Y_3+3X_2F_1F_2+X_1F_3,$$

$$B_4=Y_4+6X_3F_1^2F_2+3X_2F_2^2+4X_2F_1F_3+X_1F_4.$$

## CIJ.3 Complete two-graph recurrence

All differences below are taken in the matched output coordinates required by
the raw envelopes.  Let `delta F_j`, `delta Y_j`, and `delta X_j` be their
nonnegative coefficient rows over graph distances `Delta_0,...,Delta_j`.
Product telescoping gives

$$
\delta B_n=\delta Y_n+
\sum_{m\ne s_n}C_n(m)\left[
(\delta X_{|m|})\prod_jF_j^{m_j}
+X_{|m|}\sum_jm_j(\delta F_j)F_j^{m_j-1}
\prod_{\ell\ne j}F_\ell^{m_\ell}
\right].
$$

The inverse identity
`DF_h^{-1}-DF_k^{-1}=DF_h^{-1}(DF_k-DF_h)DF_k^{-1}`
and telescoping of `n` inverse tensor slots prove

$$
\boxed{\delta X_n\preceq
\alpha^{-n}\delta B_n+nB_n\alpha^{-(n+1)}\delta F_1.}
$$

The second term is indispensable: it is the graph-dependent inverse
correction and vanishes in the common-inverse branch.  Because all operands
are nonnegative norm envelopes, repeated product telescoping proves the row by
induction without cancellation assumptions.

## CIJ.4 Boundaries and reductions

If `F_j=0` for `j>=2` and `F_1=alpha`, then
`X_n=Y_n/alpha^n` at every finite order.  If a diagonal coefficient
`beta_n` equals one, the upper-triangular recurrence is noncontracting at that
level; the implementation therefore requires `beta_n<1`, not `<=1`.

The procedure preserves the supplied base dimension.  It does not select
dimension 4--6.  A finite tuple through order `n` also supplies neither a
uniform-in-n estimate nor C-infinity, analytic, or Gevrey regularity.

Most importantly, CIJ.1--CIJ.3 begin only after valid raw `F/Y` jets are
available.  They close the universal implicit algebra but not the remaining
map-specific raw-jet generator.
