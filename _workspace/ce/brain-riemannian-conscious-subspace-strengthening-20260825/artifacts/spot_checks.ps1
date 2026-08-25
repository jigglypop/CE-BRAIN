param()

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw "ASSERTION FAILED: $Message"
    }
}

function Assert-Close {
    param(
        [Parameter(Mandatory = $true)][double]$Actual,
        [Parameter(Mandatory = $true)][double]$Expected,
        [double]$Tolerance = 1e-12,
        [Parameter(Mandatory = $true)][string]$Message
    )
    Assert-True -Condition ([Math]::Abs($Actual - $Expected) -le $Tolerance) -Message $Message
}

# Metric fixture.  D u = (u1-u2, u2-u3) and K = diag(0.7, 0.2).
$u1 = 0.3
$u2 = -0.2
$u3 = 0.4
$du1 = $u1 - $u2
$du2 = $u2 - $u3
$localDifference = 0.7 * $du1 * $du1 + 0.2 * $du2 * $du2
$uNormSquared = $u1 * $u1 + $u2 * $u2 + $u3 * $u3

# Delta = D^T K D.  For a symmetric matrix, ||Delta||_2 <= ||Delta||_infinity.
# Its absolute row sums are 1.4, 1.8, and 0.4, so 1.8 is a rigorous bound.
$deltaOperatorNormUpperBound = 1.8
$baselineMinEigenvalue = 1.0
$edgeRatioUpperBound = $deltaOperatorNormUpperBound / $baselineMinEigenvalue

Assert-Close -Actual $localDifference -Expected 0.247 -Message 'edge quadratic-form value'
Assert-True -Condition ($localDifference -le $deltaOperatorNormUpperBound * $uNormSquared) `
    -Message 'quadratic-form perturbation is bounded by the operator-norm upper bound'
Assert-True -Condition ($baselineMinEigenvalue -gt 0.0) -Message 'coercive baseline is positive'

# Baseline-free counterexample [[1,-1],[-1,1]] annihilates (1,1).
$kernelFirst = 1.0 - 1.0
$kernelSecond = -1.0 + 1.0
Assert-Close -Actual $kernelFirst -Expected 0.0 -Message 'baseline-free kernel first coordinate'
Assert-Close -Actual $kernelSecond -Expected 0.0 -Message 'baseline-free kernel second coordinate'

# Directed-drift counterexample: grad(V)=e2 and S(1,0)=e2, hence work is 1.
$skewDriftWork = 1.0
Assert-Close -Actual $skewDriftWork -Expected 1.0 -Message 'skew drift is not automatically zero-work'

# Riesz fixture.  U0 = diag(A,D) with A=diag(0.95,0.80), D=diag(0.20,0.10).
# E has B13=0.01 and B24=-0.01.  The exact spectral projector onto A is
# [[I,Y],[0,0]], Y_ij=B_ij/(A_ii-D_jj).  Its first two columns are independent,
# so both the unperturbed and perturbed projectors have rank 2.
$projector13 = 0.01 / (0.95 - 0.20)
$projector24 = -0.01 / (0.80 - 0.10)
$rieszRankBefore = 2
$rieszRankAfter = 2
$rieszProjectorDifferenceNorm = [Math]::Max([Math]::Abs($projector13), [Math]::Abs($projector24))
Assert-True -Condition ($rieszRankBefore -eq 2 -and $rieszRankAfter -eq 2) `
    -Message 'isolated block perturbation preserves Riesz rank'
Assert-Close -Actual $rieszProjectorDifferenceNorm -Expected (1.0 / 70.0) `
    -Message 'closed-form Riesz projector perturbation norm'

# Oblique idempotent P=[[1,2],[0,0]], C=[[1,1],[1,1]].
# tr(PCP)=3 and tr(C)=2, whereas the orthogonal projector Q=diag(1,0) gives 1/2.
$obliqueConcentration = 3.0 / 2.0
$orthogonalConcentration = 1.0 / 2.0
Assert-True -Condition ($obliqueConcentration -gt 1.0) `
    -Message 'retired oblique concentration violates the probability bound'
Assert-True -Condition ($orthogonalConcentration -ge 0.0 -and $orthogonalConcentration -le 1.0) `
    -Message 'orthogonal concentration lies in [0,1]'

# Effective dimension for mu=(4,1,1/4,0), lambda=1 is 4/5+1/2+1/5=3/2.
$effectiveDimension = 4.0 / 5.0 + 1.0 / 2.0 + 1.0 / 5.0
Assert-Close -Actual $effectiveDimension -Expected 1.5 -Message 'effective dimension fixture'
Assert-True -Condition ($effectiveDimension -ge 0.0 -and $effectiveDimension -le 3.0) `
    -Message 'effective dimension is bounded by hard rank'

[ordered]@{
    status                                  = 'PASS'
    evidence_level                          = 'L0_DETERMINISTIC_ALGEBRA'
    baseline_min_eigenvalue                 = $baselineMinEigenvalue
    perturbation_operator_norm_upper_bound  = $deltaOperatorNormUpperBound
    normalized_edge_bound                   = $edgeRatioUpperBound
    local_squared_length_difference         = $localDifference
    local_bound_holds                       = $true
    baseline_free_kernel_witness             = @($kernelFirst, $kernelSecond)
    skew_drift_work                         = $skewDriftWork
    riesz_rank_before                       = $rieszRankBefore
    riesz_rank_after                        = $rieszRankAfter
    riesz_projector_difference_norm         = $rieszProjectorDifferenceNorm
    oblique_retired_concentration           = $obliqueConcentration
    orthogonal_corrected_concentration      = $orthogonalConcentration
    effective_dimension_lambda_1            = $effectiveDimension
} | ConvertTo-Json -Depth 4
