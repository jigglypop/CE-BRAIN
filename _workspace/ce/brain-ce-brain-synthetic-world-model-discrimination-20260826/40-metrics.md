# Stage 0 metrics

Status: COMPLETE

For each trajectory, predictions begin from the two observed initial states.
One-step prediction receives true lagged states; rollout feeds predictions back.

`NRMSE = sqrt(mean((prediction-target)^2)) / std(target)`.

Validation selection score is
`0.5*NRMSE_one_step + 0.5*NRMSE_rollout + 2*k/n_scalar`.
The unseen composite is the same average without a complexity penalty. Winner
margin is runner-up validation score minus winner score. Persistence improvement
is `1 - selected_unseen/persistence_unseen`.

Metrics are pooled over all trajectories, times and observed nodes within a
split. Train fit, validation fit and unseen fit are reported separately.
Nonfinite or divergent absolute state above `1e6` is infinite error.

The permutation diagnostic intentionally uses fixed fitted one-step predictions:
validation target trajectories are permuted as whole rows, one-step NRMSE plus
the same parameter penalty is recomputed, and no candidate is refit or selected.
It is not substituted for the composite validation score.
