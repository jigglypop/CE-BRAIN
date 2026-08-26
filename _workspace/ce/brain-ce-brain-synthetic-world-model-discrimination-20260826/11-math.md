# Mathematics lane

Status: COMPLETE

R, G and F are nested linear regressions with different structural constraints;
O adds fixed lag/polynomial features, while S partitions train rows using only an
observed-state threshold. Ridge solutions use
`(X^T X + lambda I)^{-1} X^T Y`, implemented with `solve` and `lstsq` fallback.
The intercept is exempt from ridge penalty.

The score is dimensionless because both RMSE terms are divided by target SD and
`k/n_scalar` is a pure count ratio. Stability and finite-rollout checks are
necessary because low one-step error alone does not imply an admissible dynamical
model. Complexity penalty can prefer R over its nested G representation in A,
but cannot by itself satisfy the held-out error or winner-frequency gates.

This benchmark establishes empirical finite-sample discrimination only. It is
not a theorem of global model identifiability.
