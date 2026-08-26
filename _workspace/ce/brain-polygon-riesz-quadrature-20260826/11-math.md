# Mathematics

Status: COMPLETE

## PQUAD.1 — midpoint remainder

For positive polygon orientation define

```text
K = -i integral_Gamma (zI-A0)^-1 dz = 2*pi*P_Gamma(A0).
```

On edge `h_k=v_(k+1)-v_k`, use `m_k` frozen midpoint panels.  The exact Q(i)
sum is `K_m`.  Since the second derivative of `-i h_k R(v_k+t h_k)` is bounded
by `2 |h_k|^3 ||R||^3`,

```text
||K-K_m||_2 <= E_K+ = sum_k (L_k+)^3 (R_k+)^3 / (12 m_k^2).
```

## PQUAD.2 — exact pi interval

Use

```text
pi/4 = 4 atan(1/5) - atan(1/239)
```

and two consecutive alternating partial sums for each arctangent.  Correct
lower/upper propagation gives exact rationals `pi-<pi<pi+`, self-checked by
`3<pi-<pi+<22/7`.

## PQUAD.3 — rank extraction

If the true nominal rank is `r`, then

```text
|trace(K_m)-2*pi*r| <= n E_K+.
```

For each integer `q` in `[0,n]`, compute the exact squared distance from the
complex `trace(K_m)` to `[2*pi-*q,2*pi+*q]`.  The true rank cannot be excluded.
If exactly one integer remains, it is the verified nominal rank; the predecessor
polygon homotopy transfers it to every matrix in the certified interval family.

## PQUAD.4 — scaled projector

Let `s-=(2*pi+)^-1`, `s+=(2*pi-)^-1`, and `sbar=(s-+s+)/2`.  For outward
`||K_m||_2<=M_K+`,

```text
||P-sbar K_m||_2 <= s+ E_K+ + (s+-s-) M_K+ / 2.
```
