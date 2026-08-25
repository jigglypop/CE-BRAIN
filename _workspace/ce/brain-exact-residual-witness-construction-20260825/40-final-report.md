# Exact construction of residual witnesses

Status: COMPLETE

Date: 2026-08-25

## Abstract

The componentwise residual theorem previously checked supplied inverse witnesses but did not certify their provenance. For exact rational nominal matrices, this successor constructs all four contour-node inverses by deterministic Gauss--Jordan elimination over $\mathbb Q(i)$ and checks both inverse identities exactly. A convenience bridge then applies the unchanged interval-family contraction and full-circle gates. Focused construction passed 14 tests, residual integration 28, the complete rational interval chain 67, and the dimensionless gate 25. A singular sampled node and a large-uncertainty case remain named non-certificates. Floating-solver rounding, weighted norms, empirical coverage, neural data, consciousness, and dimension selection remain outside the result.

## 1. Construction theorem

After normalize-first scaling, the ordered node matrices are

$$
A_{0k}=(\widetilde c+\widetilde r d_k)I-\widetilde U_0,
\qquad d_k\in(1,i,-1,-i).
$$

Gauss--Jordan elimination on $[A_{0k}\mid I]$ uses the first available nonzero pivot in each column. Because $\mathbb Q(i)$ is a field, every successful operation remains exact. A successful reduction returns $B_k$ only after

$$
B_kA_{0k}=I=A_{0k}B_k
$$

is checked entry by entry. A missing pivot proves that the sampled node matrix is singular; no inverse witness is returned.

The procedure is deterministic for a fixed normalized matrix. Common rescaling of $U_0,c,r,s_*$ leaves the normalized matrices, pivot path, and witnesses unchanged.

## 2. Composition without status leakage

For constructed exact inverses the nominal residual is zero, so the predecessor's componentwise matrix reduces to

$$
G_k^+=|B_k|^+D^+.
$$

This removes nominal inverse approximation error but not family uncertainty. Both induced contractions must still be strictly below one, and the chord-corrected full-circle lower must still be positive. The convenience bridge therefore returns the predecessor failure unchanged whenever construction passes but uncertainty is too large.

For $U_0=[1]$, center zero, and radius one, the first node gives $A_{00}=0$, so construction stops. For $U_0=[0]$ with radius-one scalar uncertainty, all nominal inverses exist but the family contraction reaches the unsafe boundary. These are separate, complete controls against status leakage.

## 3. Evidence and limits

The implementation passed 14/14 focused constructor tests, 28/28 constructor-plus-residual tests, 67/67 complete rational interval-chain tests, and 25/25 dimensionless tests. The exact constructor closes the supplied-witness provenance gap only when the nominal matrix and contour are exact rational inputs.

An approximate floating inverse still needs a frozen solver, rational rounding rule, error receipt, and downstream residual check. Weighted or block norms require predeclared weights and a translation back to the target norm. Neither extension is claimed here. No actual neural matrix, statistical interval coverage, consciousness observable, or preference for 4--6 dimensions is produced.

