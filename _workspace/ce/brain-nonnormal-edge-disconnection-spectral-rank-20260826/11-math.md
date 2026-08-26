# Mathematics

Status: COMPLETE

## NDISC.1 — directed topology/operator model

Let `U0=S Lambda S^-1`, where `S` is an invertible real matrix and `Lambda` is
real diagonal. Let `U(k)=U0+kE`, `0<=k<=kmax`. The nonzero entries of directed
`E` must equal the directed graph edges added between the disconnected and maximum
adjacency masks. Graph component count and spectral rank are distinct outputs.

## NDISC.2 — conditioned circle-resolvent theorem

For the circle `Gamma={z:|z-c|=r}`, define

`delta_Gamma=min_i ||lambda_i-c|-r| > 0`

and supply `kappa_F^+ >= ||S||_F ||S^-1||_F`. Then, for every `z` on `Gamma`,

`||(zI-U0)^-1||_2 <= R0^+ := kappa_F^+/delta_Gamma`.

Proof: `(zI-U0)^-1=S(zI-Lambda)^-1S^-1`; apply submultiplicativity,
`||.||_2<=||.||_F`, and the exact diagonal resolvent distance. This is conservative
but valid and exposes the nonnormal eigenvector-conditioning penalty.

## NDISC.3 — Neumann rank and projector theorem

Supply `epsilon^+ >= kmax||E||_F` and set `rho=R0^+ epsilon^+`. If `rho<1`,

`zI-U(k)=(zI-U0)[I-k(zI-U0)^-1E]`

is invertible for every `z` on `Gamma` and every `k` in the homotopy. Hence the
Riesz projector is continuous and its integer rank is constant. Moreover,

`sup_Gamma ||(zI-U(k))^-1|| <= R0^+/(1-rho)`

and the endpoint resolvent identity gives

`||P(kmax)-P(0)|| <= r (R0^+)^2 epsilon^+/(1-rho)`.

## NDISC.4 — eigenvalue-only certification counterexample

Take `S=[[1,20],[0,1]]`, `Lambda=diag(0,3)`, `c=0`, `r=1`, and
`E_12=1/100`. The circle gap is one and the directed coupling norm is `1/100`, but
`||S||_F||S^-1||_F=402`, so `rho=201/50>1`. This does not prove a crossing. It
proves that the candidate certificate using only eigenvalue distance and small edge
strength omits a necessary nonnormal-conditioning control.

The stable seven-dimensional fixture instead has gap `1/4`, condition product `8`,
`R0^+=32`, coupling bound `1/100`, and `rho=8/25<1`; its circle rank remains six.
