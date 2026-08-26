# Contract: fixed forcing-noise edge dimension

Status: COMPLETE

## Objective

Extend the edge-metric dimension bridge to a fixed forcing covariance
`C_Q=A^-1 Q A^-1`, prove monotonicity under explicit pairwise commutation, and
give an exact complete counterexample showing that positive edge strengthening can
increase observed ridge dimension when noise and metric do not commute.

## Acceptance conditions

1. Baseline metric is exact SPD; forcing and every edge term are exact PSD.
2. Both response covariances, observed Grams, ridge dimensions, and endpoint
   derivatives are computed exactly.
3. Pairwise commutation includes baseline, forcing, and every edge term.
4. The commuting theorem verifies Loewner decrease and nonpositive derivatives.
5. The commuting edge box has an exact robust 4--6 endpoint decision.
6. A noncommuting PSD counterexample has positive dimension change and derivative.
7. Noncommuting inputs never receive the commuting monotonicity claim.
8. No selected-rank or consciousness claim is admitted.
