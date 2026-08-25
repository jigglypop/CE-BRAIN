# Mathematics lane

Status: COMPLETE

## W1. Exact construction theorem

For a square matrix $A\in\mathbb Q(i)^{n\times n}$, deterministic Gauss--Jordan elimination on $[A\mid I]$ uses only field operations in $\mathbb Q(i)$. If every column obtains a nonzero pivot, elementary row operations transform the left block to $I$ and the right block to a matrix $B$ satisfying $BA=I$. For square matrices over a field, a left inverse implies invertibility and $AB=I$; the implementation checks both identities exactly rather than relying on that implication.

If a pivot is unavailable, the processed column has no independent pivot and $A$ is singular. Applied to $A_{0k}=z_kI-\widetilde U_0$, this means $z_k$ is an exact nominal eigenvalue at that sampled contour node, so no nominal resolvent witness exists there.

## W2. Normalize-first invariance

Under common raw spectral rescaling $(U_0,c,r,s_*)\mapsto(aU_0,ac,ar,as_*)$ with $a>0$, every normalized $A_{0k}$ is identical. The deterministic pivot sequence, exact witnesses, and downstream componentwise certificate are therefore identical in normalized units. Raw robust separations and resolvent bounds retain the predecessor's scale covariance.

## W3. Composition with the residual theorem

For every constructed witness, $R_k=I-B_kA_{0k}=0$. The predecessor's interval residual becomes

$$
G_k^+=|B_k|^+D^+.
\tag{W3}
$$

This minimizes the exact nominal residual term but does not guarantee $\|G_k^+\|_1<1$ and $\|G_k^+\|_\infty<1$. Large or badly aligned uncertainty can still fail. Thus witness construction and interval-family certification are logically separate gates.

## Counterexamples and exclusions

For $U_0=[1]$, $c=0$, $r=1$, the $d_1=1$ node gives $A_{01}=0$ and exact construction must fail. Conversely, with $U_0=[0]$ and radius-one uncertainty, all four nominal inverses exist but the predecessor contraction reaches equality at a real node and the family remains uncertified. These controls prevent both “singular constructor means generic failure” and “exact nominal inverse guarantees robust family” overclaims.

Verdict: exact rational nominal witness generation is complete; float-to-rational rounding and weighted/block selection remain open.

