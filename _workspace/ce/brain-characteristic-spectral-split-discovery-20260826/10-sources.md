# Sources

Status: COMPLETE

## Internal dependencies

1. `verified_polynomial_spectral_projector_construction.py` — exact factor-to-P/R
   construction and strict algebraic gate.
2. `verified_algebraic_riesz_projector.py` — final Riesz classification.
3. `verified_complete_q_polynomial_factorization.py` — Gauss--Kronecker complete
   exact Q factorization and primary-factor reconstruction.
4. CE-CXSPEC — exact realification envelope and original complex-rank convention.

The discovery route uses exact Faddeev--LeVerrier, Cayley--Hamilton matrix
evaluation, primitive integer lifting, Gauss' lemma, finite Kronecker
interpolation, and finite partition enumeration.  No external data is used.
