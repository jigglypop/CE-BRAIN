# Stage 0 frozen models

Status: COMPLETE

The implementation must expose exactly five selectable classes:

1. `R`: symmetric linear transition and linear signed input;
2. `F`: unrestricted linear transition with separate positive/negative inputs;
3. `G`: unrestricted directed linear transition and linear signed input;
4. `O`: polynomial/history operator with two state lags, state squares and
   state-input interaction;
5. `S`: two linear regimes separated by zero or a fixed train quantile threshold
   on observed state 0.

All candidates share the same train-derived standardization and the frozen ridge
grid. Threshold candidates for S are train-state quantiles
`{0.25,0.35,0.50,0.65,0.75}`. R symmetrizes its fitted state block; it does not
inspect the true generator. Candidate APIs accept train and validation only
during selection and return an immutable serialized fit used once on unseen data.

The persistence baseline is never selectable. No neural-network optimizer,
manual per-world hyperparameter or post-result feature addition is allowed.
