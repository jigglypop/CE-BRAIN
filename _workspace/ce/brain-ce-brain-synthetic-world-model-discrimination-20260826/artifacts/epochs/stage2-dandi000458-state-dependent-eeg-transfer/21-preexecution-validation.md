# Stage 2 pre-execution validation

Status: COMPLETE / OUTCOME_BLIND

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\epochs\stage2-dandi000458-state-dependent-eeg-transfer\test_stage2_dandi_state_transfer.py -q
```

The initial stable result was `8 passed in 1.00s`. After independent audit found
missing series-column mapping, timing-tie and raw-result verification gates, the
suite was expanded; the final result is recorded after the focused rerun.
Pre-amendment stable result: `10 passed in 1.12s`. Final post-amendment stable
result: `11 passed in 1.00s`.

The suite uses synthetic arrays and temporary text files only. It does not open
or download real DANDI EEG values. It covers nearest-origin timing, registered
split counting, exact artifact substitution, common-average/baseline/shape
mechanics, deterministic global-gain statistics, state-mean cancellation,
the revised three-way decision partition, explicit DynamicTableRegion mapping,
nearest-sample ties, manifest mutation rejection and exact independent result
comparison.

The first local schema-only attempt stopped on timestamp uniformity before any
EEG sample value was opened. Metadata-only diagnosis and the registered
post-gap segment amendment are recorded separately; its focused regression is
included in the final rerun.

Real remote HDF5 metadata probing was outcome-blind and left
`ElectricalSeriesEEG/data` values unopened. Local raw identity, full schema
receipt and one-shot manifest sealing remain pending the external temporary
download.
