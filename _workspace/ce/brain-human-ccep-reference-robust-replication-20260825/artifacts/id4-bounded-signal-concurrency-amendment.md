# ID4 bounded signal concurrency amendment

- Amendment ID: `id4-subject-development-signal-concurrency-v1`
- Frozen before the second development-site endpoint was produced: 2026-08-26
- Scope: execution capacity only; the frozen subjects, sites, events, windows, CAR75 rule,
  mean/bip readouts, split halves, thresholds, and confirmation rule are unchanged.
- `max_signal_concurrency: 4`; values other than exactly four are rejected by the subject runner.
- Only one stimulation-site tile may exist. Each worker handles exactly one channel and only
  the exact TDAT ranges needed by that site's eligible windows.
- Each worker's temporary MEF3 session must be removed before its result is accepted. The
  returned decoded channel array is copied into its deterministic channel column and then
  overwritten immediately. The site tile is overwritten and deleted immediately after the
  endpoint is computed.
- No TDAT bytes or decoded values may be cached across sites. Verified immutable TMET/TIDX
  metadata may be reused under the frozen plan identities.
- The frozen sub-1 event table has 346 eligible events over 32 sites and a maximum of 23
  trials at `LB1-LB2`. The extra four-channel decoded-value bound is therefore
  `4 * 23 * 1127 * 8 = 829,472 bytes`; the site tile bound is
  `23 * 154 * 1127 * 8 = 31,934,672 bytes` (`float64`). A site above 23 trials is rejected.
- A worker failure, cleanup failure, incomplete channel population, source-identity mismatch,
  concurrency-cap breach, or placement mismatch is fail-closed: no site endpoint receipt is
  written.
- Each site receipt records the amendment ID, configured and observed concurrency, plan/source
  identities, channel range receipts and cleanup, tile shape/dtype and memory bounds,
  `cross_site_signal_cache: false`, `decoded_value_cache_after_copy: false`, and
  `persistent_raw_bytes: 0`.

This amendment was accepted outcome-blind by the independent status-audit lane before execution.

Correction note (2026-08-26): the first frozen draft incorrectly used the already-completed
`LA1-LA2` count (12) as a subject-wide maximum. The executable frozen event table was immediately
recounted before any second site began: 346 events, 32 sites, maximum 23 at `LB1-LB2`. The
`LB1-LB2` receipt had already recorded the actual 23-trial shape and the exact larger memory bounds;
it is quarantined until independent audit accepts or rejects this mechanical capacity correction.
