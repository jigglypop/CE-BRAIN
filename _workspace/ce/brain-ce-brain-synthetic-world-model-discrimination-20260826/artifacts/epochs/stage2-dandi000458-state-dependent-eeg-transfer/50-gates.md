# Stage 2 gates

Status: COMPLETE / OUTCOME_BLIND

1. Frozen DANDI version, asset identity, byte size and SHA-256 match.
2. NWB signal shape, conversion, timestamps, trial columns and registered
   channel rows match the source receipt.
3. All trial eligibility and even/odd splits reproduce the locked counts.
4. Preprocessing returns exactly 249 samples by 17 channels per waveform.
5. Synthetic fixture tests cover artifact substitution, CAR, baseline,
   gain fitting, permutation determinism, decisions and mutation rejection.
6. Confirmation EEG values remain unopened until code, tests, contract and
   manifest are sealed.
7. One-shot execution writes an atomic result and refuses overwrite.
8. A separate `--verify-result` invocation reopens the raw file, verifies the
   manifest/schema/raw links, recomputes all waveforms, metrics, permutation
   counts and the decision, requires exact canonical result equality, and writes
   a one-shot validation receipt before any claim is reported.

Any failure is `STAGE2_APPARATUS_STOP`, not evidence for either scientific
alternative.
