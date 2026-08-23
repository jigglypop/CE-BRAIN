# BA-ERC1-E3b mathematics — exact realization and finite-menu discrimination

Status: COMPLETE

## 1. Dimensionless state and kernels

`[Definition]` Physical time is divided by $T_0$. If a physical normalized kernel is $k_{\rm phys}(t)$ with units $T^{-1}$, define $a=t/T_0$, $\tau^*=\tau/T_0$, and $k_*(a)=T_0k_{\rm phys}(T_0a)$. Then $\int k_*(a)\,da=1$ and the normalized event response $q_*=\sum_rA_rk_*(\theta-\theta_r)$ is dimensionless for dimensionless event areas $A_r$.

Every nonlinear core argument is dimensionless: $a/\tau^*$, $r=a/W$, $1/r$, and $2/(1-r)$. The bounded sigmoid is not executed, but its future argument $b+q_*$ is also dimensionless.

## 2. Finite exponential realization

`[Theorem]` For each fixed $M$, the exponential kernel has an $M$-state Markov realization. Between events,

$$
\frac{dx_m}{d\theta}=-\frac{x_m}{\tau_m},
$$

and at event $r$, $x_m(\theta_r^+)=x_m(\theta_r^-)+A_r$. The output

$$
q_M(\theta)=\sum_{m=1}^{M}w_m\frac{x_m(\theta)}{\tau_m}
$$

equals convolution with $k_M$. Thus history dependence alone does not imply an intrinsically infinite-dimensional synapse.

## 3. Exact non-realization of the compact bump

`[Definition]` The fixed bump $k_B$ is nonzero on $0<a<W$, zero outside $[0,W]$, and has the exponential form declared in the contract. Standard endpoint-flat extension results make it $C^\infty$ on the real line.

`[Conditional theorem]` A nonzero compactly supported $C^\infty$ regular impulse response has no exact realization by a finite-dimensional continuous-time causal LTI system with constant matrices and no pure delay line or distributed state.

Proof. Such a realization has regular impulse response $h(a)=Ce^{Aa}B$ for $a>0$, with polynomial factors included through Jordan blocks. Every component is real analytic on $(0,\infty)$. Compact support makes $h$ zero on the open interval $(W,\infty)$. The identity theorem for real-analytic functions then makes $h$ zero throughout $(0,\infty)$, contradicting the nonzero bump. $\square$

`[Boundary]` The theorem concerns exact realization on a continuum. It supplies no positive lower bound for approximation by eight exponentials on a finite grid. The frozen $5\times10^{-3}$ margins are synthetic predictions/falsifiers, not theorems.

## 4. Fitting and selection

For a fixed event train, let $X_M$ contain the $M$ unit-weight exponential responses and let $x_B$ contain the unit bump response. Calibration solves

$$
\widehat\beta=\arg\min_\beta\|X\beta-y_{\rm cal}\|_2
$$

by SVD after column normalization. No normal equation is formed. Candidate predictions on development and confirmation use the same $\widehat\beta$.

`[Definition]` Models within $10^{-10}$ of the minimum development relative error form a tie set. The chosen model has the fewest coefficients; an equal-size finite/history tie selects the finite baseline. Confirmation never changes the selected model.

The normalized condition number is $\kappa_2(XD^{-1})$, where $D$ holds column $L^2$ norms. Full rank and $\kappa_2\le10^6$ are apparatus requirements. They do not establish biological parameter identifiability.

## 5. Formal predictions and countermodels

`[Prediction: negative specificity]` Because `E2` contains exactly the generating time constants, `E2`, `E4`, and `E8` have zero population approximation error. The tie rule must select `E2`; selecting `B` is an apparatus counterexample.

`[Prediction: positive discrimination]` The fixed bump model has zero population approximation error for its generator. Under the frozen finite samples, the best fitted `E1/E2/E4/E8` response and dense-kernel errors are each predicted to remain at least $5\times10^{-3}$. This is an unrun finite-fixture prediction.

`[Adverse control]` The asymmetric bump is not invariant under $a\mapsto W-a$. A calibration-fit reversed bump must retain confirmation error at least $5\times10^{-2}$; otherwise temporal orientation is not discriminated.

`[Unfinished]` No real synapse, nonlinear release, voltage coupling, stochastic noise, unknown measurement filter, arbitrary finite-dimensional nonlinear model, pure delay, or Volterra term is tested. Passing cannot prove biological infinite dimensionality.
