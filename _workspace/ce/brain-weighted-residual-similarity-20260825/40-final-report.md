# Exact weighted residual similarity bridge

Status: COMPLETE

Date: 2026-08-25

## Abstract

Componentwise residual bounds can be tightened by a diagonal similarity, but the transformed norm is not the original Euclidean norm. This run proves and implements the mandatory translation through the exact diagonal condition number. A declared positive rational weight is applied to the nominal node, inverse witness, and interval uncertainty before the existing residual gate; the resulting singular lower is divided by $\kappa_2(W)$ and compared with the unweighted lower. The original-coordinate chord remains mandatory. Focused validation passed 16 tests, residual integration 44, the complete contour chain 83, and the dimensionless gate 27. The result is an exact conditional weighted apparatus, not a weight optimizer, empirical selection rule, or neural-data result.

## 1. Weighted residual theorem

Let $W=\operatorname{diag}(w_i)$ with $w_i>0$ and define

$$
A'_k=W^{-1}A_{0k}W,
\qquad B'_k=W^{-1}B_kW,
\qquad D'^+=W^{-1}D^+W.
$$

The transformed componentwise residual is

$$
G_k'^+=|I-B'_kA'_k|^+ + |B'_k|^+D'^+.
$$

When its induced $1$- and $\infty$-norms are strictly below one, the predecessor theorem bounds $\|(A'_k)^{-1}\|_2$ by a checked dyadic upper $M'_{2k}$. Since
$A_{0k}^{-1}=W(A'_k)^{-1}W^{-1}$,

$$
\sigma_{\min}(A_{0k})
\ge \ell_{wk}
:=\frac{1}{\kappa_2(W)M'_{2k}},
\qquad
\kappa_2(W)=\frac{\max_iw_i}{\min_iw_i}.
$$

The common scaling of $w$ cancels, so the apparatus normalizes $\min_iw_i=1$.

## 2. Rigorous best-of-two and full circle

The unweighted $\ell_{uk}$ and translated weighted $\ell_{wk}$ bound the same original-coordinate singular value. Hence

$$
\ell_k^*=\max(\ell_{uk},\ell_{wk})
$$

is rigorous. The whole circle is certified only if

$$
\delta_w^*=\min_k\ell_k^*-\chi^+>0,
$$

where $\chi^+$ is the unchanged original-coordinate chord upper. A weighted contraction at all nodes is therefore insufficient by itself.

For $A'=\begin{pmatrix}1&1\\0&1\end{pmatrix}$ and
$W=\operatorname{diag}(K,1)$, the original inverse norm is at least
$\sqrt{K^2+1}$. This proves that omitting the factor $\kappa_2(W)=K$ can overstate an original-coordinate singular lower without bound.

## 3. Evidence and ceiling

The exact apparatus passed 16/16 focused tests, 44/44 adjacent residual/witness tests, 83/83 complete contour-chain tests, and 27/27 dimensionless tests. In the nonnormal structural control, weighting changes unavailable unweighted node contractions into four strict contractions, but conditioning and the chord keep the full circle uncertified. Equal or harmful weights cannot weaken a valid unweighted result because selection occurs only between translated original-coordinate lowers.

This closes the mathematics and implementation of one supplied exact diagonal similarity. It does not choose the weight, certify a post-hoc search, handle blocks or dense similarities, round floating inverses, validate interval coverage, instantiate a brain matrix, identify consciousness, or select dimension 4--6.

