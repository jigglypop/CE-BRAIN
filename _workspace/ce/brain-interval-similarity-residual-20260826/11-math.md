# Mathematics

Status: COMPLETE

## ISR.1 — uniform invertibility

Let `T=T0+E`, with exact invertible `T0` and `|E|<=E+`.  Put

```text
Q = |T0^-1| E+,       theta = ||Q||_infinity.
```

Because `T=T0(I+H)` for `H=T0^-1 E` and `|H|<=Q`, `theta<1` implies

```text
|T^-1| <= K := (I-Q)^-1 |T0^-1|,
|T|    <= T+ := |T0|+E+.
```

The inverse `(I-Q)^-1=sum Q^m` is componentwise nonnegative.  Equality
`theta=1` is not admitted.

## ISR.2 — transformed family enclosure

For normalized `A=A0+D`, `|D|<=D+`, define `S=T^-1AT` and
`S0=T0^-1A0T0`.  The exact identity

```text
S-S0 = T^-1 D(T0+E) + T^-1 A0 E - T^-1 E T0^-1 A0 T0
```

gives

```text
D_S+ = K D+ T+ + K |A0| E+ + K E+ |T0^-1| |A0| |T0|.
```

The last two terms are mandatory; the fixed-transform box alone is unsound when
the coordinate map varies.

## ISR.3 — return to the original norm

Define outward bounds

```text
tau+   = sqrt(||T+||_1 ||T+||_infinity),
iota+  = sqrt(||K||_1 ||K||_infinity),
kappa+ = tau+ iota+.
```

Then `kappa_2(T)<=kappa+` uniformly.  If the transformed residual gate gives node
lower `ell'_k`, the original node lower is `ell_k=ell'_k/kappa+`.  Thus

```text
delta = min_k ell_k - chord+ > 0
```

certifies the entire original contour and common Riesz rank for every admitted
pair `(A,T)`.
