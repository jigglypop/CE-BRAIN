# BA-OBS-ID1 focused implementation validation

Status: COMPLETE

Validation was intentionally limited to the new deterministic witness:

```text
.codex\hooks\python.cmd doctor
.codex\hooks\python.cmd python -c "from pathlib import Path; compile(Path(r'_workspace/ce/brain-finite-observation-metric-identifiability-escape-20260824/artifacts/validate_metric_escape.py').read_text(encoding='utf-8'), 'validate_metric_escape.py', 'exec')"
.codex\hooks\python.cmd python _workspace\ce\brain-finite-observation-metric-identifiability-escape-20260824\artifacts\validate_metric_escape.py
```

The final command writes `artifacts/metric_escape_receipt.json`, prints its
SHA-256, and returns nonzero if any preregistered gate fails.  This machine
check verifies implementation behavior only; it does not prove the theorem
and does not validate a biological, consciousness, self, or AGI claim.

`doctor` reported Python 3.11.9, NumPy 2.4.6, bytecode disabled, and status
PASS.  The source `compile()` command exited 0.  The receipt command exited 0
and printed:

```text
{"receipt": "C:\\dev\\ce\\ce-agi-runtime\\_workspace\\ce\\brain-finite-observation-metric-identifiability-escape-20260824\\artifacts\\metric_escape_receipt.json", "sha256": "9adc50dac7df5ba87a75a357c2414dd0575a1777621eef59ffeb76075dd54b49", "status": "PASS"}
```

The four `(truth, estimate, absolute error, active Gramian, holdout error)`
rows were `(-1.2, -1.2000000000000002, 2.22e-16, 0.0248154, 1.42e-32)`,
`(-0.4, -0.40000000000000013, 1.11e-16, 0.0421300, 8.23e-33)`,
`(0.3, 0.29999999999999993, 5.55e-17, 0.0403341, 0.0)`, and
`(1.1, 1.1, 0.0, 0.0241132, 0.0)`.  The negative-zero control had Gramian
and grid-loss spread both exactly `0.0`; every frozen gate passed.

Before this final validation, the first execution STOPped because its
negative-control loss was inadvertently evaluated against active TRAIN
schedules.  That was an implementation-only mismatch with the frozen
`NEGATIVE-ZERO` contract, not a model, threshold, data, or formula failure.
The repair changed only the loss evaluation to the zero-input schedule; the
protocol, truth set, thresholds, RK4 integrator, and grid-plus-golden
estimator remained unchanged.  The final script was not rerun for this
documentation-only update.
