# Mathematics

Status: COMPLETE

## QF.1 — canonical primitive lift

For nonconstant `f in Q[z]`, divide by its leading coefficient to obtain monic
`f_m`.  Clear the coefficient denominators, divide the integer content, and fix
positive leading sign to obtain primitive `F in Z[z]`.  Gauss' lemma makes
factorization of `f_m` over Q equivalent to primitive factorization of `F` over
Z, modulo nonzero rational units.

## QF.2 — complete finite factor search

If `F=GH`, select the smaller nonconstant factor, of degree
`1 <= m <= floor(deg(F)/2)`.  Choose distinct integers `a_0,...,a_m` with
`F(a_i) != 0`.  Since `G(a_i)` divides `F(a_i)`, its value vector belongs to

```text
D_0 x ... x D_m,
D_i = {signed integer divisors of F(a_i)}.
```

For each value tuple `y`, exact Lagrange interpolation gives

```text
G_y(z) = sum_i y_i product_(j != i) (z-a_j)/(a_i-a_j).
```

Only exact degree-`m`, integral-coefficient candidates survive; they are made
primitive and accepted only on zero exact polynomial-division remainder.  The
true primitive factor occurs in this finite enumeration.  Therefore exhaustion
for every `m <= floor(deg(F)/2)` proves irreducibility over Q.  A found factor and
its quotient are recursively subjected to the same proof.

## QF.3 — resource contract and primary reconstruction

The candidate space at degree `m` has exact size

```text
N_m = product_i |D_i|.
```

If the remaining predeclared budget cannot admit all `N_m` tuples, the run stops
before that search with no completeness claim.  On success, equal monic
irreducibles `h_j` are counted with multiplicity `mu_j`, primary atoms
`g_j=h_j^mu_j` are formed, and `product_j g_j == f_m` is checked coefficientwise.

This proves completeness for each successfully admitted supplied polynomial of
arbitrary finite degree.  It does not assert a uniform small runtime bound.
