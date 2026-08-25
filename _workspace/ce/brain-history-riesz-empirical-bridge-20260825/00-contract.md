# Research contract — infinite history, certified contour, empirical bridge

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

## 1. Frozen objective and scope

This successor does not repeat the predecessor's finite L0 proofs. It addresses
three remaining gaps: (M1) domain/closedness for an unbounded history generator
and edge forms; (M2) a computable full-circle resolvent and analytic-strip
quadrature certificate for finite nonnormal Riesz projections; and (E1) a
source-locked real-neural-recording bridge that keeps biological baseline,
measurement model, and the CE history term separate.

No result may identify consciousness, a whole-brain Riemannian metric, or a
preferred dimension. The frozen candidate menu remains

$$
d\in\{1,2,3,4,5,6,8,10,12\}.
$$

## 2. PREDECESSOR_EVIDENCE

| Predecessor result | Evidence and status | Preserved claim | Retry prohibition |
|---|---|---|---|
| Coercive bounded edge metric | predecessor `11-math.md`, Theorems 1–2; `20-audit.md` Gate PASS | bounded $D_e$ plus summability and $A_0\succeq m_0I$ gives a strong metric and perturbation bound | do not remove the baseline or infer topology from $b_e$ |
| Finite normal/history seam | `history_edge_subspace.py`; focused 17/17 PASS | finite numerical certificates only | do not promote finite tolerances to exact infinite-dimensional claims |
| Finite nonnormal contour seam | `finite_riesz.py`; focused 6/6 PASS | $P_N,P_{2N}$ and sampled/a-posteriori residuals, with exact $P$ kept separate | do not call sampled separation an all-contour or analytic error bound |
| Dimensionless registry | focused 20/20 PASS | syntax/manual-heuristic evidence with explicit backend | do not call syntax-only checks symbolic proofs |
| Retired parents | predecessor P0-A–D | edge-only coercivity, skew-neutrality, loop-forced 4–6, oblique concentration are false | no threshold, basis, dataset, or wording change may reactivate them |
| Empirical bridge | predecessor completion audit `INCOMPLETE` | neural manifolds and state-dependent connectivity are compatibility evidence only | no reuse of burned BA-SELF1/2/3 or closed CCEP/Allen confirmation material |

## 3. Mathematical candidate M1 — unbounded history/domain closure

Let

$$
\mathcal H=H_0\oplus\bigoplus_e L^2_{\rho_e}(( -\infty,0],\mathbb R^{q_e}),
\qquad \rho_e(s)=e^{2\alpha_es},\quad \alpha_e>0.
$$

The candidate zero-boundary history generator is

$$
(G_eh)(s)=\partial_sh(s),\qquad
D(G_e)=\{h\in W^{1,2}_{\rho_e}:h(0)=0\}.
$$

The math lane must prove or refute dense definition, closedness, the exact
$C_0$ shift semigroup and its norm, and distinguish this zero-fill forgetting
semigroup from a coupled delay equation whose boundary is supplied by the node
state. It must give a complete counterexample to any unjustified boundary or
sign convention.

For possibly unbounded closed edge operators $D_e$, define the quadratic-form
candidate on a common dense domain $V$:

$$
a_x^{(b)}(u,v)=a_{0,x}(u,v)+
\sum_e b_e\langle K_e(x)^{1/2}D_eu,K_e(x)^{1/2}D_ev\rangle.
$$

The lane must state sufficient closed-form, lower-bound, summability and
smoothness hypotheses; apply the representation theorem only under those
hypotheses; and classify the result correctly. An unbounded represented
operator is not a strong Riemannian metric on the ambient $\mathcal H$ merely
because its form is coercive. A strong metric claim is allowed only on a model
space whose norm is equivalent to the form norm, or after a bounded transform.

## 4. Mathematical candidate M2 — rigorous finite circle certificate

For $U\in\mathbb C^{n\times n}$ and
$\Gamma=\{c+re^{i\theta}\}$, freeze $N\ge4$ equispaced nodes and

$$
\widehat\delta_N=
\min_k\sigma_{\min}(z_kI-U)-2r\sin\frac{\pi}{2N}.
$$

The candidate theorem is that $\widehat\delta_N>0$ certifies

$$
\inf_{z\in\Gamma}\sigma_{\min}(zI-U)\ge\widehat\delta_N,
\qquad R_\Gamma\le\widehat\delta_N^{-1},
$$

using the 1-Lipschitz property of $\sigma_{\min}$ and the nearest-node chord.
The lane must verify the chord factor, complex matrix norm convention, floating
roundoff ceiling, and whether interval/verified arithmetic is required before
the word “rigorous” is used in executable output.

For an analytic strip width $a>0$, the inner and outer circles have radii
$r_- = re^{-a}$ and $r_+=re^a$. If both boundary circles receive positive
full-circle lower certificates and the annulus contains no spectrum, candidate

$$
M_a\le\max\left\{\frac{r_-}{\delta_-},
\frac{r_+}{\delta_+}\right\},
\qquad
\|P_N-P\|\le\frac{2M_a}{e^{aN}-1}.
$$

The lane must prove or refute the annulus/maximum-principle step, both radius
factors, and the Fourier-aliasing constant. It must retain adverse cases:
contour crossing, negative sampled lower bound, high pseudospectral resolvent,
annulus spectrum, coarse $N$, and floating underestimation.

## 5. BIO_STARTING_MECHANISM and candidate E1

Before any data access the source lane must verify a primary-source finite
population baseline of the form

$$
dx_t=F_{\rm bio}(x_t,u_t;\theta_{\rm bio})dt+G(x_t)dW_t,
$$

where the admissible specialization is a state-conditioned linear stochastic
or point-process population model with recurrent coupling, finite conduction
or binning delay, and no Dale-law violation. The exact equation, units,
timescale and primary source are `UNVERIFIED_PENDING_SOURCE`; therefore no
empirical scoring implementation is admitted at contract time.

The single CE addition under consideration is a causal history term

$$
\Delta F_{\rm CE}(t)=
\sum_e\int_{-T_h}^{0}\kappa_e(-s)C_eh_e(t,s)\,ds,
$$

with fixed kernel family, finite $T_h$, gauge normalization, and parameter
count below the independent held-out constraints. This is `[경험식 후보]`, not
an established biological primitive. The matched baseline is the same
$F_{\rm bio}$ with the history term removed; matched alternatives include a
same-DOF finite autoregression and shuffled-history control.

## 6. MEASUREMENT_MODEL

The preferred source candidate is an official public Neuropixels/electrophysiology
dataset with repeated state/task epochs and stable unit metadata. The source
lane must verify its DOI or official repository, version, subject/session
structure, intervention status, sampling clock and preprocessing provenance.
The frozen generic observation equation is

$$
y_{ik}\mid x_i(t_k)\sim
\operatorname{CountModel}\!\left(\Delta t\,\lambda_i(x(t_k));\psi_i\right),
$$

followed by a source-justified binning and covariance estimator. Gaussian,
Poisson or negative-binomial choice remains `UNVERIFIED_PENDING_SOURCE`; it
may not be chosen from endpoint performance. Calcium/fMRI data are rejected
for this contract unless a new measurement model and acquisition kernel are
frozen before access.

## 7. DATA_PROVENANCE and DATA_SPLIT

- Primary candidate: official Allen Institute Neuropixels/Visual Coding
  electrophysiology used by a primary recurrence–dimensionality analysis.
- Official cache schema family and manifest-format version `0.2.1` are source
  verified. Exact cache manifest bytes, NWB release generation, license/data-use
  receipt, checksum and inclusion criteria remain `UNVERIFIED_PENDING_METADATA`.
- No bytes are opened in contract, source, math or audit stages.
- After source verification, split by entire subject/session, never random
  time bins: calibration 50%, development 25%, held-out 25%, with exact IDs
  frozen before endpoint construction.
- `NONOVERLAP_VERIFIED_AT_DATASET_FAMILY_NAMESPACE`: the predecessor's closed
  Allen material is ex-vivo `aisynphys` Synaptic Physiology in the
  slice/experiment/cell/pair namespace; E1 is in-vivo Visual Coding
  Neuropixels in the subject/session/probe/unit namespace. Cross-resource
  numeric ID comparison is semantically invalid, not a leakage test.
- Previously burned BA-SELF1/2/3 and closed CCEP material remain excluded.
  Exact eligible E1 subject/session IDs and their within-resource split remain
  `UNVERIFIED_PENDING_METADATA` and must be frozen before endpoint access.

## 8. OBSERVABLES

All observables are dimensionless or explicitly normalized before fitting:

$$
D_{\rm PR}=\frac{(\operatorname{tr}C)^2}{\operatorname{tr}(C^2)},
\qquad
I_{a,d}=\frac{\|Q^{\rm post}_{a,d}-Q^{\rm pre}_{a,d}\|_F^2}{\max(1,d)},
$$

plus held-out point-process/log-likelihood improvement per observation,
history-ablation loss, full-contour certificate status and the complete frozen
rank menu. Covariance debiasing, neuron-count extrapolation and uncertainty
estimator must be source-locked. No observable is called consciousness.

## 9. RESIDUAL_RULE, FALSIFIER and controls

- Baseline must first reproduce source-declared count, covariance and
  dimensionality controls. Failure closes the apparatus before CE fitting.
- CE is retained only if subject/session-held-out predictive improvement over
  every matched control exceeds the predeclared uncertainty criterion and
  disappears under history ablation.
- No menu winner, unstable contour/rank, nonpositive full-circle certificate,
  failure under shuffled-history or same-DOF autoregressive control, or loss
  under an independent session yields `CE_HISTORY_SUBSPACE_NOT_IDENTIFIED`.
- A result confined to one estimator, bin width or unit subsample yields
  `MEASUREMENT_DEPENDENT_ONLY`, not a biological claim.
- Full-contour or analytic certificate failure yields
  `NONNORMAL_RIESZ_NOT_CERTIFIED` without changing thresholds.

## 10. MODEL_SELECTION

Freeze nuisance regressors, kernel family, $T_h$, rank menu, contour family,
bin width menu and covariance estimator in development only. Compare models
with held-out proper score and a complexity penalty that counts the entire
menu. Require structural rank of the sensitivity/design matrix and report its
smallest singular value. Parameters not separately identifiable are reported
only as gauge-equivalence classes. Confirmation is one-shot.

## 11. REVISION_TRIGGER

Use D→I→P→C→B→T. Only a T residual after the first five classes are rejected
permits one structural equation change in a new run. Tolerance, endpoint,
seed, split, contour, rank cutoff, bin width and exclusion rules are immutable
after access. A source or measurement prerequisite failure narrows the route;
it is not repaired with synthetic data.

## 12. CLAIM_CEILING and stop conditions

- M1/M2 may reach conditional theorem status after independent math audit.
- Executable M2 may reach verified-finite-arithmetic only if outward rounding
  or an equivalent enclosure is actually implemented; ordinary float64 output
  remains a numerical lower-bound estimate.
- E1 begins below L1 while provenance and baseline are unverified. If source
  lock succeeds and held-out observational prediction is later run, its maximum
  is L3 compatibility. No observational result reaches L4 mechanism identity.
- The run never establishes a whole-brain geometry, consciousness, selfhood,
  or $d=4$–$6$.
- Implementation is forbidden before source and math gates verify the inputs
  relevant to that implementation.

## 13. Candidate ordering and rejected routes

1. M1 is first because it closes a mathematical domain error independent of
   data or optional packages.
2. M2 is second because it upgrades the existing finite seam with an adverse,
   falsifiable full-contour certificate.
3. E1 is third because public spike data can in principle connect recurrence,
   history and observed dimensionality, but only after provenance and
   measurement lock.
4. Human propofol/fMRI is rejected for this run: hemodynamic convolution and
   unresponsiveness-versus-consciousness ambiguity require a distinct contract.
5. Closed CCEP D3 and burned BA-SELF material are rejected by predecessor stop
   conditions.
6. Any direct “4–6 consciousness dimension” fit is rejected because it lacks
   an identified endpoint and would reuse the number as a target.
