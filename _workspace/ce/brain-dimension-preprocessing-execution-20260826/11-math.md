# Mathematics

Status: COMPLETE

## PRE.1 — development-only transform

For session development values and frozen positive scales,

```text
mu_j = mean_i x_dev[i,j],
x_tilde[i,j] = (x[i,j]-mu_j)/a_j.
```

Apply the same `mu_j,a_j` to development, conscious held-out, and matched-control
held-out observations.  Exact arithmetic gives zero normalized development sums.

## PRE.2 — leakage and scale covariance

No held-out mean or scale is computed.  Therefore a held-out constant shift is
preserved and may falsify the downstream rank gates.  Multiplying every raw
deviation and its reference scale by the same positive factor leaves all
normalized vectors and downstream receipts invariant.

## PRE.3 — composition

The normalized development observations enter DPCA; normalized held-out windows
enter DEXEC.  The nested chain reconstructs projectors, scores, moving-block
winners, transitions, dwell, control separation, and bootstrap stability.
