# BA-OBS-HPC3 validation

Status: SKIPPED — adversarial audit retained P0/P1; no raw validation authorized

Source-only compile printed `SOURCE_COMPILE_PASS`.

`.codex\\hooks\\python.cmd python -c "from pathlib import Path; compile(Path('examples/brain/ba_obs_hpc3_author_qc_transaction.py').read_text(encoding='utf-8'),'ba_obs_hpc3_author_qc_transaction.py','exec'); print('SOURCE_COMPILE_PASS')"`

`.codex\\hooks\\python.cmd pytest tests\\test_ba_obs_hpc3_author_qc_transaction.py -q -p no:cacheprovider`

- PASS: `10 passed in 2.49s`.
- Covers executable default binding and injected no-network CLI; malformed JSON,
  forged raw/QC schemas, `files=[{}]*18`, empty analysis, extra waveform key and NaN
  count; source/invariant/endpoint/aggregate/serialization stops; writer pre/post
  commit ordering; prior receipts; frozen byte tampering; and version-pinned reader.
- No raw/network execution occurred.
