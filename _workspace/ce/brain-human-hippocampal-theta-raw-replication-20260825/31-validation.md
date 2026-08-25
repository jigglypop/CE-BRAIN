# BA-OBS-HPC1 validation

Status: COMPLETE

Scientific disposition: BLOCKED / STOP_MEASUREMENT_APERTURE

Only focused source-lock and fixture validation are permitted before the serialized
source barrier is green. Full-suite testing is not authorized.

## Completed focused checks

1. `.codex\\hooks\\python.cmd doctor`
   - PASS: CPython 3.11.9, NumPy 2.4.6, pytest 9.1.1, bytecode disabled.
2. `.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc1_raw_replication.py -q -p no:cacheprovider --basetemp C:\\temp\\hpc1_pytest_20260825g`
   - PASS: `1 passed in 0.95s`.
   - Covers exact integer window indices, little-endian multiplex decoding across
     non-frame chunk boundaries, p17 filter route, DFT/baseline processing, artifact
     aperture, P2P-of-mean distinction, and shared-participant bootstrap bounds.
3. `.codex\\hooks\\python.cmd python examples\\brain\\ba_obs_hpc1_raw_replication.py source-lock`
   - PASS: serialized 18-object `SOURCE_LOCK_PASS` receipt. This stage made no EEG
     GET request.

## Historical attempt-0 status

Attempt 0 was `ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`: a contract audit found
that the implementation applied artifact rules before baseline correction. The exact
two raw child processes were terminated before any outcome receipt, and no
`raw_result.json`, raw file, waveform dump, Nature Source Data, or biological result
existed. The corrected implementation later passed the registered re-audit and was
executed once as attempt 1; its terminal receipt is recorded below.

## Revision 1 focused validation

`.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc1_raw_replication.py -q -p no:cacheprovider --basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc1_pytest_20260825i2`

- PASS: `3 passed in 1.00s`.
- Covers canonical/tampered source-lock rejection; header endian/resolution/unit
  parsing; version-pinned streamed observed hash/size receipt and microvolt scaling;
  baseline-before-artifact processing; source transaction refusal; aggregate summary
  serialization; clinical non-support and LOO sensitivity status routing.

`source-lock` was then regenerated under header-only authorization and passed the
offline canonical validator:

`.codex\\hooks\\python.cmd python -c "... m.validate_source_lock(...); print('SOURCE_LOCK_CANONICAL_PASS')"`

- Output: `SOURCE_LOCK_CANONICAL_PASS`.
- The regenerated receipt records header `DataFile`, per-channel resolution/unit and
  microvolt conversion, endian declaration, GET/HEAD identity, and all 18 canonical
  object fields. No `.eeg` GET/range request occurred; raw data remains unopened.

Final focused test after source-lock regeneration:

`.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc1_raw_replication.py -q -p no:cacheprovider --basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc1_pytest_20260825k`

- PASS: `3 passed in 0.92s`.

## Final static validation

`.codex\\hooks\\python.cmd python -c "... assert hashlib.sha256(lock_bytes).hexdigest()==m.SOURCE_LOCK_SHA256; m.validate_source_lock(...); print('SOURCE_LOCK_CANONICAL_AND_HASH_PASS')"`

- Output: `SOURCE_LOCK_CANONICAL_AND_HASH_PASS`.

`.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc1_raw_replication.py -q -p no:cacheprovider --basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc1_pytest_20260825m`

- PASS: `4 passed in 0.98s`.
- Includes source-lock digest mismatch rejection and final transaction ordering:
  result receipt first, terminal `RAW_COMPLETE` progress second.
- No `.eeg` GET/range request or raw retry occurred.

## Attempt 1 terminal validation receipt

The audit-approved raw command `.codex\\hooks\\python.cmd python
examples\\brain\\ba_obs_hpc1_raw_replication.py raw-one-shot` ran in session
`75271` and exited `1`. `artifacts/raw_progress.json` has SHA-256
`ce502e77ff83186359259e6129b06d6580c07187740a945a14c7310687a76934` and records
`RAW_STOP` for `ATTEMPT1`.

It contains one and only one completed-file receipt: TS / p16 / eppre / pre, with
the locked expected/observed object SHA-256, `60480000` expected/observed bytes,
version ID, ETag, header SHA-256, and contact indices 141/142 recorded in
`30-implementation.md`. The next frozen path was TS / p16 / eppost / post clinical;
`_clean_summary` stopped with `STOP_MEASUREMENT_APERTURE` before a completion receipt,
so the clean count that failed is unknown.

`raw_result.json` does not exist. Accordingly no endpoint, inference, status lattice
result, Nature Source Data cross-check, or biological conclusion exists. This is a
terminal blocked result for this contract version: no retry, cohort reduction, or
threshold adjustment is authorized. Any future work must use a separately registered
successor with an outcome-blind QC aperture, without selecting a threshold from these
unknown counts.
