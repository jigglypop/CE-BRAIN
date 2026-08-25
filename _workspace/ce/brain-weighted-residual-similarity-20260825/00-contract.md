# Weighted residual similarity contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-exact-residual-witness-construction-20260825`

## Objective

Strengthen the componentwise residual route with one declared positive diagonal similarity weight while retaining a valid lower bound in the original Euclidean operator norm. The conditioning penalty of the similarity is mandatory. The certificate deterministically selects the better of the existing unweighted node lower and the translated weighted node lower.

No weight is fitted to neural data, no floating optimizer is used, and no statistical coverage is claimed.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | No-retry condition |
|---|---|---|---|---|
| Componentwise residual family theorem | residual run K1--K3; focused 14/14 | PASS | Strict node contractions plus positive original-coordinate chord lower certify the family. | Keep the chord and projector bounds in the original $2$-norm. |
| Exact witness construction | exact-witness run W1--W3; focused 14/14 | PASS | Exact nominal inverses can be constructed deterministically. | Weighting cannot replace witness or uncertainty checks. |
| Weighted route | residual `12-routes.md`; ledger CE-RESINT-004 | OPEN | A diagonal similarity may reduce row/column mixing. | Must report weight conditioning and translate back to the target norm. |

## Frozen weighted construction

Supply one common vector $w\in\mathbb Q_{>0}^n$ and normalize it by
$\widehat w_i=w_i/\min_jw_j$, so $min_i\widehat w_i=1$. Let
$W=\operatorname{diag}(\widehat w)$. At each normalized node, transform

$$
A'_k=W^{-1}A_{0k}W,\qquad
B'_k=W^{-1}B_kW,\qquad
D'^+=W^{-1}D^+W.
\tag{V1}
$$

The existing componentwise calculation is then applied unchanged:

$$
G_k'^+=|I-B'_kA'_k|^+ + |B'_k|^+D'^+.
\tag{V2}
$$

If both induced contractions are strict, it yields an upper $M'_{2k}$ for
$\|(A'_k)^{-1}\|_2$. Because

$$
A_{0k}^{-1}=W(A'_k)^{-1}W^{-1},
$$

the original-coordinate bound is

$$
\|A_{0k}^{-1}\|_2
\le\kappa_2(W)M'_{2k},\qquad
\ell_{wk}=\frac{1}{\kappa_2(W)M'_{2k}},
\quad
\kappa_2(W)=\frac{\max_iw_i}{\min_iw_i}.
\tag{V3}
$$

For each node select
$\ell_k^*=\max(\ell_{uk},\ell_{wk})$ over the available rigorous unweighted and weighted lowers. Subtract the predecessor's original-coordinate chord upper and require

$$
\delta_w^*=\min_k\ell_k^*-\chi^+>0.
\tag{V4}
$$

Only then may common rank and resolvent/projector bounds be returned.

## Required controls

- scalar-equal weights reproduce the unweighted normalized nodes and status;
- common scaling of $w$ changes nothing;
- a structured nonnormal case where unweighted node contraction fails but weighted succeeds;
- a case where weighting contracts but the $\kappa_2(W)$ penalty prevents full-circle promotion;
- exact inverse and inexact supplied witnesses;
- weight length, positivity, Boolean/float/noncanonical rejection;
- raw spectral unit invariance;
- no selection leakage when weighted is worse than unweighted.

## Counterexample and ceiling

For $A'=\begin{pmatrix}1&1\\0&1\end{pmatrix}$ and
$W=\operatorname{diag}(K,1)$,
$A=WA'W^{-1}=\begin{pmatrix}1&K\\0&1\end{pmatrix}$ has inverse norm growing with $K$. Omitting $\kappa_2(W)=K$ therefore gives an invalid original-coordinate lower.

The theorem concerns one supplied exact diagonal similarity. It does not optimize weights, certify post-hoc empirical selection, handle block/non-diagonal similarities, generate floating witnesses, establish interval coverage, analyze neural data, identify consciousness, or select 4--6 dimensions.

