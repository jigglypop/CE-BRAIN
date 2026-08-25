# M2 float64 contour-estimate implementation

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

Gate prerequisite: `20-audit.md` is `Gate: PASS`.

## Scope implemented

`reality_stone/python/reality_stone/clarus/finite_contour_bounds.py` adds a
finite-complex float64 seam only:

- `circle_float64_estimate` computes the sampled minimum singular value, the
  chord formula, `delta_hat_estimate`, and a resolvent-upper estimate only
  when that float estimate is positive.
- `analytic_strip_float64_estimate` evaluates the inner/outer float circles,
  numerical annulus membership/margin, and `M_estimate` plus
  `2*M_estimate/(exp(a*N)-1)` only when its float conditions hold.
- The strip result also carries a `central_circle_estimate` at the original
  radius; inner/outer circles are used only for the float `M_estimate` path.
  Annulus-boundary/near-boundary numerical eigenvalues suppress inner/outer,
  `M_estimate`, and error estimates rather than being treated as clear.
- Both APIs require a positive `spectral_reference_scale`. Raw separation has
  spectral units and raw resolvent norm reciprocal spectral units; normalized
  quantities are dimensionless.

The exact labels are `FLOAT64_UNVERIFIED_FULL_CIRCLE_ESTIMATE` and
`FLOAT64_UNVERIFIED_ANALYTIC_STRIP_ESTIMATE`. These outputs are estimates, not
interval enclosures, verified bounds, all-contour separation results, or
analytic-strip certificates. `E1`, source manifests, data, likelihoods, and
empirical scores were not implemented or changed.

Empty matrices and unrepresentable `exp(-a)`, `exp(a)`, or `expm1(a*N)`
preflights are rejected with `ValueError`; no overflow result is reinterpreted
as a usable estimate.

## Changed paths

- `reality_stone/python/reality_stone/clarus/finite_contour_bounds.py`
- `tests/test_finite_contour_bounds.py`
