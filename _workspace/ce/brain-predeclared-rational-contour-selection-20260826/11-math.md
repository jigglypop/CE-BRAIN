# Mathematics

Status: COMPLETE

## CSEL.1 — frozen canonical menu

At least two exact normalized candidate contours, their IDs, patches, knots,
junction order, and rational mesh are sorted and hashed.  Exact duplicate
specifications and any mutated/forged menu are rejected.

## CSEL.2 — development-only strict selection

Candidate `j` is eligible only if its complete residual, homotopy, adaptive
numeric-rank, and projector gates pass.  Its score is

```text
s_j=delta_j^dev>0.
```

Require a unique winner and runner-up and a preregistered strict separation

```text
s_* - s_(2) > eta >= 0.
```

No ID-order tie break or equality promotion is allowed.

## CSEL.3 — selected-only heldout confirmation

Evaluate exactly the development winner on heldout.  Require its positive
heldout residual/rank certificate and

```text
d_*^heldout=d_*^development.
```

Heldout alternatives are never evaluated.  A certified contour with changed rank
is a failed confirmation because it isolates a different spectral bundle.
