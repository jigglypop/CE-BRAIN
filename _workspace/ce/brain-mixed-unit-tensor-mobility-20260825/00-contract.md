# Mixed-unit tensor mobility contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-physical-scale-mobility-map-20260825`

## Objective

Extend the predecessor's homogeneous scalar mobility map to a finite state chart whose coordinates may have different physical units. Prove and implement the diagonal scale/tensor congruence, exact symmetry/positive-semidefinite gate, coordinate velocity, and model-potential dissipation.

No biological coordinate scale or tensor entry is supplied by this run.

## Predecessor evidence

| Result | Evidence | State | Preserved claim | No-retry condition |
|---|---|---|---|---|
| Scalar mobility map | predecessor M1--M4; focused 23/23 | PASS | $\widetilde\mu=\mu V_0t_0/X_0^2$ and physical rate scales are exact. | Recover on $n=1$. |
| Mixed-unit extension | predecessor `12-routes.md`; CE-SCALE dependency map | OPEN | General formula was noted but not typed or checked. | Do not treat heterogeneous coordinates as one scalar unit. |
| Physical calibration | predecessor ceiling | OPEN EMPIRICAL | Actual scales and energy interpretation are absent. | No biological defaults. |

## Frozen tensor model

Let $S=\operatorname{diag}(X_1,\ldots,X_n)$ with all $X_i>0$,
$\mathcal V=V_0\widetilde{\mathcal V}$, and $t=t_0\tau$. The physical mobility entry has unit

$$
[M_{ij}]=\frac{[x_i][x_j]}{[\mathcal V][t]}.
$$

For

$$
\dot x=-M_{\rm phys}\nabla_x\mathcal V,
\tag{T1}
$$

define

$$
\widetilde M
=V_0t_0S^{-1}M_{\rm phys}S^{-T}.
\tag{T2}
$$

Then every entry is dimensionless and

$$
\frac{d\widetilde x}{d\tau}
=-\widetilde M\nabla_{\widetilde x}\widetilde{\mathcal V}.
\tag{T3}
$$

## Exact PSD and pointwise output

Require an exact real rational symmetric matrix. A symmetric real matrix is PSD iff every principal minor is nonnegative. The apparatus must compute all nonempty principal minors exactly, report the first negative subset, and distinguish PSD from positive definite.

For a supplied exact dimensionless gradient $g$, compute

$$
\widetilde v=-\widetilde Mg,
\qquad
\dot x_i=\frac{X_i}{t_0}\widetilde v_i,
\tag{T4}
$$

and

$$
-\frac{d\mathcal V}{dt}
=\frac{V_0}{t_0}g^T\widetilde Mg\ge0.
\tag{T5}
$$

The inequality is admitted only after the PSD gate. A singular PSD tensor may have a zero-dissipation direction and is not labelled coercive.

## Controls and ceiling

Controls cover scalar recovery, heterogeneous diagonal and coupled tensors, exact PSD/PD, singular PSD, nonsymmetric and indefinite failures, zero and nonzero gradients, coordinate/energy/time unit covariance, invalid shapes/types/scales, and nonselection of dimension.

This is a declared finite tensor scale map. It does not identify voltage/current/spike coordinates, fit $M_{\rm phys}$, prove Onsager symmetry, identify the model potential with metabolic energy, include drift work, analyze a brain, identify consciousness, or select 4--6 dimensions.

