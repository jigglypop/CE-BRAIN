# Stage 1 registered models

Status: COMPLETE / OUTCOME_BLIND

1. Persistence: `V_hat(t+1 ms)=V(t)`.
2. M0 Markov: ridge/logistic predictions from `V_t,I_t`.
3. M1 History: M0 plus 1/5/20 ms voltage/current lags and 2/10/50 ms observed
   spike-history counts.

All standardization and parameters use fit sweeps only. There is no per-sweep or
confirmation refit. Both fitted models see identical scored rows in each sweep.
