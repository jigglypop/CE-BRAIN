# Mathematics

Status: COMPLETE

## PSPEC.1 — Bézout projector

Let monic coprime exact factors satisfy

```text
f_in(U) f_out(U)=0,
a f_in + b f_out = 1.
```

Then

```text
P=b(U)f_out(U)
```

is identity on the `f_in` primary component and zero on the `f_out` component.
The product annihilation and coprimality give their direct sum, hence `P^2=P` and
`PU=UP`.  No eigenvector basis or diagonalization is used.

## PSPEC.2 — automatic exterior inverse

Let `Q=I-P`, `C=U-cI`, and

```text
B=P+QCQ.
```

If exact inversion of `B` succeeds, then

```text
R=QB^{-1}Q
```

has complement support and satisfies `RCQ=CR=Q`.  If the complement contains the
center eigenvalue, `B` is singular and construction fails closed.

## PSPEC.3 — final Riesz gate

The constructed `P,R` are passed unchanged to the existing algebraic theorem.
Strict inside `||(U-cI)P||_2<r` and outside `r||R||_2<1` gates are still mandatory.
Only after they pass is `P` the exact circular Riesz projector and `tr(P)` its
rank.
