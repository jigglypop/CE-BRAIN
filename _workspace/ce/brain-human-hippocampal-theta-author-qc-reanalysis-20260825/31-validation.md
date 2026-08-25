# BA-OBS-HPC2 validation

Status: SKIPPED — raw validation authorization blocked; mock-only evidence retained below

Focused synthetic validation and header-only source-lock validation only; no raw stage
is authorized before independent audit.

Focused command: `.codex\\hooks\\python.cmd python -m pytest
tests\\test_ba_obs_hpc2_author_qc_reanalysis.py -q -p no:cacheprovider --basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_1`.

Final focused command used `--basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_2`:
`2 passed in 0.86s`. The constant-trace fixture emits SciPy's expected kurtosis
precision-loss warning while confirming the required pre-baseline 600-uV rejection.
The source lock was header-only; no `.eeg` GET/range request occurred.

Static transaction fixtures:

`.codex\\hooks\\python.cmd python -m pytest tests\\test_ba_obs_hpc2_author_qc_reanalysis.py -q -p no:cacheprovider --basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_3`

- PASS: `4 passed in 1.08s` (one expected constant-trace kurtosis precision warning).
- Covers author masks, pre-baseline 600-uV failure, p20 third-channel union, tampered
  lock rejection, 18-file QC-stop count collection without endpoint leakage,
  source-stop, all-pass result-before-progress sealing, and prior-transaction refusal.

Final aggregation fixture command used `--basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_4`:

- PASS: `5 passed in 1.24s` (same expected constant-trace warning).
- Validates participant D, deterministic bootstrap reproduction and 65,536-draw shape,
  seven LOO, paired p17/p19 sensitivity, sensitivity flags, and clinical non-support.

Revision 2 focused mock-only command used `--basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_5`: `5 passed in 1.58s`.
It adds author-grid-basis differentiation, nonfinite trial isolation, and endpoint/QC
ordering coverage. No default loader or CLI raw-one-shot execution occurred.

Final mock-only loader command used `--basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_8`: `6 passed in 1.43s`.
It verifies sample-major little-endian multiplex decoding, ordered QC scales,
clinical-first endpoint identity, clinical-minus-next-contact bipolar, observed
SHA/byte receipt, and hash mismatch rejection through a fake response. No network was
called.

Final CLI mock plus compile command used `--basetemp
C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_9`: `7 passed in 1.24s`.
It confirms an exact frozen lock/static receipt dispatches one injected ATTEMPT1 call,
while pre-existing progress and byte-tampered lock fail before loader construction.
`py_compile` also passed. No raw/network execution occurred.

Final revision used `--basetemp C:\\Users\\dongh\\AppData\\Local\\Temp\\hpc2_pytest_10`:
`8 passed in 1.20s`, plus `py_compile`. It covers unequal-scale bipolar algebra,
implementation-stop sealing, nonfinite isolation, and non-downgrading early control.
No network/raw execution occurred.
