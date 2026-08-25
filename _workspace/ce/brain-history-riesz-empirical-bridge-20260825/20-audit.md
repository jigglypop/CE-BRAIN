# Formal status audit

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

Gate: PASS

This audit covers only the stable `00-contract.md`, `10-sources.md`,
`11-math.md`, and `12-routes.md` snapshot. No code, canonical document, Git
state, or data bytes were changed.

## Verdict

M1 and M2 are correctly stated as conditional mathematics with explicit
failure boundaries. M1 closes the zero-fill history-domain/sign issue and
separates a form-scale result from a strong ambient metric. M2 closes the
chord/Lipschitz/full-contour and annular Fourier steps, while explicitly
withholding rigorous executable status from ordinary float64 output. The
source lane separates de Vries optical resource material from the Allen
Neuropixels/electrophysiology resource and treats Stringer as observational,
model-dependent evidence. Allen manifest/session overlap and the biological
baseline remain UNVERIFIED, so no E1 implementation or empirical score is
admitted.

## M1 closure decisions

| Claim ID | Finding | Status |
|---|---|---|
| CE-M1-001 | For `H_rho` with `rho=e^(2 alpha s)`, the zero-fill shift has `T_0(t)h(s)=h(s+t)` on `s+t<=0`, exact norm `e^(-alpha t)`, dense domain `W^{1,2}_rho` with `h(0)=0`, and generator `+partial_s`. | Conditional theorem; PASS |
| CE-M1-002 | The boundary-coupled delay history `h(0)=Bx` is not the zero-fill semigroup; the sign-reversed transport has the wrong direction for this forgetting convention. | Counterexample/closure; PASS |
| CE-M1-003 | Direct sums have a common exponential bound only with a uniform lower rate such as `inf_e alpha_e>0`; without it only coordinatewise contraction is claimed. | Correctly limited; PASS |
| CE-M1-004 | The unbounded edge sum is a densely defined closed lower-bounded form only under the common complete form-domain, closedness, summability, and smoothness hypotheses. The representation theorem yields an unbounded self-adjoint operator in general. | Conditional theorem; PASS |
| CE-M1-005 | The `L^2` Dirichlet form example gives an unbounded `I-partial_s^2` representative and therefore refutes calling every coercive unbounded form a strong metric on ambient `H`. | Complete P0 counterexample; parent overclaim retired |

The norm derivation and generator sign are consistent: the weighted change of
variables contributes `e^(-2 alpha t)` to squared norm, and conjugation gives
`partial_s-alpha` in unweighted coordinates, hence `partial_s` in the weighted
space. The audit accepts M1 only with the displayed domain and boundary.

## M2 closure decisions

| Claim ID | Finding | Status |
|---|---|---|
| CE-M2-001 | Nearest equispaced circle node has chord distance `2 r sin(pi/(2N))`; singular value is 1-Lipschitz in the complex induced 2-norm. | Conditional full-circle theorem; PASS |
| CE-M2-002 | Positive `delta_hat_N` implies resolvent-free contour and `R_Gamma <= delta_hat_N^(-1)` only when node singular-value and chord bounds are rigorous enclosures. | Correctly conditional; PASS |
| CE-M2-003 | The annulus/maximum-principle argument uses inner/outer radii `r e^(-a)`, `r e^(a)`, both certified boundaries, and no spectrum in the annulus. The factors `r_- / delta_-` and `r_+ / delta_+` are required by the integrand. | Conditional theorem; PASS |
| CE-M2-004 | Fourier aliasing gives `2 M_a/(e^(aN)-1)` under a certified analytic strip and bound. | Conditional theorem; PASS |
| CE-M2-005 | Float64 sampled values are explicitly estimates; they cannot be labelled verified finite arithmetic without outward rounding or equivalent enclosure. | Scope guard; PASS |
| CE-M2-006 | Contour crossing, negative lower bound, annulus spectrum, high pseudospectral resolvent, coarse N, and floating underestimation are retained adverse cases. | Falsifier coverage; PASS |

No sampled separation, sampled resolvent, or N-doubling result is promoted to
all-contour separation, exact rank, or a quadrature error bound. The full
resolvent perturbation condition `R_Gamma ||E||<1` is retained, so eigenvalue
distance alone is not used as a pseudospectral stability substitute.

## Source and empirical-bridge audit

- de Vries et al. is correctly treated as the Allen Visual Coding resource
  reference; its optical and electrophysiology resources are not conflated.
- The Neuropixels white paper and AllenSDK documentation are only partial
  release/schema verification. Exact manifest, version, checksums, terms, and
  eligible sessions remain unverified.
- Stringer et al. is correctly limited to observational Allen Neuropixels
  activity, state-conditioned covariance/participation-ratio analysis and a
  model-dependent recurrence relation. It is not an intervention on recurrent
  strength and does not identify a CE history term.
- The separate synaptic physiology data are not merged with Neuropixels
  activity into one likelihood or direct edge/state observation.
- The biological baseline equation, count likelihood choice, delay, exact
  session split, and nonoverlap with sealed Allen/predecessor material remain
  `UNVERIFIED_PENDING_SOURCE`/`UNVERIFIED` as labelled. No data bytes or
  endpoint values were opened.

The maximum empirical ceiling is correctly L3 compatibility after a future
source-locked held-out run; it cannot become mechanism identity, whole-brain
geometry, consciousness, or fixed `d=4--6`.

## Implementation-admitted scope

No implementation is admitted for E1 while source, measurement, manifest,
split, and overlap gates are unverified. M2 executable output may be admitted
only as a float64 numerical estimate unless outward-rounded interval
arithmetic (or an equivalent enclosure) is actually implemented; only then
can it receive the contract's `verified finite arithmetic` label. M1 may be
implemented as the explicitly declared zero-fill semigroup/form-domain model,
but not as a coupled delay boundary or a strong ambient metric without the
additional bounded/equivalent-norm hypotheses.

## Gate rationale

`Gate: PASS` is warranted because every active mathematical statement is
conditional with its hypotheses, complete counterexamples retire the unsafe
parents, source claims have provenance ceilings, and all UNVERIFIED fields are
visible. This is a closure pass for the contract/math/source boundary, not a
claim that empirical identification succeeded. The predecessor prohibitions on
edge-only coercivity, generic skew neutrality, loop-forced 4--6, oblique
concentration, sealed Allen/CCEP reuse, and consciousness conclusions remain
in force.

## Revision-1 build addendum

The M2 implementation is correctly limited to float64 estimates in
`finite_contour_bounds.py`. It exposes the exact labels
`FLOAT64_UNVERIFIED_FULL_CIRCLE_ESTIMATE` and
`FLOAT64_UNVERIFIED_ANALYTIC_STRIP_ESTIMATE`; no output is called a verified
full-circle bound, interval enclosure, or analytic-strip certificate. The
required positive `spectral_reference_scale` keeps raw spectral quantities and
dimensionless normalized quantities distinct.

The central-circle estimate is retained as a separate estimate at radius `r`.
The inner/outer circles are used only for the numerical `M_estimate` path, and
annulus or boundary eigenvalues fail closed by suppressing `M_estimate` and the
quadrature-error estimate. Overflow/unrepresentable strip exponent preflights
also reject rather than emit a misleading result. This matches the M2
annulus/central-radius semantics and the adverse cases in `11-math.md`.

The focused build validation reports `14/14 passed`, covering scaling,
nonpositive coarse `delta_hat`, pseudospectral behavior, annulus suppression,
clean strip comparison, boundary suppression, and invalid-input/preflight
rejection. The clean-strip error comparison is explicitly a fixture
observation, not a verified error bound. No E1 code, source manifest, data,
likelihood, or empirical score was implemented.

`Gate: PASS` remains warranted: the revision adds only the admitted finite
float64 M2 estimate seam, preserves fail-closed boundaries and the empirical
source stop, and does not promote float output into verified arithmetic,
biology, a whole-brain metric, or a preferred dimension.

## Source-lock addendum

The source revision is coherent with its cited official Allen documentation.
It records `EcephysProjectCache.MANIFEST_VERSION = 0.2.1` as a schema/API
fact while keeping the exact manifest bytes, checksums, eligible session IDs,
and overlap receipt `UNVERIFIED`. It also correctly records the AllenSDK 2.0
compatibility boundary for pre-2020-06-11 Visual Coding Neuropixels NWB
releases; this is a provenance constraint, not evidence that the current
manifest or sessions have been opened.

The default hidden-unit criteria are accurately transcribed from the official
documentation: `presence_ratio < 0.95`, `isi_violations > 0.5`, and
`amplitude_cutoff > 0.1`. The source lane correctly treats these filters as a
future measurement choice affecting covariance/dimension estimates and
requires the filtered-versus-complete-unit decision to be frozen before any
endpoint access.

The additions do not alter the source ceiling. de Vries remains the Visual
Coding resource identity rather than a Neuropixels-only manifest receipt;
Stringer remains observational/model-dependent; synaptic physiology remains a
separate dataset; and no empirical bytes, session IDs, scores, or biological
baseline were opened. `Gate: PASS` remains warranted with E1 still blocked at
the source/provenance gate and the maximum future empirical ceiling at L3
compatibility.

## Revision-1 predecessor nonoverlap addendum

The revised nonoverlap split is logically correct and does not weaken the
leakage gate. The predecessor sealed material is identified as ex-vivo
`aisynphys` Synaptic Physiology with `slice/experiment/cell/pair` identifiers;
E1 targets in-vivo Visual Coding Neuropixels with
`subject/session/probe/unit` identifiers. These are distinct dataset families
and namespaces, so cross-resource numeric-ID comparison is correctly marked
`NOT_APPLICABLE / SEMANTICALLY_INVALID`, rather than falsely presented as an
ID-based leakage test.

The remaining relevant leakage question is within the E1 Neuropixels resource.
Exact eligible session IDs, repeats, missingness, and calibration/development/
held-out assignment remain `UNVERIFIED_PENDING_METADATA` and must be frozen by
a metadata-only receipt before endpoint access. The unresolved animal-level
donor question is not silently converted into session independence; it remains
outside the claimed cross-resource session-leakage test.

This revision preserves the source and evidence ceilings: no data bytes or
endpoints are opened, no E1 implementation or score is admitted, and any
future observational result remains at most L3 compatibility. Therefore
`Gate: PASS` remains warranted.

## E1 metadata-lock specification addendum

Audit target: `artifacts/e1-metadata-lock-spec.md` (frozen, unexecuted).

The permitted action is metadata-only: it limits access to the unsuppressed
Allen session table and explicitly forbids session-data, units, LFP, metrics,
NWB, signal and scientific-endpoint calls. The receipt also requires explicit
negative invocation evidence. The canonicalization (UTF-8 JSON Lines, LF,
sorted keys/arrays/rows, finite numbers, byte/row/specimen counts and
SHA-256) and fixed-salt first-eight-byte SHA-256 allocation over decimal
`specimen_id` are deterministic. Assigning the complete table before any
eligibility or unit filter prevents post-hoc specimen movement and preserves
the two-specimen minimum fail-closed rule.

The predecessor/E1 namespace statement is consistent with the contract:
ex-vivo `aisynphys` `slice/experiment/cell/pair` versus in-vivo Visual Coding
Neuropixels `subject/session/probe/unit`; cross-resource numeric-ID comparison
is `NOT_APPLICABLE / SEMANTICALLY_INVALID`. The specification remains
`FROZEN / UNEXECUTED`; a passing receipt would open only a source-locked
baseline contract, not E1 scoring or any biological/whole-brain/consciousness/
dimension claim. The maximum empirical ceiling remains L3 compatibility.

P0: none. P1: the field-availability boundary is underspecified. The spec
says to retain the listed session-table fields only when present, but makes only
session/specimen ID failures explicitly fail-closed. Before execution, it must
declare which fields are required for provenance, repeat/missingness checks and
eligibility (or explicitly classify the rest as optional), and make absence,
unsupported schema, or unusable type for each required field produce a named
fail-closed status rather than a passing receipt with incomplete metadata.
P2: the exact API/schema receipt, IDs and split checksum remain expected
UNEXECUTED state, not evidence.

At that revision point, the missing required-field policy made the gate
`REVISE`; no endpoint access or E1 implementation was admitted.

## E1 metadata-lock P1 resolution addendum

The revised `artifacts/e1-metadata-lock-spec.md` resolves the prior P1. It
now separates required core fields (`ecephys_session_id`, `specimen_id`,
`session_type`, `date_of_acquisition`) from optional descriptive fields,
requires explicit index-to-canonical-key materialization, and assigns named
fail-closed outcomes for missing required fields, unsupported schema, invalid
types, inconsistent duplicate rows, and one-session/multiple-specimen
assignments. Optional-field presence/type diagnostics also prevent silent
coercion. This is sufficient for the metadata-only provenance boundary.

The deterministic specimen-level SHA-256 split, namespace nonoverlap statement,
`FROZEN / UNEXECUTED` status, and L3-only empirical ceiling remain unchanged.
No P0/P1 remains. P2 is unchanged: the receipt, IDs and split checksum have
not been executed and therefore are not evidence. `Gate: PASS` is restored;
E1 implementation, endpoint access, and biological or consciousness claims
remain unadmitted.
