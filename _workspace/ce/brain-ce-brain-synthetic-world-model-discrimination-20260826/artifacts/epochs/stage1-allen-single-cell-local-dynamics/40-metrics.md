# Stage 1 metrics

Status: COMPLETE / OUTCOME_BLIND

- Voltage RMSE (mV) and NRMSE (`RMSE / sd(V_target)`) per sweep.
- Relative voltage improvement: `(RMSE_M0-RMSE_M1)/RMSE_M0`.
- Persistence relative improvement for each fitted model.
- Spike-event Brier score per sweep and pooled by summing squared-error/count
  receipts, never by concatenating persisted raw samples.
- Relative Brier improvement: `(Brier_M0-Brier_M1)/Brier_M0`.

All denominators must be positive and finite. Uncertainty is descriptive across
the two fixed confirmation sweeps; no population generalization is claimed.
