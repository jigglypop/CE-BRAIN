# Routes and counterexamples

Status: COMPLETE

## Implemented finite-menu route

Normalized contour geometry removes raw spectral-scale duplication.  Every menu
candidate is fully evaluated on development; only the unique strictly separated
winner is evaluated once on heldout.

## Refusal cases

- Exact duplicate geometry, invalid IDs, and forged hashes are rejected.
- Winner/runner ties, advantage equality, and no eligible candidate fail closed.
- Selected heldout singularity/nonpositive cover and rank mismatch fail.
- Development/heldout matrix dimension mismatch is rejected.

## Open successors

Continuous or adaptive contour/knot optimization requires a compact search
domain, a global objective enclosure, branch-and-bound/refinement termination,
and an independently frozen heldout protocol.  Automatic exact projector discovery
and empirical provenance remain separate.
