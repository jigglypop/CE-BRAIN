# Mathematics

Status: COMPLETE

## DX.1 — exact held-out score

For every session and frozen candidate rank, require

```text
P_d^T=P_d,  P_d^2=P_d,  trace(P_d)=d.
```

For held-out window `W`, compute

```text
score_W(d) = -mean_(x in W) ||(I-P_d)x||_2^2 - lambda*d
```

with exact rationals and frozen `lambda>=0`.  Only a unique maximizer is accepted.
The aggregate conscious winner must equal the base complete-menu selected rank.

## DX.2 — moving-block execution

Require block length `L` to divide window count `T`.  Every resample row has length
`T`, and each length-`L` chunk is cyclic consecutive.  Reaverage the stored raw
window scores for every candidate and accept only a unique bootstrap winner.

## DX.3 — stability composition

The generated conscious/control window ranks and bootstrap winners are passed to
DSTAB.  Thus transition, dwell, control, and bootstrap gates are functions of the
supplied observation vectors and verified projectors, not caller rank summaries.
