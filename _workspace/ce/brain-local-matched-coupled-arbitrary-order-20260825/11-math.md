# Mathematics lane

Status: COMPLETE

## LCN.1 Local core and collar coverage

Let the base reference scale be `X0>0`, and normalize all radii by `X0`:

$$
r_{\rm in}=R_{\rm in}/X_0,\quad
r_{\rm out}=R_{\rm out}/X_0,\quad
r_{\rm pre}=R_{\rm pre}/X_0.
$$

The backward-covered core condition is

$$m_{\rm core}=r_{\rm in}-r_{\rm pre}\ge0.$$

For an open input collar `eta_in>0`, open output collar `eta_out>0`, and a
uniform inverse-collar image radius `r_pre,col`, require

$$r_{\rm pre,col}\ge r_{\rm pre},$$

$$m_{\rm col}=r_{\rm in}+\eta_{\rm in}-r_{\rm pre,col}\ge0.$$

The global Cn raw-jet theorem uses the point modulus of Dn, so the same
normalized moduli must cover the entire collar through order `n+1`.  Coverage
only through n is insufficient even if every core class inequality passes.

When the global differential certificate passes and these gates hold, every
raw Bell evaluation and matched-preimage displacement stays inside the region
on which its modulus was declared.  This proves the local derivative wrapper.
Strict positive global, core, and collar margins give differential/collar
robust interior; equality coverage passes but is not robust.

## LCN.2 Exact matched domain

For full forward retention additionally require exact normalized contacts

$$r_{\rm pre}^{\rm exact}=r_{\rm in},\qquad
r_{\rm fwd}^{\rm exact}=r_{\rm out},$$

and boundary anchoring

$$h|_{\partial X}=0,\qquad g|_{\partial X}=0$$

in the declared fiber normalization.  The implementation represents the last
two equalities by exact nonnegative residuals and accepts only zero.

Inverse undercoverage, inverse overcoverage, forward undercoverage, forward
overcoverage, graph-boundary failure, and fiber-boundary failure are distinct
conditions and receive distinct codes.  The exact contact set has no open
margin: `domain_contact_robust_interior` is therefore false even when the
differential and collar margins are strict.

## LCN.3 Order, scale, and iteration consistency

The wrapper reads `maximum_order=n` from the global certificate and requires
collar coverage through `n+1`; no C4-specific coefficient is used.  Exact
tests at n=2,4,6 verify this order-generic dependency.

Simultaneous iteration is unchanged because domain wrapping adds no new
derivative coefficient.  Scaling every base radius and collar by the same X0,
and every fiber boundary residual by its Y0, leaves every normalized margin
and contact unchanged.  The input base dimension is preserved, not selected.

These facts close finite local/matched derivative jets only.  Uniform growth
as n tends to infinity and empirical neural boundary validity remain open.
