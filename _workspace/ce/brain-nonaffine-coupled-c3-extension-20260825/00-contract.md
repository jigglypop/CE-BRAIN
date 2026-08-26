# Research contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR:

- `_workspace/ce/brain-nonaffine-coupled-c2-extension-20260825`
- `_workspace/ce/brain-quantitative-coupled-c3-graph-transform-20260825`
- `_workspace/ce/brain-nonaffine-triangular-c3-extension-20260825`

## Question and target theorem

For the graph transform

$$
F_h(x)=\phi(x)+f(x,h(x)),\qquad
Y_h(x)=Bh(x)+g(x,h(x)),\qquad
\mathcal T h=Y_h\circ F_h^{-1},
$$

derive a fully explicit global $C^3$ and conditional $C^{3,1}$ certificate when
the graph-independent base map $\phi$ is nonaffine and the base coordinate is
also coupled to graph height through $f$.  The target includes the exact
four-level recurrence for value, derivative, Hessian, and third-derivative
distances, together with strict boundary and reduction certificates.

The theorem is conditional on the predecessor global tube, invertibility,
$C^1$, $C^{1,1}$, $C^2$, and conditional $C^{2,1}$ gates.  It does not claim
that a measured brain field realizes these hypotheses.

## Domain, normalization, and exactness

- The normalized base and fiber spaces are finite-dimensional real normed
  spaces.  `base_dimension` is supplied; it is preserved and never inferred.
- Every coefficient entering the certificate is dimensionless after division
  by the declared base and fiber reference scales.
- Inputs and outputs are exact nonnegative rational values.  Float, Boolean,
  malformed rational strings, negative moduli, and non-built-in dimensions or
  iteration counts fail closed.
- Algebraic identities and boundary comparisons use exact arithmetic; there
  is no numerical tolerance.

## New hypotheses and notation

Let $\alpha>0$ be the predecessor lower bound for $DF_h$, let $Q$ be the
predecessor $C^0$ graph-transform factor, and put
$r=1+\kappa$ and $\rho=(q\kappa+L_{gx})/\alpha$.  The predecessor supplies
$C_F,C_Y,C_P,C_R,C_N$, all lower-order recurrence coefficients, and the graph
classes $\Lambda_2,\Xi_2$.

The new inputs are:

- $T_\phi\ge0$, the normalized uniform bound on $D^3\phi$ already passed to
  the nonaffine $C^2$ predecessor as the Lipschitz modulus of $D^2\phi$;
- $U_\phi\ge0$, the normalized Lipschitz modulus of $D^3\phi$, a $D^4$-level
  base-map hypothesis;
- $U_f,U_g\ge0$, normalized Lipschitz moduli of the third derivatives of the
  coupled base and fiber nonlinearities;
- $\Lambda_3\ge0$, the invariant graph third-derivative radius, also passed to
  the $C^{2,1}$ predecessor as the Lipschitz radius of $D^2h$;
- $\Xi_3\ge0$, the graph third-derivative Lipschitz radius, required exactly
  when $L_{fy}>0$.

## Frozen claims

1. **One-graph $C^3$ class.**  Derive explicit bounds for $D^3F_h$,
   $D^3Y_h$, the modified third derivative, and $D^3(\mathcal T h)$, with the
   additive $T_\phi$ term retained.
2. **Conditional $C^{3,1}$ class.**  Derive the full modulus, including the
   additive $U_\phi$ term.  Enforce its invariance only when graph coupling
   makes the preimage graph-dependent.
3. **Two-graph recurrence.**  Prove

   $$
   f_{n+1}\le \beta_{3,c}^{\rm na} f_n
   +c_{32,c}^{\rm na}e_n+c_{31,c}^{\rm na}d_n
   +c_{30,c}^{\rm na}\delta_n,
   $$

   with every coefficient explicit and with
   $\beta_{3,c}^{\rm na}=Q/\alpha^3$ strictly below one.
4. **Boundary witness.**  Preserve the exact $h_c(x)=c|x|^3$ equality witness
   showing that $Q/\alpha^3=1$ is not a contraction theorem.
5. **Reductions.**  Setting the base-map curvature triple
   $(H_\phi,T_\phi,U_\phi)$ to zero must recover the affine coupled $C^3$
   certificate term by term.  Setting graph-to-base coupling to zero must
   recover the common-inverse nonaffine triangular $C^3$ recurrence when

   $$
   \mu=\alpha^{-1},\qquad
   \nu=H_\phi\mu^3,\qquad
   \tau=T_\phi\mu^4+3H_\phi^2\mu^5.
   $$

6. **Sine witness.**  For
   $\phi_{\lambda,a}(x)=\lambda x+a\sin x$, $\lambda>a\ge0$, return exact
   bounds $\mu=(\lambda-a)^{-1}$ and
   $H_\phi=T_\phi=U_\phi=a$.

## Predecessor evidence

| Predecessor result | Evidence and SHA-256 | State | Preserved claim | Never-retry boundary |
|---|---|---|---|---|
| Global nonaffine coupled $C^2$ | `12-routes.md` `b5a56dab98cf7f6e504c56d97dcdedbdfee5d280353da2ccca85e6d13f01818e`; `31-validation.md` `90c5515f28d57b483f2f3209a2dc7c9178b70f3688390393ae863c81722e964e`; `40-final-report.md` `1fcad052eb351845e2a2b69d8c5eaaeffa14fae3011aa424c62fb34e85d6a32e` | PASS | $H_\phi,T_\phi$ contributions close the global coupled $C^2$ recurrence. | Do not reuse affine $C^2$ coefficients unchanged or omit $T_\phi$. |
| Affine coupled $C^3$ | `12-routes.md` `e26086790b82b39bd9433144d399526d65273f7c5c909c1bd0b72b4ec55e7579`; `31-validation.md` `9d1f8482548aa1bf5ccc300c25eb9eb6b26786b7f604226836904ec04efdda25`; `40-final-report.md` `e2de4cf0fde28f6336fdd90187d719e07e7226c67290645355c39d94d147b06c` | PASS | Exact inverse-composition identity, conditional $C^{3,1}$ class, and four-level recurrence for an affine base. | Do not reuse triangular coefficients under nonzero graph-to-base coupling. |
| Global nonaffine triangular $C^3$ | `12-routes.md` `1a09da7810b1db3985cde76fa3dde28630cfb917069217d196e1ad7f341ff015`; `31-validation.md` `073d09ed269dd115e2770e538b6617fa1d240f1b1b1e7d6fd75e5bf88b4dfca0`; `40-final-report.md` `8c4a7be3cb89b06e1d1daf34bc2718fafe587c3a9b5dcf2f6202b3434a2aa080` | PASS | Exact third-order common-inverse chain with $\mu,\nu,\tau$ and strict $q\mu^3<1$. | Do not omit $D^2\psi$, $D^3\psi$, or the $D^4$-level map modulus. |

## Candidate set fixed before calculation

| Candidate | Prior decision rule |
|---|---|
| Add $T_\phi$ and $U_\phi$ to the generic coupled inverse-composition skeleton | Preferred: it preserves both predecessor reductions and exposes an independent fourth-order falsifier. |
| Reuse the affine coupled $C^3$ coefficients unchanged | Reject if any direct $D^3\phi$ or $D^3\phi(x_1)-D^3\phi(x_2)$ term survives. |
| Substitute inverse bounds $\mu,\nu,\tau$ directly into the coupled formula | Reject if graph-dependent preimages require the full variable-Jacobian correction already present in the coupled predecessor. |
| Proceed without $U_\phi$ | Reject if the $C^{3,1}$ comparison contains an uncontrolled $D^3\phi$ increment. |
| Local or matched-domain nonaffine coupled $C^3$ | Defer until the global theorem passes; it adds domain coverage, not a different global differential identity. |

## Brain/empirical contract fields

- `BIO_STARTING_MECHANISM`: not invoked; this run proves a differential
  graph-transform statement and introduces no biological baseline equation.
- `CE_DELTA`: graph-independent nonaffine base curvature inside the existing
  abstract graph-transform model.
- `MEASUREMENT_MODEL`, `DATA_PROVENANCE`, `DATA_SPLIT`, `OBSERVABLES`,
  `RESIDUAL_RULE`: not applicable; no data are read or scored.
- `FALSIFIER`: exact affine and triangular reductions, zero-curvature and
  nonzero-curvature sine witnesses, class-bound equality, and bunching
  equality.
- `MATCHED_CONTROLS`: the three predecessor certificates listed above.
- `MODEL_SELECTION`: no fit and no parameter search; formulas are selected by
  exact identities and reduction requirements.
- `REVISION_TRIGGER`: an algebraic mismatch, a failed exact reduction, or an
  uncovered fourth-order increment forces revision before implementation.
- `CLAIM_CEILING`: conditional global mathematical theorem plus implementation
  certificate only.  No claim about actual neural dynamics, consciousness,
  or a preferred dimension is permitted.
