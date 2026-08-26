# Sources and dependencies

Status: COMPLETE

## Formal inputs

The proof uses only internally restated algebraic results:

1. Gauss' lemma: a primitive integer polynomial reducible over Q has a
   nontrivial factorization by primitive integer polynomials, up to units.
2. Kronecker's finite method: values of an integer factor at integer points
   divide the corresponding values of the polynomial, and degree-many-plus-one
   values determine the factor by exact interpolation.
3. A nontrivial factorization of degree `n` has a factor of degree at most
   `floor(n/2)`.

No empirical source or external numerical factorization library is used.

## Internal successors

- `verified_characteristic_spectral_split_discovery.py`
- `verified_polynomial_spectral_projector_construction.py`
- `verified_algebraic_riesz_projector.py`
