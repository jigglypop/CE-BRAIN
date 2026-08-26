# Mathematics

Status: COMPLETE

## PCA.1 — exact development covariance

Verify `sum_i x_i=0` coordinatewise, then compute

```text
C = (1/N) sum_i x_i x_i^T.
```

The centered label alone is insufficient.

## PCA.2 — exact eigenwitness

For a full rational basis, verify

```text
v_i^T v_j = delta_ij,
lambda_j = v_j^T C v_j,
C v_j = lambda_j v_j,
lambda_1 > ... > lambda_n >= 0.
```

Strict order makes every candidate prefix subspace unique and prevents a rank
boundary from slicing an unresolved degenerate eigenspace.

## PCA.3 — projector and execution

Construct `P_d=sum_(j<=d) v_j v_j^T`.  Orthonormality proves symmetry,
idempotence, and trace `d`.  Pass the complete prefix menu into DEXEC, which
recomputes held-out scores, moving-block winners, and DSTAB stability.
