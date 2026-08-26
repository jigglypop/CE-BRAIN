# Mathematics

Status: COMPLETE

## IVS.1 — rectangular family radius

For normalized perturbations with component bounds `a_ij,b_ij`, exact dyadic
enclosure supplies

```text
||E||_2 <= ||E||_F <= eps_plus,
eps_plus^2 >= sum_ij (a_ij^2+b_ij^2).
```

## IVS.2 — uniform no-crossing homotopy

If the nominal full-circle certificate proves
`sigma_min(zI-U0) >= delta0` on all contour points and `eps_plus < delta0`, then
for every allowed `E`, every `t in [0,1]`, and every contour point,

```text
sigma_min(zI-(U0+tE)) >= delta0-t||E||_2
                         >= delta0-eps_plus > 0.
```

The entire family path is contour-free.

## IVS.3 — rank and projector conclusion

Riesz rank is constant along the path, so every family member has the exact
automatically discovered nominal rank `d0`.  The resolvent identity gives

```text
||P(U0+E)-P(U0)||_2
 <= r eps_plus / (delta0 (delta0-eps_plus)).
```

No interval characteristic polynomial factorization or root matching is needed.
