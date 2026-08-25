# Validation

Status: COMPLETE

Focused, no-network validation used the repository Python hook.

```text
.codex\\hooks\\python.cmd python -m compileall -q examples\\brain\\ba_obs_hpc6_full_endpoint.py examples\\brain\\ba_obs_hpc6_full_endpoint_validator.py
.codex\\hooks\\python.cmd pytest tests\\test_ba_obs_hpc6_full_endpoint.py -q -p no:cacheprovider
```

Result after revision 1: `6 passed, 1 warning in 22.93s`. The warning is the
expected SciPy constant-trace kurtosis warning in the finite/NaN QC parity
fixture; it is not suppressed and does not alter the tested QC masks.

Revision 2 commands:

```text
.codex\\hooks\\python.cmd python -m compileall -q examples\\brain\\ba_obs_hpc6_full_endpoint.py examples\\brain\\ba_obs_hpc6_full_endpoint_validator.py
.codex\\hooks\\python.cmd pytest tests\\test_ba_obs_hpc6_full_endpoint.py -q
```

Before execution-lock freeze: `7 passed, 1 warning in 27.52s`.
Frozen code hashes are producer `cfe53970f2d88473c946eb20feb1976fe5926f108899ace5cc88d36f4ca065e8`,
validator `40e78a2491c371fb638f21e19ea6e8ff2caff414010c409a7a7475f54a432197`,
and tests `2142131018ccbd6ad7653229dcac0345bba31326a816b6186c93152f67a326d2`.

The focused test exercises a synthetic 18-object transaction, independent
witness validation, coordinated trialwise-P2P/aggregate tampering, waveform
tampering, witness-byte tampering, all-or-none bipolar omission, clinical-zero
terminal handling, source-integrity `SOURCE_STOP`, and prior-artifact refusal.
No full test suite and no raw/network execution were run.
