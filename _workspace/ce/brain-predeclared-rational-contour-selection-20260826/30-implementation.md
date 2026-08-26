# Implementation

Status: COMPLETE

## Module

`reality_stone/python/reality_stone/clarus/predeclared_rational_contour_selection.py`

It emits canonical candidates/hash, all development certificates/scores, unique
winner/runner/advantage, selected-only heldout certificate, rank consistency,
and explicit no-post-hoc/no-continuous-optimization/provenance honesty flags.

## Tests

`tests/test_predeclared_rational_contour_selection.py` covers unique selection,
deterministic hashing/order, duplicates, winner/runner ties, strict equality,
no eligible candidate, heldout singularity, rank mismatch, exact selected-only
call count, forged menu, dimension mismatch, invalid IDs, and scale covariance.
