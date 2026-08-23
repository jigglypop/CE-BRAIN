# BA-SRM9 math lane — dense observed JUMP mixing

Status: COMPLETE

## 1. Carried conditional formula

**[정리: carried conditional]** Under BA-SRM8's nonnegative physical-time weights, valid effective-sample-size condition, and positive calibration scale, the weighted covariance is PSD. Its resolvent has $0\le d_{\rm eff}\le r_*$ and normalized $Q\in[0,1]$. This statement is unchanged and does not identify a biological Riemannian metric.

## 2. JUMP mixing lemma

**[정리]** Let $H\in\mathbb R^{12\times12}$ be orthogonal and $H_r=H_{:,1:r}$. If $\xi\sim N(0,I_r)$ and $x=H_r\xi$, then

$$
\operatorname{Cov}(x)=H_rH_r^\mathsf T,
$$

whose rank is $r$ and whose nonzero eigenvalues are all one. The fixture calls this latent pre-calcium matrix $\Sigma_{x,r}$, not a calcium-$y$ covariance. Its exact numerical tests are $|\operatorname{tr}\Sigma_{x,r}-r|\le10^{-10}$ and sorted `eigvalsh` infinity residual against $[0]^{12-r}\cup[1]^r$ at most $10^{-10}$; `matrix_rank` and every tolerance-based rank proxy are forbidden. Each channel $i$ has pre-jump variance $\sum_{k=1}^2H_{ik}^2$. For a Haar-continuous QR draw this sum is positive almost surely; BA-SRM9 admits only fixtures that explicitly verify the stronger numerical condition $>10^{-12}$ for every row. Diagonal prefix z-scaling with finite nonzero diagonal entries is invertible, so it preserves covariance rank.

**Proof.** Orthogonality gives $H_r^\mathsf TH_r=I_r$, so $H_rH_r^\mathsf T$ is an idempotent rank-$r$ projector. Its $i$th diagonal entry is the stated squared-row energy. Invertible diagonal congruence preserves rank. □

For the eight $E_A$ seeds, observed eligibility is $I_i=\{t<460:m_{i,t}=1\}$, with $|I_i|\ge100$ and clean-calcium `ddof=0` prefix SD over $I_i$ greater than $10^{-12}$. Support residuals test latent $x$ against $\operatorname{span}(H_{:,1:2})$ before the jump and $\operatorname{span}(H_{:,1:8})$ after it; a calcium-$y$ projector equality is not a valid test. Any failed matrix, eligibility, support, or environment/hash receipt check is `SYNTHETIC_DGP_STOP`.

## 3. Boundary

The lemma repairs only observed JUMP sensor support. It neither validates a candidate $Q$ nor supplies a F2-A score, behavior result, real-neural result, synaptic-edge claim, loop claim, hippocampal hash, consciousness claim, or AGI claim.
