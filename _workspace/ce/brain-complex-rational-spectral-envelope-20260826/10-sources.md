# Sources and dependencies

Status: COMPLETE

## Formal inputs

The route uses the exact real representation of a complex-linear map,
Cayley--Hamilton, coefficient conjugation, and the determinant identity
`chi_R(U)=chi_U conjugate(chi_U)` for realification.  The exact translation
`W=U-cI`, `z=c+w` converts every Gaussian-rational circle to the conjugation-
invariant zero-center circle without changing the Riesz projector.

## Internal dependencies

- `verified_complete_q_polynomial_factorization.py`
- `verified_polynomial_spectral_projector_construction.py`
- `verified_algebraic_riesz_projector.py`

No external data or numerical eigenvalue routine is used.
