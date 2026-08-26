# Mathematics lane

Status: COMPLETE

## CMD.1 Distinct spectral summaries

For each independent session, use a cross-validated signal covariance spectrum
`lambda_i>=0`, not an uncorrected raw covariance spectrum.  Freeze

$$
d_{\rm PR}=\frac{(\sum_i\lambda_i)^2}{\sum_i\lambda_i^2},
$$

$$
d_{\rm ridge}(\gamma)=\sum_i\frac{\lambda_i}{\lambda_i+\gamma},
\qquad\gamma>0,
$$

$$
d_{\rm stable}=\frac{\sum_i\lambda_i}{\max_i\lambda_i},
\qquad
d_{\rm hard}(\tau)=\#\{i:\lambda_i>\tau\}.
$$

These are four different objects.  Agreement within a preregistered tolerance
is evidence of estimator stability, not an identity theorem.  Noise can
inflate all but especially raw hard/participation estimates, hence the signal-
spectrum gate.

## CMD.2 Complete-menu held-out selection

The complete menu is

$$\mathcal D=\{1,2,3,4,5,6,8,10,12\}.$$

For paired held-out fold scores `ell_(d,k)`, select the unique highest mean.
Against the unique runner-up, form

$$
\bar\Delta=K^{-1}\sum_k\Delta_k,
$$

$$
SE^2=\frac1{K(K-1)}\sum_k(\Delta_k-\bar\Delta)^2.
$$

The gate is evaluated exactly without a square root:

$$
\boxed{\bar\Delta>0\quad\text{and}\quad
\bar\Delta^2>4SE^2.}
$$

Apply it twice: to conscious-condition prediction, and to the paired score
contrast `conscious minus matched control`.  Both unique winners must be the
same.  This prevents a rank that predicts generic task structure equally well
in the control state from being labelled consciousness-associated.

## CMD.3 Multiplicity and decision rule

Permute the state labels and recompute the maximum statistic over the entire
frozen menu on every permutation.  With E exceedances among B permutations,
use the finite-sample correction

$$
p_{\max}^+=\frac{E+1}{B+1}.
$$

A supplied summary supports a candidate 4--6 neural signal rank only if:

1. both paired two-SE gates pass with the same unique winner;
2. the winner lies in 4--6;
3. every independent session has hard rank equal to the winner and PR,
   ridge, and stable dimensions within the frozen tolerance;
4. `p_max^+<=alpha` under max-over-menu permutation;
5. spectrum, split, provenance, and menu metadata match the contract.

For a rank-five equal signal spectrum the exact fixture gives

$$d_{\rm PR}=d_{\rm stable}=d_{\rm hard}=5,qquad
d_{\rm ridge}(1/10)=\frac{50}{11}.$$

## CMD.4 Interpretation ceiling and current result

The selected object is a rank of a cross-validated signal covariance or latent
predictive model for a specified recording, task, time window, and pipeline.
It is not automatically the intrinsic nonlinear manifold dimension, the
dimension of the full brain, the number of cortical gradients, the dimension
of phenomenal content, or a dimension of consciousness.

The synthetic fixture passes ranks 4, 5, and 6 separately, proving that the
apparatus does not secretly force 5.  A later provenance audit found that a
caller-supplied source-lock string alone cannot authenticate the spectra and
scores.  The implementation therefore now records
`external_source_receipt_verified=False` and keeps
`source_locked_empirical_signal_rank_result=False` until a receipt-bearing
external adapter exists.  `consciousness_dimension_claim_admitted` also
remains false by construction.

No source-locked held-out neural dataset was executed in this run.  Therefore
the current scientific result is still: no empirical selection among 4, 5, 6,
and no evidence that consciousness itself has dimension 4--6.
