# Stage 1 Armijo optimizer retry pre-seal audit

Status: COMPLETE

Gate: PASS

Scope: fit-only failure diagnosis, optimizer mathematics, predecessor inheritance,
implementation and receipt audit. Noise 1 and Noise 2 values remained unopened.

## Failure witness and route selection

The sealed predecessor stopped before DEV/CONFIRM. On 147,192 fit rows (119
positive events), M0 converged but the M1 undamped Newton objective worsened after
iteration 8 and diverged. Three distinct solver routes were registered; monotone
Armijo Newton was selected because it preserves the same objective, curvature,
features, penalty, data and scientific gates.

## Mathematics

Independent audit verified the penalized log-likelihood, gradient, positive
Newton system and maximization-form Armijo inequality. Gradient convergence is
checked before direction construction and after accepted steps; stationary
zero-gradient starts succeed, small backtracked steps alone do not. Non-ascent,
line-search, finite, monotonicity and iteration kills are fail-closed. Verdict:
`PASS`, P0/P1/P2 none.

## Inheritance and implementation

- Predecessor manifest SHA, source SHA and all 11 bound file hashes are verified.
- Parent raw/schema/manifest verification is invoked before local seal/execute.
- Only fit rows reach the custom solver; DEV/CONFIRM remain after completed fit.
- Local manifest binds predecessor, schema, raw and six overlay prereg files.
- Stored results reload model hashes, parent data/metric receipts, optimizer
  convergence receipts and the unchanged confirmation decision.
- Existing result and parent/local/schema/raw/result mutation fail closed.

Stable-snapshot hashes before this audit file:

- retry contract: `d01dc1c2d4775e6deb2613a022dab118749d9d67012ee132df6ba6e7132eff5e`
- route portfolio: `eade935c2eea8b4cd9cd09e308ffeedd187a21bc05871d02fbdc6e8aacb15393`
- implementation: `4239c4a4e71a15dd366632021491d1bcdb145e38be017982c9e70d355b281ea3`
- test: `393a58f225808e9cc362d5617779c030ca8dd4cec77abd000a85598660498374`

Claim ceiling remains the inherited one-cell predictive comparison. This retry
cannot erase or relabel the predecessor apparatus STOP.
