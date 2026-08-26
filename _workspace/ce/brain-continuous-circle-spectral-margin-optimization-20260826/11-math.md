# Mathematics

Status: COMPLETE

## CO.1 — frozen continuous objective

For target labels `inside_j`, define on normalized `theta=(x,y,r)`

```text
q_j(theta) = r^2-|lambda_j-(x+iy)|^2       if inside_j,
             |lambda_j-(x+iy)|^2-r^2       otherwise,
Phi(theta) = min_j q_j(theta).
```

Positive `Phi` is exactly the strict target split.

## CO.2 — one-cell global upper

At a cell midpoint with half-widths `hx,hy,hr`, define maximum coordinate
distances `Dx_j,Dy_j,R`.  The mean-value theorem gives

```text
|q_j(theta)-q_j(mid)| <= 2 Dx_j hx + 2 Dy_j hy + 2 R hr = V_j.
```

Thus every real point in the cell satisfies
`Phi(theta) <= min_j(q_j(mid)+V_j) = U_cell`.

## CO.3 — tolerance-global certificate

Let `L` be the best evaluated midpoint score and `U=max U_cell` over the current
partition.  Then `L <= max_box Phi <= U`.  Longest-axis exact bisection continues
until `U-L <= eta`.  The incumbent is therefore eta-globally optimal over the
entire continuous box.  A cell-budget stop yields no claim.  Positive margin and
the downstream exact projector/rank gate are separately mandatory.
