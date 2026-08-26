# Mathematics

Status: COMPLETE

## PRAD.1 — positivity and smooth Jordan geometry

Let

```text
rho(u)=r0+p.u+sum_{|alpha|>=2} a_alpha u^alpha
```

be a finite rational polynomial.  Set

```text
A0=sum_{|alpha|>=2}|a_alpha|.
```

An outward `p*+>=||p||_2` and strict `r0-p*+-A0>0` make `rho` positive on the
closed unit disk.  Positive polar radius gives injectivity on the circle, while
`d(rho u)/dtheta=rho' u+rho u_perp` is nonzero.  An orientation-preserving
invertible affine map retains a regular positive Jordan contour.

## PRAD.2 — coefficient-sum Lipschitz cover

For higher terms define

```text
A1=sum |a_alpha| |alpha|.
```

On the unit disk, `|rho|<=r0+p*++A0` and `||grad rho||<=p*++A1`.  Hence

```text
C_poly+=r0+2p*++A0+A1
```

bounds `||D(rho(u)u)||_2`.  The affine rational-mesh cover is
`S_L+ C_poly+ h_max+`.  When higher coefficients vanish, this equals the
degree-one radial bound exactly.

## PRAD.3 — residual, family rank, and projector perturbation

If

```text
delta_poly=min_k ell_k-S_L+ C_poly+ h_max+ > 0,
```

the whole smooth contour is in the common interval-family resolvent set and its
Riesz rank is preserved.  Its length is at most `2*pi*S_L+*C_poly+`, giving

```text
||P(A)-P(A0)||_2 <= S_L+ C_poly+ D2+ (1/delta_poly)^2.
```

## PRAD.4 — polygon numeric rank transfer

The sector proof requires only positivity and a disk Lipschitz constant, not the
degree of `rho`.  Thus the radial arc-to-chord homotopy remains inside the same
cover.  A unique adaptive polygon rank and its projector approximation/error
transfer unchanged to the polynomial radial contour.  Exhaustion emits neither.
