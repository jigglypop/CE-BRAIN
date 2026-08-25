# Revision 1 — attempt 0 implementation invalidation

Status: COMPLETE

- Date: 2026-08-25 Asia/Seoul.
- Exact command: `.codex\hooks\python.cmd python examples\brain\ba_obs_hpc1_raw_replication.py raw-one-shot`.
- Execution receipt: escalated public-network launch yielded cell ID 30, then no stdout,
  traceback, exit code, session ID, result receipt, progress receipt, or raw file.
- Process receipt: the two child Python processes started at 19:41:57 (PIDs 984 and
  24580) remained alive after the execution interface returned. They were re-identified
  by exact launch time and terminated; a subsequent query found neither process.
- Static defect: amplitude, kurtosis, and sample-wise trial z-score decisions were made
  before the frozen baseline correction, contrary to `00-contract.md` §5.
- Outcome aperture: no endpoint, waveform, effect size, status, Nature Source Data, or
  biological verdict was serialized or inspected. No `.eeg` object or voltage dump was
  written to the repository or temporary storage.
- Formal disposition: `ATTEMPT0_IMPLEMENTATION_INVALID_NO_RESULT`. It is neither a
  positive nor a negative empirical result.
- Allowed repair: restore the already frozen preprocessing order, add atomic non-voltage
  raw-integrity progress/STOP receipts, serialize already frozen LOO/status outputs, and
  strengthen focused fixtures. No scientific choice may change.
- Retry budget: one audited attempt 1 only. A further failure closes this version as
  BLOCKED.
