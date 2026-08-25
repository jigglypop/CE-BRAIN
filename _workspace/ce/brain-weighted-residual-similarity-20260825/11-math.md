# Mathematics lane

Status: COMPLETE

## V1. Similarity-residual theorem

Entrywise positivity of $W$ makes (V1) exact. Since
$I-B'_kA'_k=W^{-1}(I-B_kA_{0k})W$ and every admissible perturbation satisfies
$|W^{-1}\Delta W|\le W^{-1}D^+W$, the predecessor's componentwise Banach argument applies verbatim to $A'_k$. Strict $1$- and $\infty$-contractions give

$$
\|(A'_k)^{-1}\|_2
\le\sqrt{M'_{1k}M'_{\infty k}}.
$$

The exact dyadic upper used by the apparatus can only enlarge the right side.

## V2. Translation to the original norm

Submultiplicativity gives

$$
\|A_{0k}^{-1}\|_2
\le\|W\|_2\|(A'_k)^{-1}\|_2\|W^{-1}\|_2.
$$

For positive diagonal $W$, the product is exactly
$\max_iw_i/\min_iw_i$. Taking reciprocals proves (V3). Both $\ell_{uk}$ and $\ell_{wk}$ are lower bounds for the same original-coordinate singular value, so their maximum remains a valid lower. The singular-value Lipschitz/chord theorem is also in the original norm, proving (V4).

## V3. Conditioning counterexample

With $A'=\begin{pmatrix}1&1\\0&1\end{pmatrix}$ and
$W=\operatorname{diag}(K,1)$, the original matrix is
$A=\begin{pmatrix}1&K\\0&1\end{pmatrix}$. Its inverse applied to $(0,1)^T$ has norm $\sqrt{K^2+1}$, so $\|A^{-1}\|_2\ge\sqrt{K^2+1}$. A transformed lower of order one cannot be used unchanged for $A$ as $K\to\infty$; the conditioning penalty is essential.

## V4. Status separation

A weighted node contraction can succeed while the translated lower minus the original chord is nonpositive. Conversely, if the supplied weight is ineffective, the deterministic maximum preserves the unweighted lower. Thus weighting is a rigorous optional tightening, not permission to discard the predecessor result or chord gate.

Verdict: the declared exact diagonal-similarity route is a conditional theorem. Weight optimization, block geometry, float construction, and empirical preselection remain open.

