# Research contract

Status: COMPLETE

PREDECESSOR: `_workspace/ce/brain-quantitative-triangular-c3-graph-transform-20260825`

## Objective

Derive, falsify, implement, and document the exact affine triangular C4 graph
transform: the fourth-order class bound, the five-layer two-graph recurrence,
the necessary D5-level fiber modulus, strict fourth-order bunching, exact
iteration, lower-order reduction, and equality counterexample.

## Predecessor evidence

| Result | Evidence | Status | Preserved claim | Retry prohibition |
|---|---|---|---|---|
| Affine triangular C3 | predecessor `11-math.md`, `31-validation.md`, `40-final-report.md` | PASS | Exact C0--C3 class and four-layer recurrence | Do not change its coefficients or weaken strict $q\mu^3<1$. |
| C3 equality boundary | predecessor $h_c=c|x|^3$ witness | PASS | Equality cannot force C3 | Do not reuse it as a C4 witness because $|x|^4=x^4$ is smooth. |

## Frozen definitions and claims

Let $H_h=(I,h)$ and $S_h=Bh+g\circ H_h$. Assume the predecessor C3
certificate, $\|D^4h\|\le\Lambda_4$, a normalized map bound
$K_4\ge\|D^4g\|$, and a fiber Lipschitz modulus $K_5$ for $D^4g$.

1. The exact fourth chain rule has partition coefficients $1,4,3,6,1$.
2. The C4 class output is

$$
\Lambda_{4,\mathrm{out}}=\mu^4\{q\Lambda_4
+4K_2\Lambda_3r+3K_2\Lambda_2^2
+6K_3\Lambda_2r^2+K_4r^4\},\qquad r=1+\kappa.
$$

3. The two-graph recurrence is

$$
j'\le\beta_4j+c_{43}f+c_{42}e+c_{41}d+c_{40}\delta,
\qquad \beta_4=q\mu^4,
$$

with every cross coefficient derived by slotwise telescoping.
4. Strict $q\mu^4<1$ is required. At equality, $h_c(x)=cx|x|^3$ is an
   invariant C3/non-C4 family for $x'=x/2$, $y'=y/16$.
5. $K_5$ affects only the value-to-fourth-derivative comparison coefficient;
   omitting it invalidates the two-graph C4 convergence claim.
6. Input dimension is preserved, never selected.

## Frozen candidate routes

- selected: exact fourth-order Faà di Bruno partition plus slotwise difference;
- reject unless exact reduction succeeds: extrapolating C3 coefficients;
- reject unless it controls two graph values: using $K_4$ without $K_5$;
- defer: coupled, nonaffine, local/matched C4 and arbitrary-order induction.

## Brain/empirical fields

`BIO_STARTING_MECHANISM`, `CE_DELTA`, `MEASUREMENT_MODEL`, `DATA_PROVENANCE`,
`DATA_SPLIT`, `OBSERVABLES`, `RESIDUAL_RULE`, `FALSIFIER`, `MATCHED_CONTROLS`,
`MODEL_SELECTION`, and `REVISION_TRIGGER` are not applicable because this run
uses no biological or observational claim. `CLAIM_CEILING` is a conditional
finite-dimensional mathematical theorem and exact software certificate only.

## Validation contract

Use exact rational fixtures, a programmatic partition audit, lower-order
predecessor identity, the equality witness, invalid-input controls,
dimensionless checks, and the adjacent affine triangular C0--C4 chain. No full
suite, benchmark, network, data analysis, dependency install, or physical
interpretation is authorized.
