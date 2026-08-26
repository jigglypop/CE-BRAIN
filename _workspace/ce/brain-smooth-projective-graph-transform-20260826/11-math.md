# Mathematics lane

Status: COMPLETE

## SPG.1 Finite triangular operator

For maximum order `n`, collect the full error recurrence as

$$
\Delta^{(m+1)}\preceq A_n\Delta^{(m)},
$$

where row zero is `(q0,0,...,0)` and row `j` is
`(c_j0,...,c_jj,0,...,0)`.  Thus `A_n` is lower triangular and

$$
\rho(A_n)=\max\{q_0,\beta_1,\ldots,\beta_n\}<1.
$$

The off-diagonal coefficients need not make a one-step row norm smaller than
one.  Triangularity is enough: each entry of `A_n^m` is a finite sum of a
polynomial in `m` times powers of diagonal factors.  Hence `A_n^m` tends to
zero and `sum_m A_n^m` converges entrywise.

## SPG.2 Projective C-infinity theorem

Let `E_n=C^n(K)` on one compact covered domain, with restriction maps
`E_(n+1)->E_n`, and let

$$E_\infty=\bigcap_{n\ge0}E_n$$

carry the seminorms `||.||_Cn`.  Assume:

1. one graph transform `T` maps `E_infinity` and every certified invariant
   class into themselves;
2. for every natural `n>=2`, a full certificate exists and its restriction to
   every lower order is exactly the earlier certificate;
3. every finite transition matrix has strict diagonal factors;
4. all certificates describe the same orbit `h_(m+1)=T h_m`; and
5. `E_infinity` is complete in the projective Fréchet topology.

Apply SPG.1 to consecutive increments

$$
\delta_n^{(m)}=
(\|T^{m+1}h_0-T^mh_0\|_{C^0},\ldots,
\|T^{m+1}h_0-T^mh_0\|_{C^n}).
$$

Then `delta_n^(m) <= A_n^m delta_n^(0)` and the increments are summable for
each fixed `n`.  The orbit is Cauchy in every Cn seminorm.  Projective
completeness gives one `h_* in E_infinity`; compatibility prevents a different
limit at each order.  Continuity in each finite level gives `T h_*=h_*`.
C0 uniqueness from `q0<1` makes this smooth fixed graph unique.

This is a conditional nonanalytic C-infinity theorem.  It requires no uniform
factorial or exponential control as `n` grows and therefore proves neither
analyticity nor any Gevrey order.

## SPG.3 Why finite prefixes cannot promote

For every finite `N`, a function can have all derivatives through order `N`
and fail to have derivative `N+1`; for example a suitable localized multiple
of `|x|^(N+1/2)`.  Therefore verification through C2..CN cannot establish the
all-orders hypothesis.  The machine certificate records

- `every_finite_order_hypothesis_verified=False`,
- `projective_limit_completeness_hypothesis_verified=False`,
- `common_orbit_hypothesis_verified=False`, and
- `cinfinity_claim_admitted=False`.

These fields describe the finite evidence ceiling, not a counterexample to
the conditional theorem SPG.2.
