# Stage 1 optimizer route portfolio

Status: COMPLETE / OUTCOME_BLIND

Fit-only diagnosis used 147,192 registered thinned rows with 119 positive and
147,073 negative spike events. M0 converged in 12 iterations. M1 improved its
penalized log-likelihood through iteration 8, then an undamped full Newton step
reduced the objective and initiated numerical divergence. DEV and confirmation
were not opened.

Three distinct apparatus routes were considered before selection:

1. `armijo-monotone-newton` — same Newton direction and objective with frozen
   monotone backtracking. Minimal scientific/apparatus delta. **Selected.**
2. `trust-region-irls` — adaptive Levenberg--Marquardt diagonal damping and a
   registered trust-radius acceptance ratio. Not selected because it adds a
   second stateful tuning schedule.
3. `strong-wolfe-bfgs` — deterministic quasi-Newton optimization of the same
   penalized objective. Not selected because it changes both curvature
   approximation and line search.

Selected structural fingerprint:
`allen-stage1-same-objective-armijo-globalized-newton-v1`.

The first route is killed by solve/nonfinite failure, a non-ascent direction
when the gradient is above tolerance,
failure to accept `alpha>=2^-40`, objective decrease, or nonconvergence by 50.
Failure preserves the two alternatives for separately registered successors; it
does not permit changing the scientific endpoint.
