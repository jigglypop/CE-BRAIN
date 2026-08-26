# Mathematics

Status: COMPLETE

## EO.1 — exact frozen ellipse split

Fix `p=(px,py) in Q^2`, `px^2+py^2=1`, and `p_perp=(-py,px)`.  For normalized
`lambda_j`, center `c`, and positive semiaxes `a,b`, put

```text
xi_j  = p dot (lambda_j-c)
eta_j = p_perp dot (lambda_j-c)
g_j   = a^2 b^2 - b^2 xi_j^2 - a^2 eta_j^2
q_j   = g_j for an inside label and -g_j for an outside label
Phi   = min_j q_j.
```

Dividing `g_j` by positive `a^2 b^2` proves that `g_j>0` is exactly the open
ellipse inequality.  Thus `Phi>0` excludes the boundary spectrum and realizes
all labels.  Exact `UV=V Lambda` then gives the Riesz projector
`P=V diag(labels) V^-1`, including oblique `V`.

## EO.2 — one-cell inclusion theorem

For a rational box `C=Ix x Iy x Ia x Ib`, affine interval evaluation encloses
`xi_j(C)` and `eta_j(C)`.  The sign-aware square map

```text
S([l,u]) = [0,max(l^2,u^2)] if 0 is in [l,u],
           [min(l^2,u^2),max(l^2,u^2)] otherwise
```

is exact.  Since `Ia,Ib` are positive, endpoint multiplication is exact for the
nonnegative factor ranges.  Consequently

```text
G_jC = S(Ia)S(Ib) - S(Ib)S(Xi_jC) - S(Ia)S(Eta_jC)
```

contains every `g_j(theta)`, `theta in C`.  Negating endpoints for outside
labels gives `Q_jC`, hence `sup_C Phi <= min_j upper(Q_jC)=U_C`.

## EO.3 — tolerance-global certificate

Let `L` be the best midpoint score and `U=max_C U_C`.  Inclusion proves
`L <= max_box Phi <= U`.  Repeated exact longest-axis bisection is accepted only
when `U-L<=eta4`; therefore the incumbent is `eta4`-globally optimal over all
four continuous variables.  Natural interval extensions of this finite
polynomial converge to the point value as all cell widths vanish.  A declared
finite budget may still refuse before the requested tolerance; refusal carries
no optimality claim.  Positivity, projector idempotence and commutation remain
separate mandatory gates.

## EO.4 — reduction and dimensions

For `a=b=r`, `g_j=r^2(r^2-|lambda_j-c|^2)`, so the sign reduces exactly to the
circle score.  All spectral inputs are divided by one positive reference scale;
the quartic score and tolerance are therefore dimensionless fourth powers.
