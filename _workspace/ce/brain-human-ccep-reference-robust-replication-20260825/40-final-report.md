# 연구 run 인계

Status: COMPLETE

Decision: APPARATUS_OR_EVOCATION_STOP

## Outcome

The frozen sub-1 development experiment completed all 32 stimulation sites and
346 eligible events over 154 good intracranial channels. The result does not
open confirmation. The mean-contact readout passed both preregistered
development checks, but the bipolar readout failed split-half repeatability:

| Readout | Directed edges | Split-half Spearman | Early/prestim | Frozen result |
|---|---:|---:|---:|---|
| mean | 642 | 0.6090033883473331 | 2.0447901214209576 | PASS |
| bipolar | 642 | 0.4953798448445255 | 1.6191689540447336 | FAIL (`rho < 0.50`) |

The ratio pass does not compensate for the bipolar repeatability failure. Under
the one-failure rule in `00-contract.md`, this closes the frozen development run
before sub-5 signal acquisition and leaves all confirmation subjects closed.

## Evidence

- Subject gate receipt: `artifacts/development-gate-sub-1.json`, SHA-256
  `2133e6b4124ab3c9ae68d43416d802eb850439c41958bec9f0b0cfa72d748f10`.
- Site receipt set: 31 `development-site-sub-1-*.json` files plus the separately
  frozen `development-first-site-sub-1.json`, 32/32 hashes matching the gate
  receipt and 32 unique receipt hashes.
- Total exact-range signal payload represented by the site receipts:
  184,110,520 bytes. Persistent raw bytes: zero.
- Each regular site receipt records 154/154 channel receipts, exact TDAT ranges
  and source identities, all temporary-session cleanup true, deterministic
  placement, disposed site tile, and no cross-site signal cache.
- The v1 and v2 bounded-concurrency amendments were both independently accepted
  before their respective executions.
- Independent final audit found no P0, P1, or P2 issue in receipt completeness,
  aggregation, gate arithmetic, or STOP application.

## Interpretation boundary

This is an empirical development STOP, not evidence that the biological system
lacks evoked responses. The early/prestim ratios exceeded 1.25 for both
readouts. What failed was the frozen bipolar A/B rank-repeatability threshold by
approximately 0.00462. The threshold is not rounded down, retuned, or replaced
after seeing the result.

The run therefore makes no confirmation claim, no population-level CCEP claim,
and no CE-law promotion. Running sub-5 descriptively would require a separate
successor contract and cannot be appended to this frozen run.
