# Mathematics lane

Status: COMPLETE

## NAN.1 Inverse Bell recurrence

Let `psi=phi^-1`, `I1=mu`, and let `Phi_k` bound `D^k phi`. For `n>=2`,
differentiate `phi compose psi=Id` and isolate the singleton partition carrying
`Dphi D^npsi`. With the partition notation of the affine hierarchy,

$$
I_n=\mu\sum_{m\in\mathfrak P_n\setminus\{e_n\}}
C_n(m)\Phi_{|m|}\prod_{j=1}^{n-1}I_j^{m_j}.
$$

This is a norm upper bound in Banach spaces and an exact scalar coefficient
recurrence. Its first levels are

$$I_2=\Phi_2\mu^3,$$

$$I_3=\Phi_3\mu^4+3\Phi_2^2\mu^5,$$

$$I_4=\Phi_4\mu^5+10\Phi_2\Phi_3\mu^6+15\Phi_2^3\mu^7.$$

The supplied forward bounds must reproduce the frozen predecessor I1..I4;
otherwise the extension fails closed instead of mixing incompatible envelopes.

## NAN.2 Raw graph map and second Bell composition

Let `A_b` be the affine raw derivative bound of `S_h=B h+g compose (I,h)` at
order `b`; `A_1=q*kappa+L_x`, and for `b>=2` it is the affine partition sum
before multiplying by `mu^b`. Let `Delta A_b` denote its full graph-difference
coefficient vector, with the anisotropic order-one value coefficient
`H_x+H_y*kappa`.

The common inverse is identical for both graphs. Hence

$$
\Lambda_{n,\mathrm{out}}^{\rm na}
=\sum_{m\in\mathfrak P_n}C_n(m)A_{|m|}
\prod_{j=1}^nI_j^{m_j},
$$

and the complete recurrence vector is

$$
\Delta_n'\preceq
\sum_{m\in\mathfrak P_n}C_n(m)
\left(\prod_jI_j^{m_j}\right)\Delta A_{|m|}.
$$

No inverse-difference vector appears because the inverse is graph-independent.
The diagonal remains `q*mu^n`; all lower coefficients contain the exact
inverse-curvature transports.

## NAN.3 Reductions and finite-order boundary

At n=4 the two Bell recurrences reproduce the explicit nonaffine C4 class and
all five recurrence coefficients exactly. When every `Phi_k=0` and `mu=1`,
`I_k=0` for k>=2, so every level reduces exactly to the affine Bell hierarchy.
The K(n+1) modulus still changes only the value coefficient at level n.

The affine zero-curvature subfamily supplies the complete equality
counterexample `c*max(x,0)^n`; therefore no theorem over the larger nonaffine
class can replace strict `q*mu^n<1` by equality.

For the frozen curved fixture,

`I5=488600/129140163`, `I6=3797600/1162261467`,

`Lambda5_out=116441578775/43046721`, and
`Lambda6_out=75171452147900/387420489`.

The result covers every explicit finite n, not C-infinity or a uniform growth
class, and it preserves rather than selects dimension.
