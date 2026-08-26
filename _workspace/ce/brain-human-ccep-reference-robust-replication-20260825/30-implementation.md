# BA-OBS-ID4 implementation receipt

Status: COMPLETE

## Implemented, signal-blind apparatus scope

`artifacts/id4_ccep_apparatus.py` (SHA-256
`3020037FCD986263B9DBD902C8DCA388A5F822F4AE3478D719B2890FCF682599`)
implements only the Gate-PASS scope authorized in `20-audit.md`:

- canonical-site eligibility for `ieeg`/`seeg`/`ecog` good channels, required
  biphasic event type (including `electrical_stimulation_type`), explicit-polarity
  and reversed-original-site-orientation exclusion, contact-overlap/midpoint-distance
  exclusion, zero-based even/odd half counts, and frozen subject/pair SHA-256
  allocations from TSV text or caller-owned metadata;
- dimensionless nonnegative `d`, patient median `u`, `v`, `R`, `Delta`, and the
  fixed three-confirmation-patient result-label rules;
- deterministic Gaussian/centered-$t_5$ adverse-control generators, the
  source/half-direction heteroscedastic restricted-null shape, a directed
  $log(1.6)$ fixture, and a common-reference component whose bipolar difference
  cancels it;
- a small explicit `mef3io==1.1.2` adapter exposing a bounded uUTC half-open
  `random_window` and exact sample/time/unit validation. It requires/derives an
  allowed channel set and rejects unknown channels, nonfinite/noninteger or reversed
  uUTC, windows over 1,000,000 uUTC, predicted samples over 2,048, and returned raw
  bytes over 10,240 before endpoint use. Without a caller-supplied executable fixture
  path and allowed channels it remains `APPARATUS_MEF3_RANDOM_ACCESS_STOP`.
- pure offline `.tidx` planning: 1024-byte universal header plus exact 56-byte
  little-endian `<qqqIIii16s>` rows. The semantic fields are offset, start time,
  start sample, `number_of_samples` (byte 24), and `block_bytes` (byte 28);
  byte 44 is official RED flags (`tail[4]`), exposed as `red_flags` and bit-0
  `discontinuity`; bytes 40--43 and 45--55 remain uninterpreted. It applies
  strict offset/time/sample/block validation,
  and merged half-open `.tdat` range planning that always includes its 1024-byte
  universal header.

The module has no dataset URL, download routine, raw-signal decoder, confirmation
execution mode, or dependency-install step.  It therefore cannot open the frozen
confirmation signal.

## Small receipts

`artifacts/synthetic-adverse-controls-full.json` (SHA-256
`E6C5F06A18D54D99A4934828AEC28CF4F3A2208BFE4A867BE587C78A1B0D2FFF`)
records the contract's deterministic
256-seed gate. Gaussian/centered-$t_5$ false refutations were `6/256` and `6/256`
against the frozen maximum `7/256`; directed detections were `256/256` and
`256/256` against the frozen minimum `205/256`. The common-reference fixture had
`mean_R=428571428572.3673` and `bip_R=1.0`. This is apparatus evidence only and
the receipt explicitly records `signal_accessed: false`.

`artifacts/mef3-capability-receipt.json` (SHA-256
`29D968488A78AD2FEAFFE1AD092EC564978ABD8E4B018C28F1BD3C6ECE9CD21B`)
records the installed `mef3io` adapter at version `1.1.2`, but also records
`APPARATUS_MEF3_RANDOM_ACCESS_STOP`: no executable fixture path was supplied and
`signal_accessed: false`. Its nested sample-index state is independently
`APPARATUS_MEF3_SAMPLE_INDEX_STOP`: uUTC-only mef3io capability does not establish
exact sample-index equivalence, so development remains closed.

`artifacts/mef3-transient-fixture-receipt.json` (SHA-256
`E09828FEA1D5E6B4DF39FDD95AB69C9A216E0396F3F3C0C2C33B7F77AC652D44`)
records independently observed capability evidence only.  It records the
official `ds004457` tag `1.0.2` / commit `1bbd...`, `sub-1` `LV1`, supplied
`.tmet/.tidx/.tdat` hash identifiers, `2048 Hz`, microvolts, uUTC
`[81209476921,81210476921)`, 2048 finite samples, the supplied min/max/mean, and
cleanup `true`.  Root executed full-file capability first, then the range-minimal
proof: `.tmet` 16,384 bytes, `.tidx` 196,016 bytes, and `.tdat` prefix 2,960 bytes
(first row offset 1024; block 1936 bytes). The identical 2048/2048 finite/min/max/
mean result is recorded with `endpoint_evidence: false`, `development_opened: false`,
and `confirmation_opened: false`. This independent fixture resolves the decoder
capability gate only; it explicitly leaves sample-index equivalence stopped and
does not open development or confirmation.

`artifacts/metadata-plan-receipt.json` records the corrected implementation applied
to the official v1.0.2 BIDS TSV metadata in memory. It retains $431,244,502,264,308$
pairs, excludes the mixed-orientation `sub-5` node `RK1-RK2`, and records every
subject's development/held-out counts with `signal_accessed: false`. No fetched TSV
or raw payload was persisted.

## Environment boundary

`.codex\hooks\python.cmd doctor` stopped with:

```text
ModuleNotFoundError: No module named 'torch'
```

The wrapper's direct Python mode remained usable with
`C:\Python314\python.exe`, Python 3.14.2. No virtual environment, `uv`, package
installation, or download logic was used by this implementation; the separately
recorded root LV1 transient was a bounded capability fixture, not endpoint access.

## Development range-planning build

`artifacts/id4_development_range_plan.py` (SHA-256
`82296D2A82351C6598BB2E419EF179900C6D2F65BBCA4FAD60DADDEE758814CC`)
is a source-locked, offline planner only. It accepts caller-supplied BIDS TSV text,
full `.tidx` byte buffers, exact `.tdat` sizes, and `2048 Hz`; it permits only
`sub-1`/`sub-5`, exactly all good `ieeg`/`seeg`/`ecog` CAR75 channels, and eligible good
6 mA biphasic canonical-node events. It reads each BIDS onset lexeme with exact
`Decimal`. An exactly integral `onset * 2048` is retained directly; otherwise the
hash-locked lexeme exponent defines a half-ULP interval in sample units and the
planner accepts only when that interval contains exactly one integer sample. Empty,
ambiguous/tied, or duplicate same-site sample mappings fail closed. This is an
explicit source-representation assumption, not a biological timing-precision claim.
All selection and coverage uses sample intervals rather than rounded uUTC. The frozen
`decimal-onset-lexical-ulp-sample-grid-v4` convention uses acquisition `[n0-1024,n0+103)`,
baseline `[n0-1024,n0-10)`, early `[n0+21,n0+103)`, and prestim
`[n0-512,n0-430)`; those windows are recorded as later endpoint metadata. Every
channel must start at sample 0 with one shared first uUTC. Byte/time monotonicity
checks remain exact, including rational time-end comparison without float rounding.
For a window that actually continues into the next selected block, exact sample
adjacency is required and the next parsed RED `discontinuity` bit must be false.
Block timestamp residuals are not an epoch-continuity criterion: parser-level
strictly increasing start uUTC/offset/sample starts and planner byte/sample extent
checks remain fail-closed. It rejects gaps, uncovered windows, inconsistent channel timing, wrong
source/subject, and confirmation subjects.
When recognized nonblank event provenance columns are present, `source`,
`dataset`, `dataset_id`, and `snapshot` must exactly equal `ds004457-v1.0.2`;
`subject` and BIDS `participant_id` must exactly equal the current development
subject. Conflicting/mixed labels stop before windows are formed.

Its single-pass validated selector walks sorted merged windows and index rows once,
selecting/counting each physical block at most once even when it spans multiple
non-overlapping windows. It then emits JSON-serializable merged half-open `.tdat` byte ranges, per-channel
supplied-index SHA-256, block count and byte count. Aggregate fields distinguish
`supplied_tidx_bytes`, `planned_tdat_bytes`,
`max_per_channel_planned_tdat_bytes`, and `planned_persistent_raw_bytes: 0`; `.tmet`
and HTTP overhead are explicitly excluded until supplied. It has no URL, download,
sparse-file, signal, or endpoint path.

## Development metadata/index acquisition build

`artifacts/id4_development_index_acquire.py` (SHA-256
`1E1D12438E7962A04A90FBF91094E7C0FE04FE1A1A0822584586CEA3694B51C3`)
adds an injected-transport source-locked acquisition boundary. It accepts only
development subjects, uses raw GitHub paths pinned to commit
`1bbd3a0696c56b7dfd87020bc61092644a702d0a` for TSV and annex pointer text,
and uses the exact `s3.amazonaws.com/openneuro.org/ds004457/` object prefix.
All path construction is derived internally from locked subject/exact channel names
and constrained to those hosts/prefixes; optional caller maps must be exactly equal
to the derived maps. Response sizes are capped, timeout is 30 seconds, and the
receipt records sequential `concurrency: 1`. Production urllib rejects non-HTTPS,
off-prefix, and final redirect-host/path escapes.
Its transient-only retry policy is at most three attempts with bounded 0.05 s then
0.10 s backoff; HTTP/permanent validation failures are not retried. An optional
progress callback receives `(completed, total, channel)` only after a channel has
fully passed pointer/index/HEAD verification and cannot change the receipt.

`CurlTransport` is an audited Windows alternative that resolves an exact
`curl.exe`, invokes only argv lists (never a shell), uses `-f -sS -L`, connect/max
time and max-file-size caps, writes binary GET bytes only to memory, and parses HEAD
headers only from stdout. It validates both requested and curl effective HTTPS URLs,
retries only bounded transient curl exits, and creates no temporary files.
`--max-filesize` is applied only to body GET; HEAD omits it because curl applies that
option to the remote object Content-Length. HEAD instead uses its captured-stdout
16 KB post-cap and max-time.

The channels TSV is parsed with exact `csv.DictReader` fields `name`, `type`, and
`status`; duplicate/unsafe names are rejected and only exact `status == good` with
the three allowed iEEG types is retained. Thus substring cases such as `good2` do
not acquire a channel.

It verifies frozen TSV hashes, annex `SHA256E-s<size>--sha.ext` pointers, full
supplied `.tidx` size/SHA-256, and `.tdat` HEAD size plus nonblank ETag/VersionId.
It never GETs or ranges an S3 `.tdat` object. A caller-selected atomic resume
checkpoint contains only the locked identity, completed channel provenance,
range hash/count/bytes, shared first uUTC/sample, the sample-grid convention and
version (checkpoint schema 5), and a canonical payload SHA-256. On resume it requires the
exact top-level and completed-entry schemas (no extras), matching channel names,
valid SHA-256 values, positive byte/count fields, nonblank ETag/VersionId, and the
matching TSV/good-channel/first-uUTC/sample-grid identity before skipping any channel. It never
stores raw `.tidx`, `.tdat`, or ranges. The compact receipt retains only TSV hashes,
channel provenance, hashes/counts/bytes of planned ranges and truthful unique
verified byte totals: `verified_unique_tsv_bytes`,
`verified_unique_pointer_bytes`, `verified_unique_tidx_bytes`,
`planned_tdat_bytes`, and `planned_persistent_raw_bytes: 0`. It explicitly marks
`wire_transfer_bytes_status: NOT_CLAIMED_RETRIES_AND_RESUME`; it does not claim
wire-byte totals across retries or resume. It sets `signal_accessed: false`,
`development_index_opened: true`, `development_signal_opened: false`, and
`confirmation_opened: false`.

The MEF3 segment path is exactly
`{subject}/ses-ieeg01/ieeg/{subject}_ses-ieeg01_task-ccep_run-01_ieeg.mefd/{channel}.timd/{channel}-000000.segd/{channel}-000000.{tidx|tdat}`.

## Completed v4 development index plans

The signal-blind v4 acquisition completed all good channels for both development
subjects despite bounded DNS/HEAD interruptions, using only compact schema-5
checkpoints. `development-index-plan-sub-1-v4.json` covers 154/154 channels and has
SHA-256 `CDB3385FCD936E6835E9E0AC2DD36D8AF6C40F0BE44F5307D5FDF1753D16BE2B`;
its planned `.tdat` ranges total 179,221,944 bytes. The matching COMPLETE checkpoint
has SHA-256 `54D6EC62CDA6C5C3014AC2E10B9FBF7216CE8648C73595C5712DFF0119FAAFA6`.

`development-index-plan-sub-5-v4.json` covers 156/156 channels and has SHA-256
`A32FC05C7EB8868CCAC880B1AEAFEEEFD24EBA4D116D3B4E5B4AFAE28FB84112`;
its planned `.tdat` ranges total 225,625,112 bytes. The matching COMPLETE checkpoint
has SHA-256 `26838223BD5A6B8FE46BE04871F0E57DF46AC41286C8A63B5438E0785D24DE33`.
Both receipts record precision convention 4, `planned_persistent_raw_bytes: 0`,
`signal_accessed: false`, `development_signal_opened: false`, and
`confirmation_opened: false`. Neither receipts nor checkpoints contain raw range
arrays, `.tidx/.tdat` bodies, or raw payloads. The planned byte totals are future
signal-window budgets only, not downloaded signal bytes.
