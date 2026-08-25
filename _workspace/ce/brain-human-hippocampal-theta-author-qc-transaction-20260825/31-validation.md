# BA-OBS-HPC3 validation

Status: COMPLETE

`.codex\\hooks\\python.cmd python -m py_compile
examples\\brain\\ba_obs_hpc3_author_qc_transaction.py` passed.

Focused transaction fixtures:

`.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc3_author_qc_transaction.py -q -p no:cacheprovider --basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc3_pytest_2`

- Final command used `--basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc3_pytest_4`:
  `4 passed in 1.37s`, plus `py_compile`.
- Covers strict JSON NaN refusal, resolver authority ordering, injected endpoint and
  aggregate failures, and terminal endpoint-free implementation stops. No
  network/raw execution occurred.

Additional authoritative-journal fixtures used `--basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc3_pytest_5`: `6 passed in 1.74s`.
They verify result authority after post-result journal failure, QC authority after
post-QC journal failure with recursive endpoint-key blacklist, and independent prior
progress/QC/result rejection before loader construction. No network/raw execution
occurred.

Final no-network command used a source-only in-memory compile and
`--basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc3_pytest_6`:

- `SOURCE_COMPILE_PASS`; `8 passed in 1.67s`.
- Adds inherited source-lock/static-receipt tamper rejection before loader construction
  and a fake version-pinned reader covering URL version ID, GET metadata, full SHA/size,
  sample-major `<f4` multiplexing, ordered scales, channel-wise bipolar, and mismatch
  rejection. No raw/network execution occurred.
