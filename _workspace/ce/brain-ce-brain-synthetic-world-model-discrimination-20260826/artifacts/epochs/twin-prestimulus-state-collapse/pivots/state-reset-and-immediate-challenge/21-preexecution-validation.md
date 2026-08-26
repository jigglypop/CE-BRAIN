# State-reset immediate-challenge pre-execution validation

Status: COMPLETE

Gate: PASS

Focused command:

```powershell
.codex\hooks\python.cmd pytest _workspace\ce\brain-ce-brain-synthetic-world-model-discrimination-20260826\artifacts\epochs\twin-prestimulus-state-collapse\pivots\state-reset-and-immediate-challenge\test_state_reset_confirmation.py -q
```

Stable-snapshot result: `7 passed in 0.26s` (independent math recheck:
`7 passed in 0.27s`).

The suite is mechanical-only. It uses fixtures and a temporary preregistration
directory; it does not construct or score the fresh confirmation population and
does not seal the real pivot. Covered behavior includes:

1. root-label digest and little-endian seed identity;
2. paired-Hadamard construction, RMS and train/validation row counts;
3. immediate opposite pulses and exact two-sample arm reset;
4. descriptor-before-confirmation rejection;
5. unique CRN/arm receipts and split-arm overlap rejection;
6. result-row descriptor serialization and candidate binding;
7. exact assignment-formula and main-reset receipt corruption rejection;
8. missing real manifest rejection;
9. temporary manifest seal/verify, exact prereg population and mutation rejection.

No actual pivot manifest or result existed when this document was written.
