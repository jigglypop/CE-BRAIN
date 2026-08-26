# Mathematics

Status: COMPLETE

## APREF.1 — frozen refinement rules

For initial positive integers `m_k(0)`, multiplier `a>=2`, and finite budget `B`,
the edge quadrature error is

```text
e_k(t) = c_k / m_k(t)^2,
c_k = (L_k+)^3 (R_k+)^3 / 12.
```

`UNIFORM` selects every edge.  `MAX_ERROR_TIES` selects every edge attaining the
exact maximum error.  Selected counts are multiplied by `a`; all others remain
unchanged.

## APREF.2 — finite correctness

Each round invokes the unchanged verified quadrature theorem.  The first singleton
possible-rank set is therefore the verified nominal rank and is inherited by the
certified interval family.  If no singleton appears through round `B`, the only
admitted result is explicit budget exhaustion with no rank.

## APREF.3 — conditional asymptotics

Uniform refinement multiplies every edge error by `a^-2`.  Maximum-error-tie
refinement cannot ignore an edge whose error remains bounded away from zero: once
it is maximal it is refined, so the global maximum tends to zero.  If the limiting
Machin rank intervals are separated around the true integer, the unlimited
conceptual sequence eventually isolates it.  The finite implementation never uses
this statement to exceed `B`.
