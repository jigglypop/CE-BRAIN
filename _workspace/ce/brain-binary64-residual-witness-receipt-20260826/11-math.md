# Mathematics lane

Status: COMPLETE

## B64.1 Canonical finite-bit decoding

Accept exactly sixteen lowercase hexadecimal digits.  Let `s` be the sign
bit, `e` the eleven-bit exponent, and `f` the 52-bit fraction.

For `1<=e<=2046`, the stored value is exactly

$$
x=(-1)^s(2^{52}+f)2^{e-1023-52}.
$$

For subnormal `e=0`, `f>0`, it is

$$
x=(-1)^sf2^{-1074}.
$$

For `e=f=0`, the rational value is zero while the sign bit is retained as a
diagnostic.  `e=2047` denotes infinity or NaN and is rejected.  These formulas
use integer shifts and rational denominators only; no host floating operation
enters decoding.

For example the stored bits of binary64 `0.1` decode exactly to

$$
{3602879701896397\over36028797018963968},
$$

not to the decimal rational `1/10`.  The smallest positive subnormal is
exactly `2^-1074` and does not underflow in the receipt.

## B64.2 Exact complex witness receipt

Each complex entry is a pair of real/imaginary bit strings.  Decode every
component into `Q(i)` and hash the canonical nested bit array.  The hash
distinguishes `+0` and `-0` even though their decoded rational matrices agree.

For nominal node matrix `A0`, decoded witness `B`, and interval perturbation
`Delta`, the unchanged predecessor computes

$$
R=I-BA_0,
$$

and an exact componentwise upper matrix for

$$
|R|+|B||\Delta|.
$$

If both induced one and infinity norms are strictly below one, Banach's lemma
gives the inverse bounds used by the full-circle certificate.  This argument
depends only on the exact stored witness value and its exact residual, not on
the algorithm that proposed it.

## B64.3 Provenance boundary

The receipt proves

`binary64_stored_value_decoding_verified=True`.

It permanently records

- `solver_algorithm_verified=False`,
- `solver_operation_rounding_mode_verified=False`, and
- `empirical_matrix_provenance_verified=False`.

Thus it closes float-value-to-rational-witness reproducibility, not the whole
solver execution receipt.  A poor solver result simply fails the exact
residual contraction; good stored bits may pass without trusting their origin.

## B64.4 Boundaries

- all-zero inverse witnesses give residual identity and fail at strict `q<1`;
- a valid witness cannot override excessive interval uncertainty;
- noncanonical width/case/prefix, malformed matrices, NaN, and infinity fail;
- normalizing the matrix, contour, and reference scale first preserves the
  exact residual certificate.
