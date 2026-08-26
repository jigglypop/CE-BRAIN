# Stage 1 Allen pre-execution validation

Status: COMPLETE

Gate: PASS

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\epochs\stage1-allen-single-cell-local-dynamics\test_stage1_allen_local_dynamics.py -q
```

Stable result: `8 passed in 0.23s` (independent recheck: `8 passed in 0.24s`).

The mechanical suite uses compact temporary HDF5 or pure-array fixtures only.
It does not open the real Allen file, write the real schema/manifest/result, or
compute development/confirmation endpoints. It covers:

1. schema metadata, conversion, rate and index-range fail-closed behavior;
2. exact block alignment, history/future indices and degenerate spike fitting;
3. all frozen decision statuses including absolute Markov sufficiency;
4. raw identity and manifest mutation rejection;
5. schema receipt population/hash mutation rejection;
6. JSON-safe model serialization and stored-result reload verification;
7. model parameter, decision, manifest-link and row-receipt mutation rejection;
8. one-shot existing-result refusal.

Real schema-only command completed before this document and produced receipt
SHA-256 `0c3df6cf9c84b67a7debaad3825ea5b94be115ca2a80321baca814b1e9813fab`
with `confirmation_values_opened: false`. No real result or manifest existed
when this document was written.
