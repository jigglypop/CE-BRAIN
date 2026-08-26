# Routes and counterexamples

Status: COMPLETE

## Route A: frozen composite midpoint

This is implemented because every midpoint remains rational and every nominal
resolvent inverse can be checked exactly.

## Route B: trapezoid or higher-order rational quadrature

These are valid alternatives with different derivative constants.  They are not
silently identified with the midpoint theorem and remain optional successors.

## Failure boundaries

- `m_k=0`, Boolean, float, or wrong-length subdivision vectors fail.
- Singular midpoint inversion contradicts a valid edge certificate and is an
  internal error, not a skipped sample.
- If several integer rank intervals remain possible, no ordering or nearest-value
  tie-break is permitted.
- Frozen refinement reduces the analytic remainder by `m^-2`; choosing `m` after
  inspecting an empirical rank is outside this contract.
