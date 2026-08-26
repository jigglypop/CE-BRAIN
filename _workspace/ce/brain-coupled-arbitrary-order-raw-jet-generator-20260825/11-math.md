# Mathematics lane

Status: COMPLETE

## CRJ.1 Matched-preimage graph geometry

Let `z=F_h(x_h)=F_k(x_k)` and suppose

$$|x_h-x_k|\le r_x\Delta_0.$$

For `G_h=(Id,h)`, use the product norm and define

$$R_1=1+\Lambda_1,\qquad R_j=\Lambda_j\quad(j\ge2).$$

Then the state displacement is bounded by

$$
|G_h(x_h)-G_k(x_k)|
\le S_0\Delta_0,
\qquad S_0=1+(1+\Lambda_1)r_x.
$$

For every `1<=j<=n`, same-point graph distance plus displacement of the
evaluation point gives

$$
\delta R_j\preceq \Delta_j+\Lambda_{j+1}r_x\Delta_0.
$$

Here `Lambda_(n+1)` may be a Lipschitz modulus of `D^n h`; existence of a
classical `D^(n+1)h` is not required.  Omitting this extra point modulus leaves
the matched-preimage difference unproved.

## CRJ.2 Raw composite sizes and rows

Let `K_b` bound `D^b a` and `H_b` its pointwise Lipschitz modulus on the covered
graph-state region.  For `A_h=a compose G_h`, finite Faà di Bruno gives

$$
A_n=\sum_{m\in\mathfrak P_n}C_n(m)K_{|m|}
\prod_jR_j^{m_j}.
$$

Changing the outer map derivative and then each graph-jet slot proves

$$
\delta A_n\preceq
\sum_mC_n(m)\left[
H_{|m|}S_0\Delta_0\prod_jR_j^{m_j}
+K_{|m|}\sum_jm_j(\delta R_j)R_j^{m_j-1}
\prod_{\ell\ne j}R_\ell^{m_\ell}
\right].
$$

All terms are nonnegative operator-norm envelopes, so the formula follows by
finite product telescoping.  It yields a complete D0..Dn row.  `H_n` changes
only the value coefficient at level n; `Lambda_(n+1)` also enters only through
the value displacement at that level.

The exact scalar fixture `R=(2,2,3,4)` and `K=(2,3,5,7)` yields

$$A_1=4,\quad A_2=16,\quad A_3=82,\quad A_4=468.$$

## CRJ.3 Coupled implicit composition

Apply CRJ.2 to `a=f` and `a=g`; call the results `F_n,delta F_n` and
`Y_n,delta Y_n`.  The predecessor theorem then gives

$$
B_n=Y_n+\sum_{m\ne(n,0,\ldots,0)}C_n(m)
X_{|m|}\prod_jF_j^{m_j},
$$

$$
X_n\le\alpha^{-n}B_n,
\qquad
\delta X_n\preceq\alpha^{-n}\delta B_n
+nB_n\alpha^{-(n+1)}\delta F_1.
$$

Thus supplied global normalized moduli generate every finite derivative layer,
its class margin, and its full upper-triangular recurrence row.  The curved C6
fixture has strict positive class and bunching margins.

## CRJ.4 Status boundaries

The theorem is conditional on the declared global region, conorm alpha,
preimage coefficient `r_x`, and all map/graph moduli.  It does not construct
the C0 invariant ball or prove those hypotheses from neural data.  Its
isotropic product norms may be more conservative than the explicit
anisotropic C1--C4 tensors.  A finite maximum order does not imply C-infinity,
analytic, or Gevrey regularity, and the input dimension is preserved rather
than selected.
