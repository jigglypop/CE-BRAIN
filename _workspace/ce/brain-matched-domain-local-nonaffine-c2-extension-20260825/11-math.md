# Mathematics lane

Status: COMPLETE

## P1. Two inclusions give exact domain matching

Let $\phi_t$ be injective on a neighborhood of $U_t$ and let $\psi_t$ be its
inverse on a neighborhood of $U_{t+1}$. If

$$
\phi_t(U_t)\subseteq U_{t+1}
$$

and

$$
\psi_t(U_{t+1})\subseteq U_t,
$$

then applying $\phi_t$ to the second inclusion gives

$$
U_{t+1}subseteq\phi_t(U_t).
$$

Hence

$$
\phi_t(U_t)=U_{t+1}.
$$

For an invariant graph $h_t$ this strengthens the overflow identity to

$$
F_t(\operatorname{graph}h_t)
=\operatorname{graph}h_{t+1}
$$

over the entire declared local base domains. Every input graph point has an
output base point in $U_{t+1}$, and every output graph point has its unique
preimage in $U_t$.

## P2. Exact ball boundary contact

For $U_t=\overline B(c_t,r_t)$ and
$U_{t+1}=\overline B(c_{t+1},r_{t+1})$, define the exact suprema

$$
R_{\rm pre}
=\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|,
$$

$$
R_{\rm fwd}
=\sup_{x\in U_t}\|\phi_t(x)-c_{t+1}\|.
$$

The inequalities $R_{\rm pre}\le r_t$ and
$R_{\rm fwd}\le r_{t+1}$ prove the two inclusions. Once P1 proves exact set
equality, the image is the full closed output ball, so it contains points at
distance $r_{t+1}$ from $c_{t+1}$. Therefore
$R_{\rm fwd}=r_{t+1}$. Applying the same reasoning to the inverse gives
$R_{\rm pre}=r_t$.

Thus a claimed positive margin on either exact supremum is inconsistent with
the matched-domain premises. A loose certified upper bound above the radius
does not prove inclusion. Exact equality is the only admitted ball-radius
certificate, and its domain robustness margin is necessarily zero.

## P3. C2 full-forward theorem

The predecessor already proves that inverse coverage and the uniform local
nonaffine C2 gates produce a unique overflow-invariant C2 graph. Adding forward
coverage changes no derivative coefficient. It changes only the set-theoretic
conclusion from an intersection identity to full graph equality.

**Conditional theorem.** Suppose both domain maps extend C2 to open collars,
the exact boundary-contact certificate of P2 passes, and all predecessor gates
pass, including

$$
\Lambda_{2,\mathrm{out}}le\Lambda_2,
\qquad
q\mu^2<1.
$$

Then the unique local graph is C2 and fully forward/backward invariant across
the matched domains. Its value, derivative, and Hessian recurrences are
identical to the predecessor recurrences.

## P4. Boundary-fixed nonaffine witness

On $U=[-1,1]$, put

$$
\phi_a(x)=x+a x(1-x^2),
\qquad 0\le a<\frac12.
$$

The derivative and second derivative are

$$
\phi_a'(x)=1+a-3ax^2,
\qquad
\phi_a''(x)=-6ax.
$$

On $U$, $\phi_a'\ge1-2a>0$. Because this lower bound is strict at the
boundary, continuity supplies an open collar on which the derivative remains
positive. Also $\phi_a(-1)=-1$ and $\phi_a(1)=1$, so monotonicity proves
$\phi_a(U)=U$. The inverse-function identities give

$$
\|D\psi_a\|\le\frac1{1-2a},
\qquad
\|D^2\psi_a\|
\le\frac{6a}{(1-2a)^3}.
$$

At $a=1/4$, $\mu=2$ and $\nu=12$. For the contract's exact fixture,

$$
\Lambda_{2,\mathrm{out}}=\frac78,
\qquad
\beta_2=\frac12,
\qquad
c_{21}=\frac32,
\qquad
c_{20}=0.
$$

The differential class and bunching margins are both $1/8$ and $1/2$
respectively, while both domain-contact margins equal zero.

## P5. Controls and ceiling

At $a=0$, the witness becomes the identity and all inverse-curvature terms
vanish. At $a=1/2$, $\phi_a'(\pm1)=0$, so the finite inverse-derivative bound
fails. The predecessor expander $\phi(x)=2x$ has strict inverse coverage but
forward radius $2>1$, so it cannot pass the matched-domain gate.

Verdict: exact matched-ball full-forward graph-independent nonaffine
triangular C2 is proved. The domain gate is structurally exact and non-robust,
while the differential gates may be strict. Nonaffine coupled C2, C3+, and
empirical brain identification remain open.

