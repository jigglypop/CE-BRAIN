# Contract: continuous circle spectral-margin optimization

Status: COMPLETE

## Objective

Replace finite-menu-only circle choice with a certified tolerance-global
optimization over a compact continuous exact center/radius box for a frozen
signed squared spectral margin and complete exact diagonalization witness.

## Acceptance conditions

1. Verify `UV=V Lambda` exactly with invertible square `V` and a complete list of
   Gaussian-rational eigenvalues.
2. Freeze every inside/outside target label before search.
3. Cover each real parameter cell with an exact derivative-based score upper.
4. Branch until global upper minus sampled incumbent is at most the declared
   dimensionless tolerance, or fail on the declared cell budget.
5. Require a positive selected target margin and revalidate the selected circle
   through exact characteristic/projector/rank discovery.
6. Expose all terminal cells and state that the result is not finite-grid-only.

## Ceiling

Defective/no-witness matrices, general pseudospectral objectives, continuous
noncircular shape/knot families, empirical objective selection, consciousness,
and dimension 4--6 remain outside.
