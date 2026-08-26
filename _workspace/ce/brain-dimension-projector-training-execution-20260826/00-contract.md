# Contract: exact development PCA projector training execution

Status: COMPLETE

## Objective

Recompute exact centered development covariances, verify supplied rational
eigenbases and strict eigenvalue order, construct every frozen prefix projector,
and execute the held-out DEXEC/DSTAB chain without accepting arbitrary projectors.

## Acceptance conditions

1. Development observations are coordinatewise exactly zero mean.
2. Covariance is recomputed from the supplied observations.
3. The full basis is exactly orthonormal and satisfies every covariance eigen-equation.
4. Eigenvalues are strictly decreasing, excluding rank-boundary degeneracy.
5. Prefix projector menus are constructed, never separately supplied.
6. The complete held-out execution succeeds.
7. External bytes and preprocessing execution remain unverified.
