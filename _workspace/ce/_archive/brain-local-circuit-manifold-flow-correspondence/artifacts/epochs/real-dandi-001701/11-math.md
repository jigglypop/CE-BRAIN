# Preregistered real-data estimands

Status: COMPLETE

Let $n_t\in\mathbb N^N$ be 100 ms spike counts and let $x_t$ be the train-scaled
Anscombe transform. Train-only PCA gives orthogonal coordinates
$z_t=U_d^{\mathsf T}x_t$ and $y_t=V_d^{\mathsf T}x_t$. The candidate model is

$$
z_{t+1}=Bz_t+d+\epsilon^z_t,
\qquad
y_{t+1}=Ay_t+Cz_t+e+\epsilon^y_t.
$$

All coefficient matrices use ridge regression with an unpenalized intercept.
The reconstruction is $\widehat x_{t+1}=U_d\widehat z_{t+1}+V_d\widehat y_{t+1}$.
Development-only selection follows `00-contract.md`.

For $T$ bins, the exact half-open split indices are those in `00-contract.md`.
One-step input indices in a block $[a,b)$ are $a,\ldots,b-2$ and targets are
$a+1,\ldots,b-1$; cross-boundary rows are absent. Train-only scaling and PCA are
immutable before development scoring. Whole-file/HDF5 decoding is not itself a
statistical opening, but the implementation must assert that every event admitted
to the prefix count matrix is before the test boundary and that no test-derived
array or statistic exists before `model_selected=True`.

The primary score is

$$
\operatorname{NMSE}
=\frac{\sum_t\|x_{t+1}-\widehat x_{t+1}\|_2^2}
{\sum_t\|x_{t+1}-\bar x_{\rm train}\|_2^2},
\qquad
\bar x_{\rm train}=T_{\rm train}^{-1}\sum_{t=0}^{T_{\rm train}-1}x_t.
$$

The affine-fiber empirical bridge passes only if its held-out NMSE is at least
1% smaller than persistence and an independently development-tuned, same-input
full ridge VAR(1), and both paired 95% moving-block-bootstrap improvement
intervals have lower endpoint above zero. Bootstrap settings are 2,000
resamples of 100-bin blocks with seed 1701. It must also satisfy

$$
q=\|A\|_2<1,
\qquad
q\kappa=q\|B^{-1}\|_2<1.
$$

Candidate and full VAR use the same train/development rows, ridge menu,
unpenalized-intercept convention and denominator; each receives its own fair
development selection. No coefficient clipping or stability projection is allowed. If $B$ is singular,
$\kappa=\infty$ and the bunching certificate fails. A fitted linear invariant
graph $y=Hz+r$ is obtained from train samples by ridge regression and evaluated
without refitting through

$$
R_{\rm inv}
=\frac{\sum_t\|H(Bz_t+d)+r-[A(Hz_t+r)+Cz_t+e]\|_2^2}
{\sum_t\|y_{t+1}\|_2^2}.
$$

Here $H,r$ are fit on the same train one-step rows with fixed ridge
$\lambda_H=10^{-2}$ and unpenalized intercept. A zero denominator reports
`UNDEFINED` and cannot be converted to zero. $R_{\rm inv}$ is a secondary
diagnostic and not a pass condition. It measures compatibility of the fitted maps;
it is not proof of a global manifold. Multi-step forecasts iterate the frozen
maps at horizons $1,2,5,10$. The 10-second shifted control is a 100-bin lag
inside each split: the first 100 rows are discarded, no wraparound is admitted,
and all comparators are rescored on the same reduced targets. Observational trajectories cannot directly
identify counterfactual fiber attraction or a unique continuous-time generator;
those claims remain outside the empirical ceiling.
