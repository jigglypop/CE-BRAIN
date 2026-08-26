# Mathematics

Status: COMPLETE

## MKRES.1 — affine distance lower bound

Let `f_L^2=||L||_F^2`, `d_L=det L>0`, and
`s_L^-=d_L^2/f_L^2`. Since `sigma_max(L)^2<=f_L^2` and the product of the two
squared singular values is `d_L^2`, `s_L^-<=sigma_min(L)^2`.

For CE-MKSPEC signed squared margin `m_j`, set `b_j=rho^-` for an inside label
and `b_j=rho^+` for an outside label. Reverse triangle and
`(r_j+b_j)^2<=2(r_j^2+b_j^2)` give

```text
d_j^2=m_j^2/[2(r_j^2+b_j^2)]
 <= inf_{kappa,u}|rho_kappa(u)u-L^-1(lambda_j-c)|^2.
```

Therefore `delta_*^2=s_L^- min_j d_j^2>0` is a uniform normalized physical
contour-to-spectrum distance-squared lower bound.

## MKRES.2 — conditioned nonnormal resolvent upper bound

For exact `U~=V Lambda V^-1`, every admitted contour point satisfies

```text
||(zI-U~)^-1||_2^2
 <= ||V||_2^2 ||V^-1||_2^2 / delta_*^2
 <= ||V||_F^2 ||V^-1||_F^2 / delta_*^2.
```

All terms on the right are exact rationals. A self-checked outward dyadic square
root gives a rational norm upper bound. Omitting the eigenvector factor is
invalid for nonnormal matrices.

## MKRES.3 — dimensions and ceiling

All inputs are normalized by the common spectral reference scale. Squared
radii, affine singular-value and distance bounds, Frobenius conditioning, and
the normalized resolvent bound are dimensionless. The theorem covers the exact
nominal diagonalizable matrix only; interval perturbations and defective inputs
need separate gates.
