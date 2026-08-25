# Successor routes — history, certified spectra, and an empirical bridge

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-history-riesz-empirical-bridge-20260825`

These are pre-data route specifications.  They retain the predecessor stops:
no edge-only coercivity, skew-neutrality, topology claim from a weight, fixed
rank 4--6, oblique concentration, or consciousness conclusion.

## R1 — boundary-coupled history versus zero-fill null

Target: distinguish a source-locked node-plus-history model

$$
\dot x=F(x,u)+Lh,\qquad \partial_th=\partial_sh,\qquad h(t,0)=Bx(t),
$$

from the zero-fill null $h(t,0)=0$, using a finite causal kernel/readout fixed
before data.  Estimate held-out proper-score difference and boundary-trace
residual.  Degrees of freedom: the declared kernel basis, $B,L$, node
nuisance parameters, delay/bin menu, and all ranks; parameters are counted
after the stated scaling gauge.  A sufficient local identifiability condition
is full column rank of the held-out-calibration sensitivity matrix modulo that
gauge, with a frozen positive smallest-singular-value threshold.

Controls: same-DOF finite autoregression, shuffled history, and the zero-fill
semigroup.  Exact falsifier: failed trace compatibility, rank-deficient
sensitivity, or no session-held-out gain over every matched control yields
`COUPLED_HISTORY_NOT_IDENTIFIED`.  It tests a causal model distinction, not a
brain metric or consciousness.

## R2 — verified finite contour/Riesz route

Freeze a finite transition $U$, units, circle family, $N$, reference scale,
and an outward-rounded arithmetic library.  Compute lower enclosures at every
node and the upper chord subtraction

$$
\underline\delta_N=
\min_k\underline\sigma_{\min}(z_kI-U)-
\overline{2r\sin(\pi/(2N))}.
$$

If required, repeat on radii $re^{-a}$ and $re^a$ and certify the annulus by a
separate eigenvalue/resolvent enclosure.  Estimands: $\underline\delta_N$,
$\overline R_\Gamma$, verified rank enclosure, and the analytic trapezoid
bound.  Degrees of freedom are contour/radius menu, $N$, $a$, reference scale,
rank tolerance, enclosure method, and all precision settings, frozen before
the matrix is inspected.  A sufficient stability condition is
$\overline R_\Gamma\|E\|<1$.

Controls: normal matrix with known projection; oblique diagonalizable matrix;
contour-crossing, annulus-spectrum, coarse-$N$, and high-pseudospectral-norm
adversaries.  Exact falsifier: any nonpositive verified lower bound, missing
annulus proof, rank ambiguity, or failed residual/perturbation inequality gives
`NONNORMAL_RIESZ_NOT_CERTIFIED`.  Float64-only output is a separate numerical
estimate and cannot pass this route as verified arithmetic.

## R3 — source-locked empirical history bridge (E1)

Only after a primary source locks population equation, dataset version,
session IDs, sampling clock, count model, preprocessing, and subject/session
split, compare the common biological baseline

$$
dx_t=F_{\rm bio}(x_t,u_t;\theta_{\rm bio})dt+G(x_t)dW_t
$$

with the sole CE candidate

$$
\Delta F_{\rm CE}(t)=\sum_e\int_{-T_h}^0\kappa_e(-s)C_eh_e(t,s)ds.
$$

Estimand: session-held-out proper-score improvement per observation, with
history-ablation loss and predeclared covariance/rank summaries.  Degrees of
freedom include biological parameters, CE kernel basis and $C_e$, $T_h$,
bin/covariance/rank menus, nuisance regressors, and count-model parameters;
the complete menu enters the penalty.  Sufficient local parameter
identifiability is full structural rank of the calibrated sensitivity matrix
after fixed kernel-scale gauge, plus independent sessions exceeding parameter
constraints.

Controls: identical baseline without history, same-DOF autoregression,
shuffled-history, and matched nuisance-only model.  Exact falsifier: baseline
apparatus failure; no held-out advantage over every control; no ablation loss;
or a rank-deficient design gives `CE_HISTORY_SUBSPACE_NOT_IDENTIFIED`.  A
single-estimator/bin/subsample finding is only `MEASUREMENT_DEPENDENT_ONLY`.
Even a pass is observational compatibility capped at L3, never mechanism
identity, whole-brain geometry, consciousness, or a dimension choice.

## R4 — form-scale regularity route

Target: an explicitly declared common form space $V$ and bounded-transform
alternative to an unbounded edge form.  Estimate the form-norm continuity
residual of $a_x^{(b)}$ under frozen perturbations and the spectral lower
bound; if a strong ambient metric is desired, separately estimate a finite
upper bound for the transformed operator.  Degrees of freedom: form-domain
choice, baseline, edge family, summability weights, transform, and local
parameter neighborhood.  A sufficient mathematical condition is completeness
of the declared form norm and locally uniform summable form bounds.

Controls: bounded-edge model, derivative/unbounded-edge model, and a
deliberately domain-incompatible edge family.  Exact falsifier: non-dense or
incomplete common domain, failed lower bound, divergent edge sum, or absence
of an ambient upper bound yields `FORM_SCALE_NOT_CLOSED`; it forbids the strong
ambient metric wording rather than changing the counterexample.

## Cross-route safeguards

All empirical choices remain unavailable while the contract's source and
measurement fields are `UNVERIFIED_PENDING_SOURCE`.  Full sessions, not time
bins, are split; confirmation is one-shot; contour/rank/bin/precision changes
after access are prohibited.  Algebraic or numerical certificates do not
substitute for empirical provenance, and empirical fit never reopens the
predecessor P0 parents.
