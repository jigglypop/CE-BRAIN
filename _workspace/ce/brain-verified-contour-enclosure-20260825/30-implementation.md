# Verified rational contour enclosure -- implementation

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-verified-contour-enclosure-20260825`

Implemented only the approved standalone module
`reality_stone/python/reality_stone/clarus/verified_rational_contour.py` and
its focused test file.  It has no NumPy/Torch import and does not alter the
predecessor float64 paths.

## Implemented V1--V3 seam

- `QComplex` stores a pair of exact `Fraction` values; the parser admits only
  built-in integers, `Fraction`, or canonical strings.  Integer/fraction
  strings must round-trip through `str(Fraction)`; finite decimals use a
  no-leading-zero, no-trailing-fractional-zero grammar.  It rejects `bool`,
  `float`, Python `complex`, exponent notation, signs such as `+1`, and
  noncanonical forms such as `01`, `1/02`, and `1.0`.
- Inputs are divided by the positive rational reference scale before all
  inversions and dyadic decisions.  Raw node lower bounds, chord, separation,
  and resolvent quantities are then derived covariantly.
- Exact Gauss--Jordan elimination over $\mathbb Q(i)$ checks both inverse
  residual identities exactly.  Each inverse Frobenius square is enclosed by
  an integer-`isqrt` dyadic bracket whose squared inequalities are checked.
- The certificate exposes both endpoints and both exact inequalities for
  $\sqrt2$ and for the chord factor
  $\sqrt{2-\underline{\sqrt2}}$; no placeholder truth value is used.
- Only `nodes=4` is accepted.  The central quadrature includes the required
  $r i^k/4$ factor.  Singular samples and nonpositive conservative lower
  bounds receive named non-certificate statuses.
- The strip route accepts only rational `q>1` and a square diagonal witness.
  It exactly verifies $UV=V\Lambda$, `V` invertibility, diagonal structure, and
  strict exclusion from the closed annulus before returning the exact witness
  projector and $2M^+/(q^4-1)$.

Limitations remain intentional: this is a fixed four-node, finite rational,
diagonalizable-witness route.  A failure is not evidence of contour-spectrum
intersection, and no float64, biological, empirical, consciousness, or rank
claim is promoted.
