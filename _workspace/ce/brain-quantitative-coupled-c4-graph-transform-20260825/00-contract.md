# Research contract

Status: COMPLETE

PREDECESSOR:
- `_workspace/ce/brain-quantitative-coupled-c3-graph-transform-20260825`
- `_workspace/ce/brain-quantitative-triangular-c4-graph-transform-20260825`

## Objective

Close the affine graph-dependent coupled-base C4 graph transform by deriving
the modified fourth tensor, the C4 and conditional C4,1 graph classes, every
coefficient of the five-layer recurrence, exact triangular reduction, and the
sharp fourth-order bunching boundary.

## Predecessor evidence

| Result | Evidence | Status | Preserved claim | Retry prohibition |
|---|---|---|---|---|
| Coupled C3 | predecessor `12-routes.md`, `31-validation.md`, `40-final-report.md` | PASS | Exact $T,N,M$ tensors, C3/C3,1 classes and four-layer recurrence | Do not discard inverse-Jacobian, modified-Hessian, or graph-dependent preimage terms. |
| Triangular C4 | predecessor `11-math.md`, `31-validation.md`, `40-final-report.md` | PASS | Exact partition coefficients, $K_5$ requirement and equality witness | Coupled formulas must reduce coefficient-by-coefficient at zero base coupling/nonlinearity. |

## Frozen identity

For $Y_h=(\mathcal Th)\circ F_h$, define

$$
J=DF_h,\ P=D^2F_h,\ U=D^3F_h,\ W=D^4F_h,
$$

$$
K=DY_h,\ R=D^2Y_h,\ V=D^3Y_h,\ Z=D^4Y_h,
$$

$L=J^{-1}$ and use the predecessor tensors $T=KL$, $N=R-TP$ and
$M=V-TU-3N[LP,\cdot]$. Freeze

$$
O=Z-TW-4N[LU,\cdot]-3N[LP,LP]-6M[LP,\cdot,\cdot],
$$

$$
D^4(\mathcal Th)=O[L,L,L,L].
$$

## Frozen claims and falsifiers

1. Finite D4 map bounds and $\Lambda_4$ give explicit $C_W,C_Z,C_O$ and
   $\Lambda_{4,\mathrm{out}}=C_O/\alpha^4$.
2. When graph height affects the base, D5-level map moduli and graph C4,1
   radius $\Xi_4$ are required; otherwise the C4,1 gate is bypassed exactly.
3. Differences of $J,P,U,T,N,M,W,Z$ are composed as nonnegative coefficient
   vectors over $(j,f,e,d,\delta)$. No cross term may be discarded.
4. The diagonal factor is $\beta_{4,c}=Q/\alpha^4$ and must be strict.
5. Zero base coupling and zero base nonlinear derivative bounds reduce the
   complete certificate and iteration coefficients to triangular C4.
6. $Q/\alpha^4=1$ retains the $cx|x|^3$ C3/non-C4 invariant family.
7. Any failed scalar fourth-chain-rule identity, reduction coefficient,
   dimension covariance, or predecessor gate kills the route.

## Brain/empirical ceiling

All real-brain discovery fields are not applicable because this is abstract
conditional mathematics with no data or biological claim. The claim ceiling
excludes neural calibration, consciousness, and selection of dimension 4--6.

## Validation

Use an independent scalar jet identity, exact rational coefficient-vector
audit, exact triangular reduction, focused failures/bypass/equality tests,
dimensionless checks, and adjacent triangular/coupled C0--C4 regression. Do
not run the full suite, network, benchmarks, empirical analysis, installs, or
irreversible stages.
