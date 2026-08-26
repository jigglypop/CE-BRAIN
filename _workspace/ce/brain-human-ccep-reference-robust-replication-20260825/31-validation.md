# BA-OBS-ID4 validation receipt

Status: COMPLETE

## Focused implementation validation

```text
.codex\hooks\python.cmd pytest _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_ccep_apparatus.py _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_range_plan.py _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_index_acquire.py -p no:cacheprovider

3 passed in 11.18s
```

The single focused test (`artifacts/test_id4_ccep_apparatus.py`, SHA-256
`A34134370E4E7A639B07ACF462DB2F6BEAB29841E79DECF695B5A2990F9EBE70`)
uses embedded TSV text only.  It checks `seeg`/`ecog` eligibility,
`electrical_stimulation_type` biphasic filtering, reversed site-orientation
exclusion, canonical site/pair/hash planning, dimensionless calculations and fixed
labels, deterministic 16-seed adverse smoke controls, bipolar cancellation of a
common reference, receipt writing, installed `mef3io==1.1.2` adapter recognition,
independent transient-fixture schema fields, synthetic `.tidx` parse/range planning
and rejection cases, byte-44 RED flag extraction (with other tail bytes ignored),
bounded-channel/window adapter stops, the no-path fail-closed MEF3 status, and the
separate uUTC-only sample-index-equivalence stop.

The first new range assertion stopped with
`APPARATUS_MEF3_RANGE_STOP:no overlapping index block`: an adjacent `.tdat` header
and first block correctly merge into one range, but the implementation mistook that
for no selected block. The stop was corrected by checking selected index blocks
before merge. The recorded passing command above is the corrected execution.

No full test suite was run. Development execution, confirmation serialization,
endpoint analysis, and any dataset download were not run. The separately recorded
root LV1 transient is bounded decoder capability evidence only.

## Prespecified 256-seed synthetic gate

```text
.codex\hooks\python.cmd python -c "... synthetic_adverse_controls(256) ..."
null: gaussian=6/256, centered-t5=6/256 (required each <=7/256)
power: gaussian=256/256, centered-t5=256/256 (required each >=205/256)
common-reference: mean_R=428571428572.3673, bip_R=1.0
status=PASS; signal_accessed=false
```

This validates the frozen synthetic apparatus criteria. It is not a biological
result and does not remove the MEF3 capability stop.

## Official metadata-only spot validation

The official `OpenNeuroDatasets/ds004457` tag `1.0.2` channels/electrodes/events
TSVs were read through the GitHub contents API into memory and passed directly to
`canonical_metadata_plan`; no signal object or TSV file was saved. Results were:

```text
sub-1 nodes=32 pairs=431 development=321 held_out=110 excluded=[]
sub-2 nodes=24 pairs=244 development=190 held_out=54 excluded=[]
sub-3 nodes=35 pairs=502 development=392 held_out=110 excluded=[]
sub-4 nodes=25 pairs=264 development=207 held_out=57 excluded=[]
sub-5 nodes=27 pairs=308 development=230 held_out=78 excluded=[RK1-RK2]
signal_accessed=false
```

This check found and corrected the pre-signal metadata count for `sub-5` from 354
to 308 after the contract-required mixed-orientation exclusion. The official CE
revision record is `impl-engineer 1/3`. This is apparatus validation, not a neural
endpoint.

## Capability blocker

The default capability call remains exactly `APPARATUS_MEF3_RANDOM_ACCESS_STOP`:
the installed adapter has no caller-supplied executable path or allowed-channel set,
so it fails closed before a read. The independently executed LV1 fixture resolves the
decoder capability gate only; it does not open development, confirmation, or a
biological endpoint and must not be bypassed by downloading the 11 GB dataset.

## Development range-planner validation

```text
.codex\hooks\python.cmd pytest _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_range_plan.py _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_index_acquire.py -p no:cacheprovider

Superseded by the three-file focused command above.
```

`artifacts/test_id4_development_range_plan.py` (SHA-256
`6F93A6AC5F478916FF6D024EA783A66F18D404EF06EB9861186D498F40789AF7`)
uses synthetic TSV/index buffers only. It validates deterministic index hashing and
byte arithmetic, the header-plus-adjacent-block merge, rejection of confirmation
subjects and wrong nodes, inconsistent per-channel timing, uncovered/gapped windows,
and out-of-file spans. It also proves sparse many-window selection, including two
separated windows covered by one long block with exactly one selected block/range,
requires every good channel rather than accepting a subset, and rejects adversarial
wrong event dataset/subject labels while accepting exact explicit locked labels.
It additionally accepts the exact contract example
`82.52587890625 * 2048 = 169013`, accepts the source-quantized example
`415.5825195` only because its lexical half-ULP interval has the unique sample
851113, rejects an onset outside that interval and ambiguous/tied candidates, and
accepts an exactly aligned coarse lexeme without float conversion. It rejects two
rows for the same stimulation site mapped to one sample. It proves exact cross-block sample
selection, locks the four sample-center epoch windows and `1024 + 56*3482 = 196016`
index cardinality, and asserts no float path is present. It accepts an LA1-like
`2049/2047` pair with `999999`-us start-time delta when RED bit 0 is clear, rejects
selected sample gaps/overlaps and a next-row RED discontinuity bit, and thereby
proves timestamp residual alone is nondecisive. No tdat body, network
resource, development signal, or endpoint was accessed.

## Development metadata/index acquisition validation

```text
Same two-file focused command above.
```

`artifacts/test_id4_development_index_acquire.py` (SHA-256
`3C36C20D77B4CF255105CB4B5AE53D0C5F0D76EA957CF8242EDEBE12863760DC`)
uses injected in-memory transport only. It proves deterministic compact receipts,
all-good-channel acquisition, annex/index identity checks, tdat size/version stops,
unsafe/cross-subject/wrong-channel path rejection, exact `good` versus `good2`,
unsafe channel rejection, subject rejection, and that no S3 `.tdat` body method is
called. It also covers one transient timeout followed by success, no retry for a
permanent HTTP error, and deterministic verified-channel progress order/count.
Literal official-path assertions lock both `sub-1/LV1` and a `sub-5` representative.
No real network invocation occurred in this focused test. Curl runner tests cover
binary GET bytes, parsed HEAD headers, effective-host escape, response caps, and a
transient curl timeout followed by one bounded retry. It further proves an
interrupted raw-free checkpoint resumes without re-fetching completed channels and
matches the uninterrupted source-plan receipt. Completed-entry planned-byte,
provenance, and schema-extra tampering stops even with a recomputed checkpoint
digest; stale digest/hash tampering also stops. The receipt reports only unique
verified TSV/pointer/tidx bytes plus planned tdat bytes and persistent raw zero;
wire-transfer bytes are expressly `NOT_CLAIMED_RETRIES_AND_RESUME`. Resume state
also locks the bumped v4 lexical-ULP sample-grid convention/version, checkpoint
schema 5, shared start sample 0, and shared first
uUTC; an older precision-incompatible checkpoint stops before any channel skip.

## Interrupted urllib operational attempt

The real urllib index-only attempt remained before the first 10-channel checkpoint
for more than four minutes with no active TCP connection. It was interrupted and
exited `1`; no receipt, temporary file, raw payload, source result, or biological
evidence was produced. This is an operational transport failure only.

## Stopped curl HEAD attempt

The subsequent real curl attempt stopped immediately at the first `.tdat` HEAD with
curl exit `63`: `--max-filesize 16384` was incorrectly interpreted by curl as the
remote object's Content-Length limit, rather than a header limit. No receipt or raw
payload was produced. HEAD now omits that option and applies the 16 KB cap only to
captured header stdout; the focused argv regression verifies this distinction.

## Interrupted curl checkpoint attempt

The real curl index-only run verified 30/154 channels (last checkpoint `LC1`) then
stopped at a later `.tdat` HEAD after bounded curl exit `28` retries; process exit
was `1`. No final receipt or raw payload was produced. The compact checkpoint/resume
tests cover raw-free state, skip of verified channels, bit-identical completion, and
tampered-checkpoint stop. Those earlier focused checks passed before this precision
revision; the superseding two-file focused result is recorded above.

## Pre-revision precision stop

The prior first-channel plan rejected a sample-aligned onset whose uUTC conversion
was not integral. It is classified `IMPLEMENTATION_INVALID`, not source, signal, or
endpoint evidence: no signal was opened or persisted. This revision removes that
incorrect microsecond-integrality requirement and retains exact sample alignment.

## Signal-blind lexical precision P0 and v4 correction

The first real `sub-5` v3 planning attempt stopped at `RA1` before checkpoint or
signal access because 331 of 344 eligible event onset lexemes were not exactly
integral after multiplication by 2048. Independent exact-Decimal verification
classified this as a P0 apparatus defect: for example,
`415.5825195 * 2048 = 851112.9999360`, while the lexeme's half ULP is only
0.0001024 sample and therefore identifies the unique sample 851113. Silently
dropping those trials or generic nearest rounding was prohibited.

Contract and implementation precision convention 4 instead accepts an exact
integral product directly, or a nonintegral lexeme only when its exact lexical
half-ULP interval contains exactly one integer. Empty, multi-candidate/tied, and
duplicate same-site sample mappings stop. This is a signal-blind adopted
source-representation rule; it changes no window cardinality (1127/1014/82/82),
split, readout, threshold, endpoint, or claim ceiling.

The focused post-v4 command was:

```text
.codex\hooks\python.cmd pytest _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_range_plan.py _workspace\ce\brain-human-ccep-reference-robust-replication-20260825\artifacts\test_id4_development_index_acquire.py

2 passed in 0.13s
```

## Completed real v4 index-only acquisitions

The source-locked curl path completed `sub-1` 154/154 and `sub-5` 156/156 good
channels using compact schema-5 checkpoints. Bounded interruptions were exclusively
curl exit 6 DNS failures or exit 28 HEAD timeout and were resumed without treating
wire retries as unique bytes. Final receipt evidence is:

```text
sub-1 receipt sha256=cdb3385fcd936e6835e9e0ac2dd36d8af6c40f0be44f5307d5fdf1753d16be2b
      verified tidx=30,186,464; pointer=66,836; TSV=73,848 bytes
      planned tdat=179,221,944; persistent raw=0 bytes
sub-5 receipt sha256=a32fc05c7eb8868ccac880b1aeafeeefd24eba4d116d3b4e5b4afae28fb84112
      verified tidx=38,764,128; pointer=68,016; TSV=82,736 bytes
      planned tdat=225,625,112; persistent raw=0 bytes
wire_transfer_bytes_status=NOT_CLAIMED_RETRIES_AND_RESUME
```

Both checkpoints are `COMPLETE`, precision 4, schema 5, with 154/156 completed
entries. Receipt checks confirmed `signal_accessed=false`,
`development_signal_opened=false`, and no raw ranges, `.tidx/.tdat` body, or raw
payload field. The earlier `development-index-plan-sub-1.json` and non-v4
checkpoint are superseded apparatus history and are not admissible under v4.
These index plans do not clear `APPARATUS_MEF3_SAMPLE_INDEX_STOP`; no development
signal or confirmation subject was opened.
