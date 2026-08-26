# Implementation

Status: COMPLETE

## Owned module

`reality_stone/python/reality_stone/clarus/verified_complete_q_polynomial_factorization.py`

It emits canonical inputs, every Kronecker search record, evaluation points,
candidate-space size and examined count, exact found factor, search exhaustion,
irreducible factors, multiplicities, primary powers, product reconstruction, and
honesty flags.

## Integration

`verified_characteristic_spectral_split_discovery.py` now accepts
`maximum_factor_candidate_value_tuples`, refuses incomplete factor searches before
partition enumeration, and uses complete primary factors at arbitrary admitted
finite degree.  The legacy rational-root/residual fields remain diagnostic for
backward-readable receipts.

## Focused tests

- `tests/test_verified_complete_q_polynomial_factorization.py`
- `tests/test_verified_characteristic_spectral_split_discovery.py`
