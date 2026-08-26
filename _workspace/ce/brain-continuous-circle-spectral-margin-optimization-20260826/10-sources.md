# Sources and dependencies

Status: COMPLETE

## Formal inputs

The proof uses exact diagonalization, the coordinate mean-value theorem for a
quadratic signed distance function, compact-box branch-and-bound, and the standard
incumbent/global-upper optimality sandwich.

## Internal dependencies

- `verified_characteristic_spectral_split_discovery.py`
- `verified_complete_q_polynomial_factorization.py`
- `verified_polynomial_spectral_projector_construction.py`

No numerical eigensolver, continuous black-box optimizer, or external data is
used.
