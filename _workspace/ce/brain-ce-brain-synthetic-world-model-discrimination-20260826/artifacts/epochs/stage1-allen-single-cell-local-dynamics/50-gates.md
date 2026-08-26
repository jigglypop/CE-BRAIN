# Stage 1 gates

Status: COMPLETE / OUTCOME_BLIND

1. Official specimen/ephys/file identities and byte hash recorded.
2. Sampling rate, units, sweep identities, lengths and split membership exact.
3. Fit-only standardization/parameters; no confirmation-driven selection.
4. Mechanical fixture and one real-data schema smoke pass.
5. Every Noise sweep has at least 100,000 valid scored 10 kHz bins.
6. All predictions, probabilities and metrics finite; probabilities in `[0,1]`.
7. Frozen decision logic in `00-contract.md` is applied without retuning.

Any gate failure produces `STAGE1_APPARATUS_STOP` and no biological disposition.
