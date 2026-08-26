# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-local-nonaffine-triangular-c2-extension-20260825`

## Question and exact invariant meaning

Let

$$
U_t=\overline B(c_t,r_t),
\qquad
U_{t+1}=\overline B(c_{t+1},r_{t+1}),
$$

and let $\phi_t$ be a C2 diffeomorphism between open neighborhoods with inverse
$\psi_t$. Strengthen the predecessor's inverse coverage to

$$
\phi_t(U_t)\subseteq U_{t+1},
\qquad
\psi_t(U_{t+1})\subseteq U_t.
$$

The second inclusion is equivalent to $U_{t+1}\subseteq\phi_t(U_t)$, so both
together prove exact matched-domain equality

$$
\phi_t(U_t)=U_{t+1}.
$$

The fixed graph is then fully forward and backward invariant over the declared
base domains, not merely overflow invariant.

## Predecessor evidence

| Evidence | Frozen state | Preserved result | Retry boundary |
|---|---|---|---|
| local graph-independent nonaffine triangular C2 | PASS / final-gated | inverse coverage closes backward-covered overflow C2 | Full forward retention was explicitly excluded. |
| compact-ball boundary audit | selected here | two-sided inclusion implies exact image equality | Both strict interior margins are impossible for inverse compact-ball homeomorphisms. |

## Exact ball-domain certificate

Let $R_t,R_{t+1}$ be raw base radii and let

$$
R_{\rm pre}
=\sup_{x'\in U_{t+1}}\|\psi_t(x')-c_t\|,
\qquad
R_{\rm fwd}
=\sup_{x\in U_t}\|\phi_t(x)-c_{t+1}\|.
$$

The matched-domain certificate requires exact certified suprema

$$
R_{\rm pre}=R_t,
\qquad
R_{\rm fwd}=R_{t+1}.
$$

Values above the relevant radius fail the inclusion. Values strictly below
the radius are inconsistent with two inverse inclusions on compact balls:
the two inclusions imply equality of the image sets, whose boundary reaches
the declared radius. The implementation therefore fails closed on both
positive and negative boundary mismatches instead of reporting a fictitious
robust domain interior.

## Exact boundary-fixed curved witness

On $U=[-1,1]$, let

$$
\phi_a(x)=x+a x(1-x^2),
\qquad 0\le a<\frac12.
$$

Since

$$
\phi_a'(x)=1+a-3ax^2\ge1-2a>0,
\qquad
\phi_a(\pm1)=\pm1,
$$

$\phi_a$ is a C2 diffeomorphism of an open collar of $U$ and maps $U$ onto
itself. Freeze

$$
\mu_a=\frac1{1-2a},
\qquad
\nu_a=\frac{6a}{(1-2a)^3}.
$$

At $a=1/4$, $(\mu,\nu)=(2,12)$. With
$q=1/8$, $\kappa=1/4$, $L_x=H_x=H_y=K_2=K_3=0$,
$\Lambda_2=1$, $R=1$, and $G=1/4$, freeze

$$
\Lambda_{2,\mathrm{out}}^{\rm match}=\frac78,
\quad
\beta_2=\frac12,
\quad
c_{21}=\frac32,
\quad
c_{20}=0.
$$

The differential gates are strict, while both exact domain-contact margins
are zero by necessity.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| exact matched-ball full-forward C2 | SELECTED | Two inverse inclusions prove $\phi_t(U_t)=U_{t+1}$. |
| two strict interior ball margins | REJECTED | Contradicts equality of compact image sets under inverse maps. |
| inverse coverage alone | RETAINED AS PREDECESSOR ONLY | Proves overflow invariance but not full forward retention. |
| unchecked Boolean `domain_matched=True` | REJECTED | Does not expose the two independently falsifiable image bounds. |
| nonaffine coupled C2 | DEFERRED | Graph-dependent inverse comparisons remain separate. |
| C3 and higher | DEFERRED | Higher inverse derivatives remain separate. |

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional domain mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact image-radius identities and exact recurrence algebra.
- `FALSIFIER`: either image radius differs from its declared ball radius;
  predecessor C2 failure; $a\ge1/2$; missing open collar.
- `MATCHED_CONTROLS`: boundary-fixed cubic, identity $a=0$, overflow expander,
  forward/inverse overrun, impossible strict margin, scale covariance,
  dimensions 1/4/5/6/100.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: accepting a nonzero domain-contact margin or inferring
  a neural chart from the apparatus forces revision.
- `CLAIM_CEILING`: conditional exact matched-ball graph-independent nonaffine
  triangular C2 theorem/apparatus; no coupled nonaffine C2, C3+, biology,
  consciousness, or dimension selection.

## Exactness and validation

All inputs use exact integers, `Fraction`, or canonical rational strings.
Floats, Booleans, invalid radii, unequal boundary contacts, and invalid cubic
amplitudes fail closed. Run focused, local/global predecessor, dimensionless,
and graph integration only. No full suite, remote call, or empirical operation
is authorized.
