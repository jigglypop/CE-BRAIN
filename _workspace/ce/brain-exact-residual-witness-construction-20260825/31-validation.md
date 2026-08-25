# Validation

Status: COMPLETE

- focused constructor: `tests/test_exact_residual_witness_construction.py`, 14/14 passed;
- constructor plus predecessor residual: 28/28 passed;
- complete rational/interval/tightening/residual/constructor chain: 67/67 passed;
- dimensionless gate: 25/25 passed.

Controls include exact two-sided identities, scalar/diagonal/nonnormal cases, deterministic repetition, normalize-first unit invariance, sampled-node singularity, successful construction followed by uncertainty failure, and invalid exactness/shape/mesh inputs.

No floating solver, denominator rounding, weight optimization, empirical interval, or data action was used.

