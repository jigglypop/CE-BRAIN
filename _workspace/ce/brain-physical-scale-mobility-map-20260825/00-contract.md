# Physical scale and mobility-map contract

Status: COMPLETE

Date: 2026-08-25

PREDECESSOR: `_workspace/ce/brain-quantitative-nonlinear-graph-transform-20260825`

## 1. Objective and exact boundary

This light successor closes the algebraic part of the predecessor's physical-scale gap. It preserves an arbitrary declared scalar physical mobility instead of choosing the special value that makes the normalized coefficient one. It also converts a certified per-window contraction factor into a rigorously enclosed physical decay-rate bound once a positive physical time scale is supplied.

No neural state unit, energy scale, biological mobility, window duration, or empirical contraction factor is measured in this run. A positive output is a scale-map certificate for supplied exact inputs, not a biological calibration.

## 2. Predecessor evidence

| Result | Evidence | State | Preserved narrow claim | No-retry condition |
|---|---|---|---|---|
| Triangular graph contraction | predecessor `11-math.md`, G1--G2; `31-validation.md`; `40-final-report.md` | PASS | For declared uniform constants, distance is bounded by $q^n$ with $0\le q<1$. | Do not reinterpret window count as seconds without a time map. |
| Physical scale warning | predecessor `12-routes.md`, CE-GRAPH-002 ledger row | PASS | The missing physical time map is explicitly isolated. | Do not fit or invent a biological duration in this algebraic run. |
| Dimension nonselection | predecessor `40-final-report.md` | PASS | The graph theorem preserves any supplied positive base dimension. | Do not use the scale map to select 4--6 or identify consciousness. |

## 3. Frozen homogeneous-coordinate model

Use one homogeneous state unit and positive reference scales

$$
x=X_0\widetilde x,\qquad
\mathcal V=V_0\widetilde{\mathcal V},\qquad
t=t_0\tau,
$$

with a scalar physical mobility $\mu_{\rm phys}>0$ having unit
$[x]^2/([\mathcal V][t])$. For the pure metric-gradient term

$$
\frac{dx}{dt}=-\mu_{\rm phys}A^{-1}\nabla_x\mathcal V,
$$

the normalized mobility is

$$
\widetilde\mu
=\frac{\mu_{\rm phys}V_0t_0}{X_0^2},
\qquad
\frac{d\widetilde x}{d\tau}
=-\widetilde\mu A^{-1}\nabla_{\widetilde x}\widetilde{\mathcal V}.
\tag{S1}
$$

All executable inputs are exact integers, `Fraction`, or canonical rational strings. Booleans, floats, nonpositive scales/mobility/window, noncanonical strings, invalid contraction factors, and invalid series depth fail closed.

## 4. Physical rate scales

For a positive dimensionless window width $\Delta\tau$, define

$$
\Delta t=t_0\Delta\tau,\qquad
v_0=\frac{X_0}{t_0},\qquad
P_0=\frac{V_0}{t_0}.
\tag{S2}
$$

If $\|A^{-1}\nabla\widetilde{\mathcal V}\|\le G$ is a supplied dimensionless bound, then the gradient term satisfies

$$
\left\|\frac{dx}{dt}\right\|
\le v_0\widetilde\mu G.
\tag{S3}
$$

In the Euclidean $A=I$ subcase, the physical potential dissipation obeys

$$
-\frac{d\mathcal V}{dt}
=P_0\widetilde\mu
\|\nabla_{\widetilde x}\widetilde{\mathcal V}\|^2,
\tag{S4}
$$

so a supplied gradient-norm upper bound gives
$-d\mathcal V/dt\le P_0\widetilde\mu G^2$. For general $A$, (S4) must use the $A^{-1}$ quadratic form; the scalar Euclidean executable bound must not be advertised as that general case.

## 5. Exact contraction-to-rate enclosure

For $0<q<1$ and physical window $\Delta t$, define

$$
\gamma=-\frac{\log q}{\Delta t}.
\tag{S5}
$$

Then $q^n=e^{-\gamma n\Delta t}$. Put $z=(1-q)/(1+q)\in(0,1)$ and, for integer $N\ge1$,

$$
L_N=2\sum_{k=0}^{N-1}\frac{z^{2k+1}}{2k+1},\qquad
U_N=L_N+
\frac{2z^{2N+1}}{(2N+1)(1-z^2)}.
\tag{S6}
$$

The executable certificate must return the exact rational enclosure

$$
\frac{L_N}{\Delta t}
\le\gamma\le
\frac{U_N}{\Delta t}.
\tag{S7}
$$

The $q=0$ boundary means the bound is exactly zero after one window and has no finite logarithmic rate. The $q=1$ boundary certifies no positive decay rate. These cases receive distinct statuses; neither is sent through the logarithm.

## 6. Required controls

- exact normalization with a non-unit mobility;
- recovery of the predecessor's special $\widetilde\mu=1$ choice;
- independent common unit rescalings that preserve normalized outputs;
- exact physical window, speed scale, power scale, speed upper, and Euclidean dissipation upper;
- $0<q<1$ log enclosure containing a trusted numerical value only as a test oracle;
- enclosure width decreasing with series depth;
- separate $q=0$ finite-window and $q=1$ no-positive-rate boundaries;
- invalid exactness, sign, contraction, and series-depth controls;
- dimensionless-registry verification of (S1)--(S7).

## 7. Claim ceiling

This run may establish a conditional algebraic theorem and exact rational apparatus for a homogeneous scalar state unit. It does not calibrate volts, currents, spikes, metabolic energy, or seconds; identify the model potential with physical/metabolic energy; handle mixed-unit state vectors or a general mobility tensor; prove that a neural trajectory satisfies the graph-transform premises; identify consciousness; or select dimension 4--6.

