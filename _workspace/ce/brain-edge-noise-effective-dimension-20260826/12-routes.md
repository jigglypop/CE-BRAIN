# Routes and counterexamples

Status: COMPLETE

## Closed routes

- Exact PSD/PD and dimension schemas are inherited from EDIM.
- Pairwise commutation checks every matrix pair, not merely `Q` against `A0`.
- Both endpoint derivatives are computed from the full noncommutative product rule.
- A commuting six-coordinate fixture gives `60/11 -> 30/7` inside `[4,6]`.
- Singular commuting noise preserves its observed hard rank.
- Zero forcing realizes exact equality.
- Scaling `A,H` by `c` and `Q` by `c^2` preserves response covariance.

## Rejected route

The exact noncommuting example has a positive ridge derivative and endpoint change,
so PSD edge strengthening alone cannot support a universal dimension-decrease claim.
