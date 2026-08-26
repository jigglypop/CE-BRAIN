# Implementation

Status: COMPLETE

- Runtime: `reality_stone/python/reality_stone/clarus/verified_dimension_signed_acquisition_receipt.py`
- Focused tests: `tests/test_verified_dimension_signed_acquisition_receipt.py`
- Predecessor: `verified_dimension_source_bytes_receipt.py`
- Dimensionless registry: `tests/test_dimensionless.py`
- Claim-status lock: `tests/test_brain_claim_ledger_status.py`

The implementation uses standard-library exact integer and SHA-512 operations,
canonical compressed-point decoding, prime-subgroup checks, and a detached
signature gate. Test-only signing logic is confined to the focused test fixture.
