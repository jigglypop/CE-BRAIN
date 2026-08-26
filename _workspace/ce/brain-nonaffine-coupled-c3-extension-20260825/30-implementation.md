# Implementation

Status: COMPLETE

## Changed scope

- Added
  `reality_stone/python/reality_stone/clarus/quantitative_nonaffine_coupled_c3_graph_transform.py`.
  It composes the frozen nonaffine coupled $C^2$ certificate with the exact
  coupled inverse-composition $C^3$ identity.
- Added
  `tests/test_quantitative_nonaffine_coupled_c3_graph_transform.py` with exact
  class, recurrence, reduction, boundary, rescaling, dimension, and fail-closed
  controls.
- Extended `tests/test_dimensionless.py` with the normalized nonaffine coupled
  $C^3$ core.

The implementation adds $T_\phi$ to the one-graph base third derivative,
$U_\phi$ to its Lipschitz modulus, and $U_\phi r_x$ to the two-graph value
coefficient.  All remaining modified-Hessian and inverse-Jacobian corrections
are inherited without simplification from the affine coupled skeleton.

## Preserved invariants

- Exact `Fraction` arithmetic and existing fail-closed input parsing are used.
- The supplied finite dimension is preserved and is not selected.
- $\Lambda_3$ is also passed to the lower $C^{2,1}$ gate as the Lipschitz
  radius of $D^2h$.
- $(H_\phi,T_\phi,U_\phi)=(0,0,0)$ reproduces affine coupled $C^3$ term by
  term.
- Zero graph-to-base coupling reproduces common-inverse nonaffine triangular
  $C^3$ with $\nu=H_\phi\mu^3$ and
  $\tau=T_\phi\mu^4+3H_\phi^2\mu^5$.
- $C^{3,1}$ is required only for graph-dependent preimages, and strict
  $Q/\alpha^3<1$ is never relaxed.
- No runtime, biological model, threshold, dataset, or package dependency was
  changed.

## Revision discovered by the focused test

The first focused execution produced `30 passed, 1 failed`.  The failed
affine reduction showed that the draft API had allowed a separate lower
$C^{2,1}$ graph radius instead of passing $\Lambda_3$ as the bound on
$\operatorname{Lip}(D^2h)$.  Revision 1 removed that redundant input and
restored the frozen affine class convention.  No formula coefficient,
threshold, or fixture was tuned to a target value.

The corrected focused, dimensionless, and adjacent results are recorded in
`31-validation.md`.  Git state was not staged or published.

