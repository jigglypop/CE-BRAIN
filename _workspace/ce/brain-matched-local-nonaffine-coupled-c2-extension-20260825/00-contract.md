# Research contract

Status: COMPLETE

Mode: light successor theorem

PREDECESSOR: `_workspace/ce/brain-local-nonaffine-coupled-c2-extension-20260825`

SECOND PREDECESSOR: `_workspace/ce/brain-matched-domain-local-nonaffine-c2-extension-20260825`

## Question

What boundary-compatible graph class and exact domain contacts upgrade the
backward-covered graph-dependent local C2 theorem to full forward/backward
matched-domain invariance?

## Predecessor evidence

| Predecessor | State | Preserved result | Missing seam |
|---|---|---|---|
| local nonaffine coupled C2 | PASS / final-gated | Uniform $F_h^{-1}$ coverage and unchanged C0/C1/C2 recurrence | It proves overflow invariance only. |
| matched graph-independent nonaffine C2 | PASS / final-gated | Forward plus inverse inclusions imply exact compact-ball image equality and zero contact margin | Its base map does not vary with $h$. |

No empirical, simulator, threshold, seed, endpoint, or decoder route is
opened. The new mechanism is a boundary-anchored graph class preserved by the
fiber transform.

## Frozen boundary-compatible class

For compact base balls, restrict admissible graphs by

$$
h|_{\partial U_t}=0.
$$

Require the fiber boundary condition

$$
g_t(x,0)=0
\quad\text{for every }x\in\partial U_t.
$$

Then $Y_h=0$ on the input boundary whenever $h=0$ there. Require independently
supplied exact uniform contacts for the actual graph-dependent base maps:

$$
R_{\rm pre}^{\rm exact}=R_t,
\qquad
R_{\rm fwd}^{\rm exact}=R_{t+1}.
$$

Together with the local predecessor, these contacts prove
$F_{t,h}(U_t)=U_{t+1}$ for every admissible graph. Domain-contact robust
interior is structurally false.

## Exact nonzero-coupling witness

Let

$$
\phi_a(x)=x+a x(1-x^2),
\qquad
f(x,y)=\varepsilon y,
$$

on the boundary-anchored graph class. If

$$
0\le a<\frac12,
\qquad
1-2a-\varepsilon\kappa>0,
$$

then

$$
F_h'(x)\ge1-2a-\varepsilon\kappa>0,
\qquad
F_h(\pm1)=\pm1.
$$

Thus each $F_h$ maps the unit interval exactly onto itself. Freeze

$$
a=\frac1{100},
\quad \varepsilon=\frac1{100},
\quad \kappa=\frac12,
\quad B=\frac1{10},
\quad g=0.
$$

Then the base inverse bound is $50/49$, the actual coupled inverse bound is
$40/39$, $H_\phi=T_\phi=3/50$, both exact domain radii equal one,
$\beta_{2,c}=6272/59319$, and the anchored fiber boundary is preserved.

## Candidate ordering fixed before implementation

| Candidate | Decision | Independent discriminator |
|---|---|---|
| boundary-anchored graph class plus exact contacts | SELECTED | Supplies a nonzero-coupling witness and preserves both base and fiber boundaries. |
| base-map boundary fixation without graph anchoring | REJECTED | A constant nonzero graph shifts $F_h(\pm1)$ outside the target. |
| graph anchoring without fiber boundary preservation | REJECTED | The transformed graph leaves the anchored class. |
| positive exact contact margin | REJECTED | Exact image equality reaches compact-ball boundaries. |
| boolean matched-domain assertion | REJECTED | Hides four independently falsifiable boundary/domain inputs. |
| C3 and higher | DEFERRED | Requires fourth-order moduli and higher recurrences. |

## Required controls

- exact nonzero-coupling cubic witness and zero-coupling reduction;
- full identity with the overflow-local differential predecessor;
- graph-boundary and fiber-boundary failures are independent and named;
- inverse/forward strict-contact and overrun failures;
- predecessor failure remains primary;
- exact recurrence, scale covariance, dimensions 1/4/5/6/100, and invalid
  exact inputs.

## Brain-equation admission fields

- `BIO_STARTING_MECHANISM`: UNVERIFIED; not used.
- `CE_DELTA`: none; conditional mathematics only.
- `MEASUREMENT_MODEL`: NOT APPLICABLE.
- `DATA_PROVENANCE`: none.
- `DATA_SPLIT`: NOT APPLICABLE.
- `OBSERVABLES`: none.
- `RESIDUAL_RULE`: exact identities, boundary residuals, and rational fixtures.
- `FALSIFIER`: unanchored-graph boundary shift, fiber-boundary escape,
  nonexact contact, failed predecessor identity.
- `MATCHED_CONTROLS`: strict witness, zero coupling, four independent boundary
  failures, predecessor ordering, scale and dimension controls.
- `MODEL_SELECTION`: no fitted model.
- `REVISION_TRIGGER`: any hidden boolean domain premise or missing boundary
  preservation term forces revision.
- `CLAIM_CEILING`: conditional exact matched local nonaffine coupled C2; no
  C3+, biology, consciousness, or dimension selection.

## Exactness and validation

Exact rational inputs only. Floats, Booleans in numeric fields, negative
radii/residuals, singular witness gaps, and invalid iterations fail closed.
Run focused, predecessor adjacency, dimensionless, and graph integration only.
