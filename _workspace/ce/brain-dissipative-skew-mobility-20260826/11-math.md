# Mathematics lane

Status: COMPLETE

## DSK.1 Mixed-unit normalization and unique split

With `x=S_x x_tilde`, `V=V0 V_tilde`, and `t=t0 tau`, define

$$
\widetilde M=V_0t_0S_x^{-1}M_{\rm phys}S_x^{-T}.
$$

Then

$$
\widetilde M=S+K,
\qquad
S={\widetilde M+\widetilde M^T\over2},
\qquad
K={\widetilde M-\widetilde M^T\over2}.
$$

The split is unique because any symmetric/skew decomposition has these same
sum and difference formulas.  Diagonal congruence commutes with transposition
in this mixed-unit normalization, so the split is dimensionally valid.

## DSK.2 Potential balance with directional drift and forcing

For dimensionless gradient `g` and external dimensionless forcing `u`, use

$$
{d\widetilde x\over d\tau}=-(S+K)g+u.
$$

Since `K^T=-K`, exact real bilinearity gives

$$
g^TKg=(g^TKg)^T=g^TK^Tg=-g^TKg,
$$

hence `g^T K g=0`.  Therefore

$$
\boxed{
{d\widetilde{\mathcal V}\over d\tau}
=-g^TSg+g^Tu
}
$$

and the net dissipation margin is `g^T S g-g^T u`.  A skew component can
rotate/transport the state without direct model-potential work.  Forcing can
overcome symmetric dissipation and must not be hidden inside `K`.

## DSK.3 Coercivity and PL rate

If

$$
S\succeq mI,qquad m>0,
$$

and the model potential satisfies the supplied Polyak--Lojasiewicz inequality

$$
{1\over2}\|g\|^2\ge
\lambda(\widetilde{\mathcal V}-\widetilde{\mathcal V}_*),
\qquad\lambda>0,
$$

then for `u=0`,

$$
{d\over d\tau}(\widetilde{\mathcal V}-\widetilde{\mathcal V}_*)
\le-2m\lambda
(\widetilde{\mathcal V}-\widetilde{\mathcal V}_*).
$$

Thus

$$
\boxed{
\widetilde{\mathcal V}(\tau)-\widetilde{\mathcal V}_*
\le e^{-2m\lambda\tau}
[\widetilde{\mathcal V}(0)-\widetilde{\mathcal V}_*]
}
$$

and the physical rate is `2m lambda/t0`.  The exact apparatus verifies
`S-mI` by all principal minors.  It records the PL constant as a supplied
hypothesis; pointwise matrix algebra cannot establish the functional
inequality.

## DSK.4 Hilbert/form-level extension

Let `H` be a real Hilbert space and `V` a dense form domain.  Suppose

- `a:VxV->R` is a closed symmetric nonnegative form;
- `k:VxV->R` is a continuous skew form, `k(v,w)=-k(w,v)`;
- the trajectory and gradient are regular enough that the chain rule holds
  and `g(t)=grad V(x(t))` lies in `V`; and
- the weak evolution satisfies

$$
\langle g,\dot x\rangle=-a(g,g)-k(g,g)+\ell_t(g).
$$

Then `k(g,g)=0` and

$$
{d\mathcal V\over dt}=-a(g,g)+\ell_t(g).
$$

If `a(g,g)>=m||g||^2`, `ell=0`, and the same PL inequality holds, the previous
decay proof follows.  Domain density, closedness, chain-rule regularity,
forcing duality, and existence of the weak evolution are essential.  The
finite matrix checker sets
`infinite_dimensional_form_hypotheses_verified=False` because it cannot verify
them.

## DSK.5 Counterexamples and boundaries

- Pure skew `[[0,-c],[c,0]]` has nonzero velocity but zero dissipation.
- A nonsymmetric matrix whose symmetric part is indefinite admits negative
  quadratic dissipation and fails.
- Declaring `m` above the smallest eigenvalue makes `S-mI` non-PSD and fails.
- Nonzero forcing with `g^T u>g^T Sg` makes the model potential increase.
- Setting `K=0` reduces exactly to the predecessor symmetric tensor theorem.
