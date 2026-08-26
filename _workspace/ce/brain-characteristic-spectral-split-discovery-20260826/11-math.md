# Mathematics

Status: COMPLETE

## CHSPEC.1 — exact characteristic polynomial

Starting with `B0=I`, compute

```text
c_k=-(1/k)tr(U B_{k-1}),
B_k=U B_{k-1}+c_k I.
```

Then `chi_U(z)=z^n+c_1z^(n-1)+...+c_n`.  Exact evaluation `chi_U(U)=0`
is a mandatory Cayley--Hamilton self-check.

## CHSPEC.2 — complete budget-admitted exact factor discovery

Clear coefficient denominators and primitive content.  Rational roots remain
diagnostic receipts.  CE-QFACT enumerates signed divisor values at `m+1` integer
points, exactly interpolates every possible primitive degree-`m` factor for
`1 <= m <= floor(n/2)`, and recursively certifies factors and quotients.  Search
exhaustion proves irreducibility; budget exhaustion proves nothing and stops.
Equal irreducibles are grouped into primary powers and exactly reconstruct the
characteristic polynomial.

For Gaussian-rational `U=A+iB` and arbitrary exact center `c`, first set
`W=U-cI`, then compute realification `[[Re W,-Im W],[Im W,Re W]]`.  Its
characteristic polynomial is
`chi_U conjugate(chi_U) in Q[z]` and annihilates original `U`.  Complete Q factors
therefore feed the unchanged original-matrix projector gate.  Reported rank is
complex rank on `U`, not doubled realification rank.  Resolvent translation makes
the zero-center `W` projector exactly the center-`c` projector of `U`.

## CHSPEC.3 — unique strict partition classification

Enumerate every subset of certified atoms within an explicit partition budget.
For empty/full subsets use an automatically chosen linear factor coprime to the
characteristic polynomial.  Each partition must pass exact Bézout P/R
construction and both strict algebraic norm gates.  Exactly one passing partition
yields the discovered projector/rank; zero, multiple, equality, or budget
exhaustion yields no selection.
