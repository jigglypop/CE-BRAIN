# Successor routes — independent tests of open hypotheses

Status: COMPLETE

CE_RUN: `_workspace/ce/brain-riemannian-conscious-subspace-strengthening-20260825`

No empirical dataset is opened here. These are frozen route specifications, not results; they preserve every predecessor stop and every P0 retirement in `11-math.md`.

## R1 — gauge-fixed active finite-family metric identification

Declare a finite family $A(\theta)=A_{\rm ref}+\sum_{j=1}^p\theta_jB_j\succeq mI$, with linearly independent symmetric $B_j$ after all scale/basis gauges are fixed. Under known intervention directions $v_l$, use the response design

$$
H_{lj}=\langle v_l,B_jv_l\rangle,\qquad y_l=\langle v_l,A(\theta)v_l\rangle+\varepsilon_l.
$$

Estimand: gauge-fixed $\theta$ and held-out quadratic-response residual $r_l=y_l-\langle v_l,A(\widehat\theta)v_l\rangle$. Degrees of freedom are $p$ after subtracting fixed gauges; an unrestricted $q\times q$ symmetric family starts at $q(q+1)/2$. A sufficient noiseless local-identifiability condition is $\operatorname{rank}H=p$; with noise, stability is controlled by $\sigma_{\min}(H)>0$ and the frozen condition-number threshold. Freeze directions, time, noise model, family, and holdout split before access.

Controls: equal-DOF diagonal/isotropic family, wrong directions, shuffled direction-response pairing. Exact falsifier: $\sigma_{\min}(H)=0$, loss of $A\succeq mI$, or prespecified held-out residual not lower than all controls gives `METRIC_FAMILY_NOT_IDENTIFIED`. This does not identify an arbitrary ambient metric or claim complete tomography.

## R2 — recurrent-selective variable-rank subspace

For each frozen real rank in

$$
d\in\{1,2,3,4,5,6,8,10,12\},
$$

form the conjugation-correct real projector convention of `11-math.md`. With matched recurrent $R$ and feedforward $F$ interventions, define normalized projector instability

$$
I_{a,d}=\frac{\|Q^{\rm post}_{a,d}-Q^{\rm pre}_{a,d}\|_F^2}{\max(1,d)},\qquad
\Delta_d=\mathbb E[I_{R,d}-I_{F,d}].
$$

Estimand: held-out $\Delta_d$ and held-out predictive score for that $d$, with residuals fixed by the same nuisance model in both arms. A sufficient mathematical stability condition for each projector is the resolvent-gap condition $R\|E\|<1$ from Theorem 4; it is not evidence that the condition holds empirically. Degrees of freedom are the entire nine-member menu plus frozen nuisance parameters. Apply the complete menu penalty, e.g. select only if the best candidate exceeds every alternative by held-out $\Delta\mathrm{ELPD}>2SE$ under the declared multiplicity procedure.

Controls: amplitude/duration/quality matched feedforward arm, time-shuffled stimulus, and dimension-free recurrent latent model. Exact falsifier: no positive held-out difference-in-differences beyond the frozen uncertainty criterion, gap failure, or no menu-penalized winner gives `LOOP_SELECTION_NOT_IDENTIFIED`. A rank-4 winner would remain an observed candidate subspace, not consciousness dimension.

## R3 — passive quotient prediction with blind-tail ceiling

Use only the observed pullback $G^{\rm obs}=J^*WJ$ and a frozen regularized predictor

$$
\widehat y_{t+h}=f_{d,\lambda}(Q_{d,t}\widetilde y_{\le t},z_{\le t}),
$$

where $Q_{d,t}$ is selected only in development and $z$ is the predeclared nuisance vector. Estimand: held-out proper score difference against raw, PCA/CCA, and random-projection predictors with matched feature and parameter budgets; residual is the held-out forecast error under the frozen scoring rule. DOF include sensor scaling, $W$, $\lambda$, rank menu, horizon, nuisance parameters, and predictor parameters; all are nested-development choices.

The blind-tail ceiling is explicit: construct two ambient extensions with the same $J$, $W$, measured process, and therefore same $G^{\rm obs}$, but different unobserved kernel dynamics. They are observationally equivalent for this route. Thus no passive score can identify ambient metric, topology, or ambient dimension. Exact falsifier: no independent held-out gain over every matched control, or equality with blind-tail-equivalent control, gives `OBSERVED_QUOTIENT_NOT_USEFUL`; even a gain cannot exceed the quotient claim ceiling.

## R4 — adjacency indicators versus continuous metric deformation

For source-locked eligible edges define separately an adjacency indicator $a_e\in\{0,1\}$, availability $b_e\in[0,1]$, and continuous PSD operator $K_e(\eta_e)$:

$$
A(\eta,b,a)=A_0+\sum_e a_eb_eD_e^*K_e(\eta_e)D_e.
$$

Estimands are (i) graph reachability/shortest-path change from $a$, (ii) metric quadratic/length change from $b,K$, and (iii) their predeclared held-out dynamic residuals. Gauge: normalize each $K_e$ by a frozen reference norm or fix one of $b_e,K_e$; otherwise $b_eK_e$ has a multiplicative non-identifiability. DOF are $r$ binary indicators plus declared independent $b$ and $\eta$ parameters, after this gauge. Sufficient local separation requires a full-column-rank design/Jacobian for continuous parameters conditional on $a$, and nonidentical graph signatures for candidate $a$ patterns.

Controls: adjacency-only ($a$ changes; $b,K$ fixed), metric-only ($a$ fixed; $b,K$ change), matched operator-norm perturbation, and sham. Exact falsifier: rank-deficient continuous design, duplicated graph signatures, lost coercivity, or no held-out separation of adjacency-only from metric-only gives `TOPOLOGY_METRIC_SEAM_NOT_IDENTIFIED`. No outcome is called curvature, and this route does not reopen the killed CCEP D2 candidate.

## R5 — finite nonnormal contour-Riesz certificate

Target: a source-locked finite real transition matrix $U$ and a predeclared conjugation-closed contour family. For each circle $z_k=c+re^{2\pi ik/N}$, compute

$$
P_N=\frac1N\sum_{k=0}^{N-1}re^{2\pi ik/N}(z_kI-U)^{-1}.
$$

Estimands are the exact finite certificate vector: contour/eigenvalue enclosure margin (or explicitly only sampled margin), maximum sampled resolvent norm, $\|P_{2N}-P_N\|$, idempotence, commutator, realification singular values/rank, imaginary residual, and the orthogonal range projector $Q_N$. The Riesz object is $P$, not $P_N$; $Q_N$ is only the range projector for concentration.

Degrees of freedom: freeze circle/menu, $N$, contour enclosure method, rank tolerance, realification convention, and all residual thresholds before data. A sufficient exact-rank-stability condition is a certified full-contour $R_\Gamma$ satisfying $R_\Gamma\|E\|<1$ for the declared perturbation. A sufficient quadrature error bound needs a certified analytic strip and bound as in Theorem 10; sampled gaps and $N$-doubling alone are not sufficient.

Controls: normal matrix with known projector, oblique diagonalizable fixture, contour-crossing adverse case, high-pseudospectral-resolvent adversary, unpaired conjugate selection, and coarse-quadrature adversary. Exact falsifier: a contour enclosure failure, missing conjugate partner, unbounded/uncertified resolvent, failed residual/gap/rank certificate, or absence of analytic quadrature bound yields `NONNORMAL_RIESZ_NOT_CERTIFIED`. Passing this route is finite numerical/operator evidence only and cannot identify a brain subspace or consciousness dimension.

## Cross-route safeguards

Each route requires a new contract, primary-source provenance, independent heldout allocation, declared $F_{\rm bio}$, separate CE delta, measurement model, and frozen residual/multiplicity rule. L0 fixtures test algebra/software only. Allen validation/confirmation, CCEP D3, and sealed or failed material remain closed. A failure removes only its precise route parent claim.
