# BA-OBS-ID3 validation receipt

Status: COMPLETE

Result: `REFERENCE_SENSITIVE_OR_INCONCLUSIVE`.

## Commands and results

```text
.codex\hooks\python.cmd doctor
PASS: C:\Users\dongh\AppData\Local\Programs\Python\Python311\python.exe
Python 3.11.9; numpy 2.4.6; bytecode disabled.

.codex\hooks\python.cmd python -c "... compile(ba_obs_id3.py, ..., 'exec') ..."
PARSE_PASS

.codex\hooks\python.cmd python ...\artifacts\ba_obs_id3.py fixtures
RuntimeError: STATISTICAL_FALSE_POSITIVE_STOP:
{"gaussian": {"refutations": 30, "raw_gt": 142, "n": 256},
 "t5": {"refutations": 17, "raw_gt": 121, "n": 256}}
```

The preliminary fixture invocation exposed an `AxisError` in NumPy bootstrap indexing;
it was fixed before the recorded substantive run.  It neither opened nor requested an
iEEG signal object.

## Invalid initial diagnostic

The earlier 30/256 Gaussian and 17/256 $t_5$ result is **IMPLEMENTATION_INVALID** because
the scalar surrogate was not the frozen two-readout, actual-site, source-shared operation.
It is not a valid formula failure or biological result.

## Corrected validation evidence

`artifacts/fixture-receipt.json` records the corrected 256×2048 gate:

- Gaussian: composite refutations 1/256; raw $R>1.25$ mean/bipolar 61/80.
- centered $t_5$: composite refutations 0/256; raw $R>1.25$ mean/bipolar 61/62.
- directed $\log(1.6)$ power: 256/256 in both scenarios.
- full-window equivalence masks: baseline/early/pseudo 1014/82/82 samples.

The version-locked real development receipt has 255 range records (the frozen eligible
24-site trials, not all 391 good events), each status 206 with
the exact requested Content-Range, frozen ETag/VersionId, byte count and SHA-256.  Its
fixed 42-pair development gate passed:

- mean: Spearman 0.6267085; early/prestimulus 1.9538596; 84 directed edges;
- bipolar: Spearman 0.5180520; early/prestimulus 1.3527095; 84 directed edges.

## Executed, invalidated, and final-run history

- Official S3 `HEAD` identity, metadata lock, marker crosswalk, corrected fixtures and
  development: **PASS**.
- The earlier same-half confirmation numbers ($R_{mean}=1.9083274$,
  $R_{bip}=1.2582018$) are **IMPLEMENTATION_INVALID**: the contract requires
  cross-half reciprocal disagreement.  They are not an empirical verdict.
- Corrected cross-half confirmation, $B=8192$: **RUN ONCE** after the 255-range
  audit; every reacquired range SHA-256 matched its development receipt, with ordered
  reacquisition-record SHA-256 `ccc18836493d7c52117faeb11210c13371c53683dd697e321788abb0e899f2ea`.
- mean readout: $R=1.8848874$, tail $=0$, $p_R=1/8193=0.0001220554$.
- bipolar readout: $R=1.1852950$, tail $=673$, $p_R=674/8193=0.08226535$.
- Confirmation serialization: **true**, receipt
  `artifacts/confirmation-receipt.json`; shared selection-index SHA-256
  `352d4ed84f4c8bc86b3563ebbbca6d2e19e91230b459eb9c76af5453f07982db`.

Both references require $R>1.25$ and $p_R\le0.025$ for the P1 proxy refutation.
The bipolar readout misses both the raw-$R$ tolerance and the tail condition, so the
frozen final label is
`REFERENCE_SENSITIVE_OR_INCONCLUSIVE`.  This is a conditional single-subject observed
CCEP result, not evidence for a neural metric, consciousness, self, hippocampal hash, or
AGI.

No full test suite was run. `git diff --check --
_workspace/ce/brain-human-ccep-restricted-active-response-20260824` returned success.

## Required next action

Do not retune this run.  A future replication requires a new contract and independent
source lock; this run's confirmation has been consumed.
