# Stage 1 Allen optimizer-only successor contract

Status: COMPLETE / OUTCOME_BLIND

## Predecessor and scope lock

The predecessor `stage1-allen-single-cell-local-dynamics` is preserved as
`STAGE1_APPARATUS_STOP:irls convergence` with manifest
`190f75971a6e7879e3f2d6825507950d018c954862257b88e0f938b4488a7169`.
It failed inside `_fit_models` after opening fit sweeps only. No Noise 1/Noise 2
value, model endpoint or result was opened.

This successor inherits every scientific byte represented by that manifest:
specimen, raw SHA, sweep split, SI conversion, downsampling, horizon, features,
thinning, ridge/logistic objective and penalty, metrics, 2% thresholds, decision
logic, claim ceiling and all stop rules. The predecessor manifest and its 11
bound files are hash-verified read-only before seal and execution.

The sole change is logistic optimizer globalization. This is an implementation
retry, not a new scientific hypothesis and not permission to inspect or tune on
Noise 1/Noise 2.

## Frozen Armijo Newton solver

For standardized design matrix `X` including an unpenalized intercept, slopes
`beta[1:]`, penalty `lambda=1e-4`, maximize

`Q(beta)=sum(y*eta-logaddexp(0,eta))-0.5*lambda*||beta[1:]||^2`,

where `eta=X beta`. At each iteration compute the same penalized Newton direction

`d=(X' W X + P)^(-1) [X'(y-p)-P beta]`.

Start `alpha=1` and halve until

`Q(beta+alpha*d) >= Q(beta) + 1e-4*alpha*g'd`.

Accept the first satisfying alpha. Before constructing a direction, and again
after every accepted step, converge only when `max(abs(g)) <= 1e-8`. A small
backtracked step is not itself convergence. Store its norm for audit, but if the
gradient remains above tolerance the solver continues. Maximum iterations remain
50. Intercept remains unpenalized; no feature, row, penalty, threshold or
endpoint changes.

Kill as `STAGE1_APPARATUS_STOP` if the nonconverged gradient has `g'd<=0`, the
solve is singular/nonfinite, no
finite accepted `alpha>=2^-40`, accepted objective decreases beyond `1e-10`, or
the gradient tolerance is not reached by iteration 50. Store per-model iteration
count, final objective, final gradient infinity norm, final step infinity norm
and minimum accepted alpha as fit receipts.

## Decision and claim ceiling

The inherited `STAGE1_HISTORY_SUPPORTED`, `STAGE1_MARKOV_SUFFICIENT`,
`STAGE1_HISTORY_TENSION` and `STAGE1_APPARATUS_STOP` rules are byte-equivalent.
Stage 2 remains unauthorized automatically. The maximum claim remains a
one-cell public-recording predictive comparison, never a causal, cell-type,
geometry, memory, consciousness or AGI result.
