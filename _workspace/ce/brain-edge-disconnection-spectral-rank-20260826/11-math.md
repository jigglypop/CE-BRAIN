# Mathematics

Status: COMPLETE

## DISC.1 — coupled topology/operator model

In the disconnected eigenbasis let `U(k)=Lambda+kE`, `0<=k<=kmax`, where `E` is
real symmetric, has zero diagonal, and its nonzero pairs equal the removed graph
edges. A fixed spectral window is `(-r,r)`.

## DISC.2 — sufficient uniform no-crossing theorem

Let `delta0=min_i ||lambda_i|-r|` and
`epsilon_F^2=kmax^2 sum_ij E_ij^2`. If `epsilon_F^2<delta0^2`, then

`dist_H(sigma(U(k)),sigma(U(0))) <= k||E||_2 <= kmax||E||_F < delta0`.

No eigenvalue reaches either fixed boundary, so the window rank is constant for the
entire homotopy.

## DISC.3 — necessary crossing theorem

Ordered Hermitian eigenvalues vary continuously with `k`. If the exact endpoint
counts inside `(-r,r)` differ and neither endpoint lies on the boundary, at least one
intermediate eigenvalue equals `-r` or `r`. The endpoint witness proves existence,
not the crossing location, number, uniqueness, or direction.

## DISC.4 — independence counterexample

The seven-node fixture increases graph components from six to seven while its fixed
window rank remains six under a strict gap margin `697/625`. Thus topological
disconnection does not by itself force dynamical spectral-rank change.
