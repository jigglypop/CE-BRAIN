# Mathematics

Status: COMPLETE

## DIF.1 — exact invariant coordinate family

For a coordinate partition `I union O`, require every nominal and uncertainty
cross-block entry to be exactly zero.  Hence every family member has

```text
A = diag(A_I,A_O).
```

## DIF.2 — direct factor coefficient enclosure

For every admitted member,

```text
chi_A(z) = det(zI_I-A_I) det(zI_O-A_O).
```

Each block determinant is expanded by the Leibniz formula.  Exact rational
complex-rectangle addition, negation, and multiplication enclose every resulting
coefficient.  Both factors are monic.  The conservative work contract is

```text
|I|! + |O|! + n! <= maximum_determinant_terms.
```

## DIF.3 — spectral interpretation

If IVSPEC succeeds and its nominal exact projector is the declared coordinate
projector, then the factor degrees are `|I|` and `|O|` and equal the certified
family Riesz rank and complement rank.  No interval root tracking is required.
If that bridge fails, coefficient boxes may be emitted but no spectral
inside/outside certificate is issued.
