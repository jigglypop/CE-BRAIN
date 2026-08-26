# Mathematics

Status: COMPLETE

## IDISC.1 — uncertainty family

Let `||Delta U||<=eta_U^+`, `kmax||E||<=epsilon_E^+`, and
`kmax||Delta E||<=eta_E^+`. Entrywise nonnegative radius matrices are normalized by
the spectral scale and exact squared Frobenius sums must be enclosed. Coupling
uncertainty support may occur only on the declared added directed edges.

## IDISC.2 — uniform rank theorem

For `U=U0+Delta U+k(E+Delta E)`, the triangle inequality gives total perturbation

`epsilon_tot^+=eta_U^+ + epsilon_E^+ + eta_E^+`.

If the algebraic base circle resolvent is bounded by `R_alg^+` and
`rho_int=R_alg^+ epsilon_tot^+<1`, every member of the full uncertainty/homotopy
family avoids the circle and has the base Riesz rank.

## IDISC.3 — projector bound

Every family projector satisfies

`||P-P0|| <= r (R_alg^+)^2 epsilon_tot^+/(1-rho_int)`.

The fixture has `epsilon_tot=17/1000`, `rho_int=51/2000`, rank six, and projector
bound `153/1949`.

## IDISC.4 — strict boundary

Equality `rho_int=1` fails closed. Zero uncertainty reduces exactly to DDISC.
Deterministic box coverage is not statistical confidence coverage.
