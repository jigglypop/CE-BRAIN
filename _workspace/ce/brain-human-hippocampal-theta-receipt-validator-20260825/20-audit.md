# BA-OBS-HPC4 audit and terminal closure

Status: COMPLETE

Gate: PASS

Final disposition: `TERMINAL_QC_STOP`

The final stable-snapshot preflight PASS authorized exactly one real `ATTEMPT1`. That
attempt has now been consumed and closed as
`QC_STOP_MIN20 / NO_RAW_RESULT / NO_ENDPOINT / NO_BIOLOGICAL_VERDICT / NO_RERUN`.
HPC3 ended with no raw attempt or endpoint, and HPC4 changed only strict numeric receipt
typing, deterministic P2P/aggregate recomputation, and the p20 three-channel
reason-count bound. The inherited source lock, static receipt, cohort, signal
processing, estimator, status lattice, and MIN20 aperture were not changed before the
attempt.

The stable implementation replayed every HPC3 adversarial counterexample and binds its
CLI and output receipts to this HPC4 run. Independent preflight implementation audit
reported zero P0/P1 after 36 inherited/transaction no-network tests; independent
mathematics audit confirmed full-block aperture, p20 reason algebra, nonnegative
waveform-derived P2P, and deterministic full aggregate recomputation.

## Post-run receipt audit

The terminal receipts contain 18 unique source objects and exactly match the frozen
source lock for SHA-256, byte size, OpenNeuro version ID, and ETag. The verified payload
is `723,560,000` bytes. `raw_progress.json` and `qc_result.json` both name `ATTEMPT1`,
the progress/QC source records agree byte-semantically, no endpoint-family key is
present, and `raw_result.json` does not exist. The prior-receipt guard therefore blocks
another HPC4 attempt.

The all-cell MIN20 aperture passed in 34 of 36 file/reference cells and failed in
exactly two:

| Protocol | Subject | Phase | Clinical clean | Bipolar clean | Failed aperture |
|---|---|---|---:|---:|---|
| TS | p17 | post | 11 | 25 | clinical |
| PB | p17 | pre | 22 | 11 | bipolar |

Independent post-run implementation audit found no P0, P1, or P2 receipt defect. The
mathematics audit confirmed that the frozen conjunction requires all 36 apertures, so
either failure entails the terminal QC stop. This is a measurement-aperture result,
not evidence for or against a neural effect. No endpoint, effect size, bootstrap,
leave-one-out result, paired sensitivity, memory result, consciousness claim, CE
claim, or AGI claim is authorized by this run.

Receipt SHA-256:

- `raw_progress.json`:
  `5b350ac0b568888ac6a8416f0084f04fad83242500ffbfd40451bb605e065e87`
- `qc_result.json`:
  `5f9ce77000613de4761d24519a6b7c1309fbea55d465739aafbc2a7189038e17`
