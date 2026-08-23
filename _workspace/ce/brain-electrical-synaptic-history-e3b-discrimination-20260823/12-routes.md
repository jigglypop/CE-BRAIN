# BA-ERC1-E3b route decision

Status: COMPLETE

| route | decision | reason and stop boundary |
|---|---|---|
| Fixed nested exponential dictionary versus fixed asymmetric compact bump | `SELECTED / E3B-0..2 AUTHORIZED` | Includes a finite-truth negative generator, compact-history positive generator, held-out event trains, and reversal control. |
| Arbitrary FIR/history basis with many fitted lags | `REJECTED_FOR_THIS_STAGE` | Would confound history with parameter count and can overfit the noiseless synthetic fixture. |
| Nonnegative-only exponential weights | `REJECTED_AS_WEAK_CONTROL` | Unrestricted signed coefficients give the finite LTI family a stronger approximation opportunity. |
| Normal-equation least squares | `REJECTED_NUMERICALLY` | Squares conditioning; SVD on normalized columns is frozen instead. |
| Symmetric compact bump for orientation control | `REJECTED` | Time reversal would be identical and therefore nondiscriminating. |
| Nonlinear second-order Volterra kernel | `LOCKED_TO_E3B-3` | May open only under a new contract after the linearized port closes. |
| Active cable/HH re-embedding and measurement stress | `DEFERRED` | First isolate kernel-family specificity; then restore voltage/channel/measurement confounds one seam at a time. |
| Prior Allen IC/VC operator results | `PROHIBITED_EVIDENCE` | BA-SRM3 mixed amperes and volts; old ranks/scores cannot validate this equation. |
| Real data, state dimension, consciousness, hippocampal hash, or AGI | `PROHIBITED_HERE` | No corresponding endpoint or measurement model is opened. |

Execution is fail-closed: E3b-0 checks algebra and apparatus; E3b-1 must select finite `E2`; only then may E3b-2 generate the compact-history truth and open confirmation. Even a PASS makes E3b-3 only separately contractable, never automatically authorized.
