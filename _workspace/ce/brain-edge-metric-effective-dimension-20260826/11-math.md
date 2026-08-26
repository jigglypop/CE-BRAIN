# Mathematics

Status: COMPLETE

## EDIM.1 — adopted observed fluctuation candidate

For `A(b)=A0+sum_e b_e H_e`, with `A0>0`, `H_e>=0`, and fixed finite observation
map `M`, define `G(b)=M A(b)^-1 M^T` and
`d_lambda(b)=tr(G(b)(G(b)+lambda I)^-1)` for `lambda>0`.

## EDIM.2 — monotonicity and derivative theorem

If `b+ >= b-` coordinatewise, then

`A+ >= A-`, `A+^-1 <= A-^-1`, and `G+ <= G-`.

Since `f_lambda(X)=I-lambda(X+lambda I)^-1` is operator-monotone increasing,

`0 <= d(b-)-d(b+) <= tr(G--G+)/lambda`.

For one continuously strengthened edge,

`partial d/partial b_e = -lambda ||H_e^(1/2) A^-1 M^T (G+lambda I)^-1||_HS^2 <= 0`.

## EDIM.3 — exact robust 4--6 endpoint gate

Monotonicity gives `d(b+) <= d(b) <= d(b-)` throughout the edge box. Hence every
admitted weight has ridge dimension in `[4,6]` iff
`4 <= d(b+)` and `d(b-) <= 6`.

## EDIM.4 — non-transfer boundaries

`G=(M A^-1/2)(M A^-1/2)^T` implies `rank(G)=rank(M)`, so positive metric
reweighting does not select a new hard rank. Participation ratio is nonmonotone:
the exact examples `diag(10,1)->I` and `I->diag(1/10,1)` respectively increase
and decrease it between `121/101` and `2`.
