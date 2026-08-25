# HPC5 focused validation

Status: COMPLETE

Commands run (no network/raw analysis):

```text
.codex\hooks\python.cmd python -m compileall -q examples\brain\ba_obs_hpc5_author_intended_recheck.py
.codex\hooks\python.cmd pytest tests\test_ba_obs_hpc5_author_intended_recheck.py -q -p no:cacheprovider
```

Final stable result: `15 passed` in 4.79 s.  SciPy emitted one expected kurtosis warning for
a constant synthetic fixture; it does not change the tested nonfinite-mask
semantics.

The focused suite covers exact corrected masks and integer-cycle DFT removal,
A/B path parity including p17 filtering, nonfinite/reason-mask behavior,
strict endpoint-free Q receipts and diagnostic tampering, frozen loader/object
identity, zero-clean Q preservation, source-versus-implementation terminal states,
prior-receipt and endpoint-stage preconditions, receipt/progress mutual binding,
orphan authority, and journal/receipt pre- and post-commit failure recovery.
It also retains endpoint receipt tampering and clinical zero-cell stopping tests,
but these do not authorize Stage E. It does not fetch any OpenNeuro object or
produce a biological endpoint.

Stable hashes:

```text
executor 79191826af3a28b174cc793119817e1536e9466f9a162d1dcc05bea724b25c54
tests    7c7d6a470c09b5e8386a8b2127892e4336038e651acafe96af8772c11b3a6d78
lock     5cce4a71f03090793ed21d8316cbf8fc0b9b4403ae077e331963d7c1cda2e470
loader   8e9358ea72217b4f0d48f96d174ec506f3b2faf4b55cb2d2ebcc3248a93fb85c
```

## Actual one-shot QC_RECHECK1

```text
.codex\hooks\python.cmd python examples\brain\ba_obs_hpc5_author_intended_recheck.py recheck-one-shot
QC_RECHECK1
```

The transaction downloaded and verified exactly two version-pinned OpenNeuro objects
(83,300,000 bytes total). Expected and observed SHA-256, size, version ID, and ETag all
matched the frozen source lock. The completed progress journal is mutually bound to the
receipt by SHA-256 and exact records.

| target | HPC4 old-grid clinical | corrected clinical | HPC4 old-grid bipolar | corrected bipolar |
|---|---:|---:|---:|---:|
| TS/p17/post | 11 | 12 | 25 | 25 |
| PB/p17/pre | 22 | 24 | 11 | 11 |

Clinical amplitude rejection changed from 48 to 47 trials for TS and from 38 to 36 for
PB; all other reason counts and bipolar counts were unchanged. The largest A/B waveform
difference was `6.071e-11 µV`, below the locked `1e-6 µV` tolerance.

```text
qc_recheck1.json    04edcbe5c290985f6a59c230989f4d13d83323e193767559ec4e15562de9e6e6
recheck_progress    da9d5d5f77d31632640faef11b3fb8cc7b44068c849c051d0db658938a06d679
status              QC_RECHECK1 / COMPLETE
raw_result.json     absent
endpoint_progress   absent
```

Authorization ceiling: `QC_RECHECK1_COMPLETE_ONLY`. `ENDPOINT1` remains `BLOCKED`.
This receipt is a QC/apparatus result, not a biological endpoint.
