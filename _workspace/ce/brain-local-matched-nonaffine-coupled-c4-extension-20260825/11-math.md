# Mathematics lane

Status: COMPLETE

## LC4.1 Backward-covered local C4

Let core radii be `R_t,R_t+1`, input/output open C4 collar widths
`eta_t,eta_t+1`, and uniform inverse-image bounds `R_pre,R_pre,4`. Normalize
all radii by the declared base scale. The independent coverage gates are

$$R_{\rm pre}\le R_t,$$

$$R_{\rm pre,4}\ge R_{\rm pre},$$

$$R_{\rm pre,4}\le R_t+\eta_t,$$

with `eta_t>0` and `eta_t+1>0`. The first is core coverage; the last two ensure
that every point required by the fourth derivative and its point modulus lies
inside the declared extension on which the global bounds are uniform.

The margins are

$$m_{\rm core}=R_t-R_{\rm pre},\qquad
m_{\rm collar}=R_t+\eta_t-R_{\rm pre,4}.$$

Equality passes coverage but is not a robust collar interior.

## LC4.2 Exact matched local C4

Add exact inverse and forward contacts

$$R_{\rm pre}=R_t,\qquad R_{\rm fwd}=R_{t+1},$$

and boundary anchoring

$$h|_{\partial U_t}=0,\qquad g|_{\partial U_t}=0.$$

Together with the open C4 collar gates, these give full forward/backward
matched-domain invariance. Domain contact has zero margin by construction, so
`domain_contact_robust_interior=False`; the distinct flag
`differential_and_collar_robust_interior` may remain true.

## LC4.3 Exact cubic witness

For

$$F_h(x)=x+a x(1-x^2)+\varepsilon h(x)$$

on `[-1,1]`, with boundary-anchored `h`, the C3 collar predecessor gives the
exact core/contact values. The base polynomial is cubic, hence

$$D^4\phi=0,\qquad D^5\phi=0.$$

Thus the same collar is a genuine C4 witness with
`U_phi=V_phi=0`; it is not merely a renamed C3 fixture. At
`a=epsilon=1/100`, graph slope `1/2`, and input collar `1/10`,

`alpha_core=39/40`, `alpha_collar=9687/10000`,
`eta_out=9687/200000`, `R_pre,4=21/20`, and collar margin `1/20`.

The wrappers leave the global five-layer recurrence unchanged and preserve the
input dimension without selecting it.
