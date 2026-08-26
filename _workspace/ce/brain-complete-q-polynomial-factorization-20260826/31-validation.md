# Validation

Status: COMPLETE

## Focused evidence

- complete Q factorization: 16/16
- strengthened characteristic discovery including arbitrary-center Gaussian-rational envelope: 16/16
- Q-factor/characteristic/projector/algebraic adjacency: 60/60
- same chain plus dimensionless and canonical ledger: 144/144
- dimensionless suite: 80/80

## Commands

```text
.codex/hooks/python.cmd pytest tests/test_verified_complete_q_polynomial_factorization.py
.codex/hooks/python.cmd pytest tests/test_verified_complete_q_polynomial_factorization.py tests/test_verified_characteristic_spectral_split_discovery.py tests/test_verified_polynomial_spectral_projector_construction.py tests/test_verified_algebraic_riesz_projector.py tests/test_dimensionless.py tests/test_brain_claim_ledger_status.py
```

Source AST parsing passes for both changed modules.  Patch whitespace passes
(`git diff --check` emits line-ending warnings only), the run contains exactly
eight files, the full contour-chain regression passes 359/359 after the
arbitrary-center Gaussian-rational successor, and the final research gate reports `OK final`.
