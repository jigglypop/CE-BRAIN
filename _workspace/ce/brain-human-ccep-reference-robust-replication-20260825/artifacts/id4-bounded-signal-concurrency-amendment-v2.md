# ID4 bounded signal concurrency amendment v2

- Amendment ID: `id4-subject-development-signal-concurrency-v2`
- Frozen before any v2 site endpoint was produced: 2026-08-26
- Scope: execution capacity only. Frozen source/site/event/window identities, CAR75, mean/bip
  readouts, split halves, thresholds, and gate rules are unchanged.
- The completed v1 receipt set is exactly `LB1-LB2`, `LB11-LB12`, `LB12-LB13`,
  `LB13-LB14`, and `LB2-LB3`. These remain valid under v1 and are not recomputed.
  `LA1-LA2` remains the separately frozen first-site receipt.
- Every other sub-1 site uses v2 with `max_signal_concurrency: 8`; values other than exactly
  eight are rejected by the subject runner.
- Only one stimulation-site tile may exist. Each worker handles one channel and exact TDAT
  ranges only; its temporary MEF3 session must be removed before acceptance. Returned channel
  values are copied into the deterministic frozen column and overwritten immediately. The site
  tile is overwritten/deleted after endpoint calculation.
- The frozen maximum is 23 trials. Peak site tile is 31,934,672 bytes and peak extra decoded
  storage is `8 * 23 * 1127 * 8 = 1,658,944 bytes` (`float64`). Sites above 23 trials stop.
- No cross-site TDAT/decoded cache is allowed. Verified immutable TMET/TIDX metadata reuse is
  unchanged. Persistent raw bytes must remain zero.
- Receipt/fail-closed requirements are identical to v1, with v2 amendment ID and configured /
  observed concurrency recorded. A worker, cleanup, source, placement, population, cap, or
  memory-bound failure prevents the site endpoint receipt from being written.
- v1 and v2 outputs combine only as a site-disjoint receipt set; execution version is not an
  endpoint covariate and does not alter aggregation.

The independent status-audit lane accepted this amendment outcome-blind before v2 execution.
