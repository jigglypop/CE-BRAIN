# E1 local metadata receipt validation

Status: COMPLETE

Focused command (no full suite):

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
.codex\hooks\python.cmd pytest tests/test_e1_metadata_receipt.py -vv -s --tb=short
```

Covered scope: fixed SHA-256 vectors, two-run equality of both byte streams
and hashes, optional-field exclusion, integer ordering, exact duplicate and
conflict policy, built-in-ID restriction, NFC/control/invalid-surrogate
rejection, strict time normalization, missing fields, and empty-response
behavior.

Final result (2026-08-25): **18 passed in 0.07 s**, Python 3.14.2, pytest 9.0.3.
No assertion was bypassed, no alternate interpreter was substituted, and no
broader suite was run.

Before this successful run, the default plugin-loading path and `doctor`
returned `MemoryError` during standard-library/NumPy imports; an attempted
fallback also once failed to start a thread before collection. These are
retained as host-environment diagnostics and are not counted as test results.
Disabling only external pytest plugin auto-loading allowed the same repository
hook and interpreter to execute the focused test normally.

This is local implementation evidence only. Remote metadata access, actual
response-schema/nullability validation, unit/channel/probe/NWB/LFP/spike data,
and every scientific inference remain unexecuted.
