# BA-OBS-HPC1 implementation

Status: COMPLETE

Scientific disposition: BLOCKED / STOP_MEASUREMENT_APERTURE

Implementation owner: CE implementation lane. The implementation is limited to
`examples/brain/ba_obs_hpc1_raw_replication.py`, its focused fixture test, and this
run's receipts. It does not persist EEG voltage or waveform dumps.

## Fixed implementation choices

- The 18-object table, channel counts, trial blocks, contacts, timing grid, and
  windows are copied from `00-contract.md`; p20 is frozen to ordered contact D9 and
  local bipolar D9-D10.
- Source lock reads Git-annex pointer text, S3 HEAD fields, and version-pinned
  BrainVision headers only. It checks annex SHA-256 and size, all HEAD receipt
  fields, exact channel count/order and frozen contacts, and
  `bytes/(4*n_channels) == blocks*1000` before any `.eeg` GET.
- The public archive (`TSS-main.tar.gz`, MD5
  `6feba89b7c49fd661b39b589e8d9624a`) informs the artifact grammar:
  `zscore(squeeze(trial))` is sample-wise across trials with sample (N-1) standard
  deviation; `kurtosis(trial,[],3)` is bias-corrected Pearson kurtosis. The contract
  additionally fixes zero-variance z scores to zero. Thresholds are 500 muV, 5, and
  5. The implemented OLS sine/cosine nuisance removal and SciPy Butterworth are
  contract-defined Python operations, not claimed as exact FieldTrip/MATLAB parity.
- Raw execution is sequential/version-pinned, hashes every full object, extracts
  only the frozen clinical and local-bipolar contacts in memory, and releases the
  full object buffer before endpoint calculation. The code writes only summaries.
- The trial-level Satterthwaite LME is explicitly unavailable in this environment;
  the result receipt must preserve `PUBLISHED_MODEL_ENGINE_UNAVAILABLE` rather than
  manufacture a p-value.

## Attempt 0: invalid implementation, no result

- `source-lock` completed with `SOURCE_LOCK_PASS` and serialized
  `artifacts/source_lock.json` (18 records). Each receipt records annex SHA-256/size,
  version ID, ETag, content length, accept-ranges, version-pinned header SHA-256,
  channel order, and frozen channel indices. p20 is D9 index 54 and D10 index 55.
- The audit-approved `raw-one-shot` command was invoked with elevated public network
  access. Its exact command was `.codex\\hooks\\python.cmd python
  examples\\brain\\ba_obs_hpc1_raw_replication.py raw-one-shot`. The execution
  interface yielded `cell ID 30` and then gave no exit code or traceback; it created
  no `artifacts/raw_result.json` or raw file. Two exact child Python processes,
  PIDs 984 and 24580 (both start time 2026-08-25 19:41:57), were re-verified and
  terminated after a contract audit found a pre-baseline artifact-rule defect.
- This is `ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`, not an outcome. No endpoint,
  waveform, Nature Source Data, or biological verdict was accessed or retained.
- Revision awaiting audit moves baseline correction before amplitude, kurtosis and
  z-score rules; adds atomic per-file non-voltage hash/received-size progress
  receipts, seven leave-one-participant-out contrasts, status-lattice output, and
  atomic final-result writing. Raw must not be re-run until the parent registers and
  audits that revision.

No Nature Source Data was opened.

## Revision 1 implementation repair

The registered implementation revision now:

- parses and receipt-binds BrainVision `DataFile`, `ChN` name/resolution/unit,
  the `BrainVision-Core/FieldTrip-ieee-le` convention, and versioned-header GET versus
  HEAD identity; selected
  contact values are explicitly multiplied to microvolts before preprocessing;
- canonically validates every source-lock field against the frozen 18-object table
  before raw access, and binds the byte SHA-256 of that lock into the final receipt;
- writes exact expected/observed object digest and size, version, ETag, header hash,
  and selected indices per completed file; transaction state is atomic and uses only
  `ATTEMPT1`, rejects pre-existing progress/result paths, preserves completed entries
  on stop, and finishes as `RAW_COMPLETE` only after an atomic final receipt;
- serializes allowed aggregate clean mean waveforms and clean trial-level window P2P
  values, all seven LOO contrasts, and the revised status lattice. The unavailable
  mixed-model engine remains an explicit ceiling rather than a fabricated result.

The source lock was regenerated using only Git-annex pointers, S3 HEAD, and
version-pinned `.vhdr` GET metadata. It passes canonical validation for all 18
objects; no `.eeg` GET/range request was made.

## Final static transaction and lock freeze

- `raw_result.json` is atomically committed before `raw_progress.json` transitions
  to `RAW_COMPLETE`; therefore either a final result or a nonterminal/STOP progress
  receipt prevents a retry after interruption.
- The final header-only source lock is frozen by both canonical content validation and
  SHA-256 `0b3d92f998f626ed37f68d0dfb1188a777afb287975916beec1f623d10d3fc58`.
  Raw mode rejects any byte-different lock before it can issue an `.eeg` request.
- When a header omits optional channel-unit or endian declarations, the receipt names
  the applicable source convention as `BrainVision-Core-default-µV` and
  `BrainVision-Core/FieldTrip-ieee-le`; explicit incompatible endian hints still
  stop source identity.

## Attempt 1: measurement-aperture stop, no result

The audit-approved command `.codex\\hooks\\python.cmd python
examples\\brain\\ba_obs_hpc1_raw_replication.py raw-one-shot` ran as session
`75271` and exited `1`. Its only transaction receipt is
`artifacts/raw_progress.json`, whose SHA-256 is
`ce502e77ff83186359259e6129b06d6580c07187740a945a14c7310687a76934`.

- The receipt status is `RAW_STOP`, attempt ID `ATTEMPT1`.
- Exactly one completed file is recorded: TS / p16 / eppre / pre. Its integrity
  receipt verifies expected and observed SHA-256
  `5c19f0453e114ffef850adbd95b6a05eab4bd72158f70abd8180a77fe41ef6cc`,
  expected and observed size `60480000`, locked version ID
  `sVZSXO4kOS4MOrAF06Uzz5sAoSaE1vas`, ETag
  `"92cb4fc9003231b1fc907c67d02cee42"`, header SHA-256
  `cec6e1bc207941f43a5f708a0734f77da86c7ec5a2c5f5c35f61ab8a998c38dc`,
  and frozen clinical/bipolar indices 141/142.
- The next deterministic file/reference was TS / p16 / eppost / post, clinical.
  `_clean_summary` raised `STOP_MEASUREMENT_APERTURE` before that file obtained a
  completion receipt. Its failing clean-trial count is therefore unknown.
- `artifacts/raw_result.json` is absent. No endpoint, contrast, bootstrap, status
  lattice outcome, Nature Source Data, or biological verdict was produced.

This contract version is closed. There is no cohort reduction, threshold change, or
retry. Resumption requires a separately registered successor with an outcome-blind
QC aperture; this record supplies no basis for choosing a favorable threshold.
