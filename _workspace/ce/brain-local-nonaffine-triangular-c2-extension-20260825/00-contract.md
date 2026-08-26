# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-nonaffine-triangular-c2-extension-20260825`

## Question and local invariant meaning

Let $U_t=\overline B(c_t,r_t)$ be convex normalized base balls and let
$\phi_t$ extend to a C2 diffeomorphism between open neighborhoods. Put
$\psi_t=\phi_t^{-1}$. Replace the predecessor's global-domain premise by the
uniform local coverage condition

$$
\psi_t(U_{t+1})\subseteq U_t,
\qquad
\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|
\le r_{\rm pre,t}\le r_t.
$$

The graph transform is then a self-map of graph families over the declared
local domains. Its fixed graph is `BACKWARD_COVERED_OVERFLOW_INVARIANT`: a
graph point is carried to the next graph whenever its output base point lies
in $U_{t+1}$. No claim is made that every point of the input graph remains in
the next base domain.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| global graph-independent nonaffine triangular C2 | PASS / final-gated | exact $D^2S[D\psi,D\psi]+DSD^2\psi$ class and recurrence | Global domain was stronger than the calculus actually used. |
| local-domain audit | selected here | only $\psi_t(U_{t+1})\subseteq U_t$ is needed to evaluate every graph transform | Full forward retention requires a separate equality/inclusion premise. |

## Frozen local certificate

Normalize the raw base radius and inverse-image radius by the same positive
base reference scale $X_0$:

$$
r_x=R_x/X_0,
\qquad
r_{\rm pre}=R_{\rm pre}/X_0,
\qquad
m_{\rm cov}=r_x-r_{\rm pre}.
$$

The local coverage gate is non-strict, $m_{\rm cov}\ge0$; equality passes but
is not robust. All predecessor C2 constants and gates are unchanged because
every derivative estimate is uniform on the declared local neighborhoods.
Predecessor failures remain primary; coverage failure is
`LOCAL_C2_INVERSE_BASE_DOMAIN_NOT_COVERED`.

## Exact expanding curved witness

For

$$
\phi_{\lambda,a}(x)=\lambda x+a\sin x,
\qquad \lambda>a\ge0,
$$

freeze

$$
\mu_{\lambda,a}=\frac1{\lambda-a},
\qquad
\nu_{\lambda,a}=\frac{a}{(\lambda-a)^3},
\qquad
r_{\rm pre}\le\mu_{\lambda,a}r_x.
$$

The strict fixture is $\lambda=2$, $a=1/4$, $r_x=1$, hence
$\mu=4/7$, $\nu=16/343$, $r_{\rm pre}=4/7$, and coverage margin $3/7$.
With $q=1/2$, $\kappa=1$, $L_x=1/8$, $H_x=H_y=K_2=K_3=1/16$,
$\Lambda_2=1$, $R=1$, and $G=1/4$, freeze

$$
\Lambda_{2,\mathrm{out}}^{\rm loc}=\frac{94}{343},
\quad
\beta_2=\frac8{49},
\quad
c_{21}=\frac{36}{343},
\quad
c_{20}=\frac{37}{343}.
$$

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| backward-covered/overflow local C2 graph | SELECTED | Exact inverse-domain coverage is sufficient for repeated graph transforms. |
| full forward-invariant local graph from inverse coverage alone | REJECTED | $\phi(x)=2x$ passes inverse coverage but sends boundary points outside. |
| coverage-free local C2 | REJECTED | $\phi(x)=x/2$ requires $h(2x')$ outside the declared domain. |
| exact matched-domain full invariance | OPEN | Requires a separately certified structural equality $\phi_t(U_t)=U_{t+1}$. |
| nonaffine coupled C2 | DEFERRED | Graph-dependent inverse comparisons remain different. |
| C3 and higher | DEFERRED | Higher inverse derivatives and Faà di Bruno bounds remain different. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional local mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact symbolic identities and rational fixtures.
- `FALSIFIER`: inverse image exits the domain; forward-overflow overclaim;
  missing $\nu$; $q\mu^2=1$.
- `MATCHED_CONTROLS`: strict/equality/failed coverage, expanding sine witness,
  base-scale covariance, global arithmetic reduction, dimensions 1/4/5/6/100.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: any use of $h$ outside $U_t$, or any unconditional full
  forward-invariance statement, forces revision.
- `CLAIM_CEILING`: conditional backward-covered local graph-independent
  nonaffine triangular C2 theorem/apparatus only; no full-domain forward
  retention, coupled nonaffine C2, C3+, biology, consciousness, or dimension
  selection.

## Exactness and validation

All scalar inputs use exact integers, `Fraction`, or canonical rational
strings. Floats, Booleans, nonpositive domain radius, negative image bounds,
and invalid witness parameters fail closed. Run the focused local test first,
then predecessor, dimensionless, and graph integration. No full suite,
benchmark, remote call, or empirical operation is authorized.
