# BA-SELF1 A1/A2 byte-range apparatus

Status: COMPLETE

Scope is limited to the sealed `sub-01/ses-02` apparatus allocation: A1's 8
trials and A2's additional 24 trials. D1, D2, C1, C2, C3, unused trials, and
all fMRI objects remain unopened. `scientific_endpoint_opened=false` in both
receipts.

## Implementation

`artifacts/brainvision_range.py` SHA-256:
`b075b9deb34c6a5e93ab58eabeb378a38c2e69045b4155d219252154baa3d559`.

For every task/rest anchor it requested only samples `anchor-2500` through
`anchor+500`, inclusive (3,001 samples, 768,256 bytes), using one HTTP Range
GET. Each response had to be `206`, exact `Content-Range`, exact byte length,
and the A0-recorded ETag. The bytes were decoded only in memory as little-
endian multiplexed 64-channel float32; channel 32 (`ECG`, zero-based index 31)
was removed, the remaining 63 channels were common-average referenced, then a
causal 501-tap Hamming `firwin(45 Hz, fs=5 kHz)` and `lfilter` was applied.
The first 500 samples were discarded and every twentieth remaining sample was
kept with the anchor on-grid. No zero-phase filter, delay compensation, raw
byte persistence, endpoint loss, model fit, or effect estimate was used.

## Receipts

- A1: `artifacts/a1-range-receipt.json`, SHA-256
  `ac6511152a10cb9682a324513e969eb4e701063aa996e6ca7c33fcefd21bd93f`;
  `A1_APPARATUS_PASS`, 16 task/rest windows.
- A2: `artifacts/a2-range-receipt.json`, SHA-256
  `8f37e315b2a2fb808c24c60ab10f5bd3c177ad31c3e00498634c6894bc1ac8d5`;
  `A2_APPARATUS_PASS`, 64 task/rest windows.

A2 froze QC from those 64 windows. Cutoffs are 281.5218166091819 for maximum
absolute common-reference amplitude and 95.39727548778933 for maximum
absolute first difference. Five of 32 task/rest pairs are marked excluded by
the predeclared paired QC rule. This is a measurement/QC fact only, not a
scientific result.

## Environment and command

Interpreter: `C:\\Users\\dongh\\AppData\\Local\\Programs\\Python\\Python311\\python.exe`,
Python 3.11.9, NumPy 2.4.6, SciPy 1.17.1.

```
.codex\hooks\python.cmd python ...\artifacts\brainvision_range.py --stage A1 ...
.codex\hooks\python.cmd python ...\artifacts\brainvision_range.py --stage A2 ...
```

Both commands produced the receipts above. No Git state was changed.

## D1 draft and stop

`artifacts/self_trajectory_d1.py` SHA-256:
`a39b6efb25c9c0a81c123b42a625577c2981e270fa65d2f72c5a2b0bfda9f9a6`.
The implementation fixes the D1-only manifest scope, A2's frozen QC, paired
leave-one-trial-pair-out folds, fold-local robust channel scaling/PCA whitening,
and the fixed feature menu. It applies outcome futility only to d=2/3; d=4 is
diagnostic-only and explicitly deferred to D2. It selects nothing in D1.

Execution stopped before either screen because the frozen A2 QC accepted zero
D1 trial pairs. The receipt-only failure-path repair preserves all 64 already
computed range/QC diagnostics without changing a cutoff, transform, feature,
split, model, or outcome rule. `artifacts/d1-receipt.json` SHA-256
`d05bd70e013a09cfb47d4ab0cb3bb507bba7839fbb00b98a9988246279da92d2`
records `D1_FAIL_CLOSED`, `scientific_endpoint_opened=false`,
`model_outcome_computed=false`, 0 accepted pairs and 32 rejected pairs.

The first execution attempt wrote no receipt because of an implementation
defect, and the first repair wrote only a minimal fail-closed receipt. Its exact
contents and SHA-256 are preserved as
`revisions/d1-receipt-minimal-v1.json`,
`b9ba7c105f691056c0983749b9b8e0d954bf7c94e0144f948c69957902096d71`.
`revisions/d1-execution-receipt-repair-v1.md` records the repair boundary. No
scientific endpoint was computed in any attempt.
