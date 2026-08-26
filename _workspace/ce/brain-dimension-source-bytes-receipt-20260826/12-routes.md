# Routes and counterexamples

Status: COMPLETE

## Closed routes

- Tagged recursive decoding reconstructs exact rationals and structures.
- Re-encoding equality rejects alternate byte representations.
- Six domain hashes bind archive bytes directly to DMAN expected hashes.
- The bundle root binds payload order, boundary, and total content.
- Session and base-contract seams are checked before execution.
- Integer-only bootstrap indices require exact denominator-one refinement.

## Adversarial routes

- Trailing JSON whitespace is rejected as noncanonical.
- An unreduced `2/2` rational node is rejected.
- A stale bundle root, wrong domain tag, cross-domain session mismatch, or altered
  base selected-rank contract fails before the full chain is admitted.
- A successful canonical archive still has no external signer or device receipt.
