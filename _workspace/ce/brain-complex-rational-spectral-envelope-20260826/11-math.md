# Mathematics

Status: COMPLETE

## CX.1 — exact realification

For `U=A+iB` over `Q(i)`, define

```text
R(U) = [[A,-B],[B,A]] in Q^(2n x 2n).
```

This is the real-coordinate representation of the original complex-linear map.

## CX.2 — real characteristic envelope

If `chi_U` is the characteristic polynomial over `Q(i)`, then

```text
chi_R(U)(z) = chi_U(z) conjugate_coefficients(chi_U)(z) in Q[z].
```

Cayley--Hamilton gives `chi_U(U)=0`, hence the product also evaluates to zero on
the original `n x n` complex matrix.  Therefore complete irreducible Q factors of
the envelope form a valid annihilating factor family for the original matrix.

## CX.3 — arbitrary-center shift, label, and rank theorem

For arbitrary exact Gaussian-rational `c`, set `W=U-cI` and `z=c+w`.  Then
`|lambda-c|=|mu|` for `mu=lambda-c`, and
`(zI-U)^(-1)=(wI-W)^(-1)`.  The shifted circle has center zero, so conjugates
have equal modulus and an envelope factor joining them cannot force opposite
labels.  The factor-derived Bezout projector is evaluated on `W` and is exactly
the original `U` Riesz projector.  Its reported rank is

```text
d_C = trace_C(P) = rank_C(P),
rank_R(R(P)) = 2 d_C.
```

Only `d_C` is returned.  Envelope factors are centered-variable Q factors, not a
direct irreducible factor listing in Q(i)[z].
