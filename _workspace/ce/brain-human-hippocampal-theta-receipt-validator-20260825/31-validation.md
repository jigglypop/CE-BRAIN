# BA-OBS-HPC4 validation

Status: COMPLETE

Source-only compile:

`.codex\\hooks\\python.cmd python -c "from pathlib import Path; compile(Path('examples/brain/ba_obs_hpc4_receipt_validator.py').read_text(encoding='utf-8'),'ba_obs_hpc4_receipt_validator.py','exec'); print('SOURCE_COMPILE_PASS')"`

Focused validation:

`.codex\\hooks\\python.cmd pytest tests\\test_ba_obs_hpc4_receipt_validator.py -q -p no:cacheprovider`

- PASS: `18 passed in 6.58s` (two expected SciPy precision-loss warnings from the
  deliberately constant, author-detectable QC-stop fixture).
- Replays CLI injection, malformed authority/progress, empty/extra receipts, strings,
  booleans, nulls, NaN, waveform/P2P/analysis finite tampering, p20 `3*151` valid and
  invalid reason caps, source/invariant/prior/truncated-loader stops,
  endpoint/aggregate failures, and authority writer pre/post-commit behavior. Includes
  deterministic HPC2 estimator recomputation and source-lock exact shape/mirror checks.
- These were preflight checks; no raw/network execution occurred during preflight.

## Actual one-shot execution

Exactly one authoritative command was executed:

`.codex\\hooks\\python.cmd python examples\\brain\\ba_obs_hpc4_receipt_validator.py raw-one-shot`

- Exit code: `0`
- Terminal output: `QC_STOP_MIN20`
- Attempt: `ATTEMPT1` (consumed; no rerun)
- Frozen source-lock SHA-256:
  `66cac4202971cabb0838b3ddb93710c160c88325133411f58c8595c89e7c5810`
- Source integrity: 18/18 exact SHA-256, size, version ID, and ETag matches
- Verified raw bytes: `723,560,000`
- Required file/reference apertures passing MIN20: 34/36
- Failing apertures: TS p17 post clinical `11` (bipolar `25`), and PB p17 pre
  bipolar `11` (clinical `22`)
- Terminal disposition:
  `QC_STOP_MIN20 / NO_RAW_RESULT / NO_ENDPOINT / NO_BIOLOGICAL_VERDICT / NO_RERUN`

`raw_progress.json` and `qc_result.json` agree on all 18 source/QC records. No waveform,
P2P, delta, bootstrap, LOO, paired-sensitivity, status-lattice, or other endpoint value
was committed, and `raw_result.json` is absent. The observed stop therefore verifies
the sealed transaction and QC behavior only; it is neither a positive nor a negative
biological result.

Artifact SHA-256:

- `raw_progress.json`:
  `5b350ac0b568888ac6a8416f0084f04fad83242500ffbfd40451bb605e065e87`
- `qc_result.json`:
  `5f9ce77000613de4761d24519a6b7c1309fbea55d465739aafbc2a7189038e17`
