# BA-SRM7 수학 검산 — 무한 history와 관측 유효차원

Status: COMPLETE

Date: 2026-08-23

## 1. 판정

계약의 finite observed operator와 resolvent 유효차원에는 P0 반례가 없다. BA-SRM6에서
확인한 trace-class 조건, rank-4 no-go, 좌표불변성 제한도 유지된다. 이번 판본의 새
부분인 reliability weight는 PSD를 보존한다. causal measurement는 scored block에서
미래 neural/behavior를 읽지 않도록 정의됐다.

초안의 Volterra boundedness, history unit, synthetic truth, time-reversal alignment,
fixed-$d$ domain과 missingness-only zero control은 revision 1/2에서 명시적으로 닫혔다.
구현 전 남은 P0/P1은 없다. 이 판정은 L0 또는 실제 데이터 결과를 미리 보증하지 않는다.

## 2. 형식 지위

| 대상 | 지위 | 전제ㆍ경계 |
|---|---|---|
| weighted history direct sum $\mathcal H$ | `[정의]` | 성분별 reference scale로 무차원화, $\tau_h>0$ |
| Volterra edge $K_{ij}$ boundedness | `[조건부 정리]` | 계약의 weighted Hilbert--Schmidt 적분이 유한 |
| loop return $L_\gamma$ boundedness | `[조건부 정리]` | 유한 loop, 각 edge bounded |
| strong Riemann metric $g_x$ | `[조건부 정리]` | $\mathcal A_x$ boundedㆍself-adjointㆍuniformly coerciveㆍoperator-norm smooth |
| calcium reliability covariance $G_t$ PSD | `[정리]` | finite observed window, fixed diagonal $D_r$, $W\ge2$ |
| $d_{\rm eff}$ 범위ㆍ연속성ㆍ단조성 | `[정리]` | $G\succeq0$, $c_G>0$, $\lambda>0$ |
| infinite-dimensional finite trace | `[조건부 정리]` | positive self-adjoint trace-class $G$ |
| four soft features의 locomotion 증분값 | `[예측]` | L0와 input gate 뒤 frozen splitㆍcontrols로만 판정 |
| 의식ㆍ해마ㆍedgeㆍAGI 해석 | `[미완성]` | 현재 관측 map으로 식별 불가, active prediction 아님 |

## 3. history space와 edge operator

무차원 history coordinate에 대해

$$
\|h_i\|_{\mathcal H_i}^2=
\int_{-\infty}^{0}\|h_i(s)\|^2e^{2s/\tau_h}\frac{ds}{\tau_h}
$$

는 잘 정의된 Hilbert norm이다. 단순히 Volterra 적분을 썼다는 사실만으로 operator가
bounded인 것은 아니다. 예를 들어 $\tau_h=1$, $k(s,u)=1$,
$f_n(u)=e^n\mathbf1_{[-n-1,-n]}(u)$이면 input weighted norm은 유계지만
$s\in[-1,0]$에서 $(Kf_n)(s)=e^n$이므로 output norm이 발산한다.

계약은 이를 피하기 위해

$$
\int_{-\infty}^{0}\int_{-\infty}^{s}
\|k_{ij}(s,u;\xi)\|_F^2e^{2(s-u)/\tau_h}\,du\,ds<\infty
$$

를 충분조건으로 둔다. weighted coordinate로 unitary conjugation하면 이 적분은
transformed triangular kernel의 Hilbert--Schmidt norm이므로 $K_{ij}$가 bounded다.
유한 loop의 return $L_\gamma$는 bounded operator의 유한 곱이어서 bounded다.
그러나 calcium covariance는 시간 순서와 방향을 버리므로 이 operator들을 데이터에서
복원하지 못한다.

## 4. observed PSD operator

$H=I-W^{-1}\mathbf1\mathbf1^{\mathsf T}$는 symmetric idempotent centering
projector다. 임의의 $v$에 대해

$$
v^{\mathsf T}G_tv
=\frac1{W-1}v^{\mathsf T}D_rZ_tHZ_t^{\mathsf T}D_rv
=\frac{\|HZ_t^{\mathsf T}D_rv\|^2}{W-1}\ge0.
$$

따라서 $G_t\succeq0$이고
$\operatorname{rank}G_t\le\min(N_{\rm kept},W-1)=r_\star$다. $D_r$가
train-prefix missingness에서 만든 analyst reliability prior라는 점은 이 증명을
바꾸지 않는다. 반대로 이것이 latent covariance의 unbiased estimator라는 결론도
주지 않는다.

$\widetilde G$의 eigenvalue를 $\mu_k\ge0$라 하면

$$
S_\lambda=\widetilde G(\widetilde G+\lambda I)^{-1},
\qquad
d_{\rm eff}(\lambda)=\sum_k\frac{\mu_k}{\mu_k+\lambda}.
$$

따라서

$$
0\preceq S_\lambda\preceq I,
\qquad
0\le d_{\rm eff}\le r_\star,
$$

$$
\frac{d}{d\lambda}d_{\rm eff}
=-\sum_k\frac{\mu_k}{(\mu_k+\lambda)^2}\le0.
$$

$d_{\rm eff}$는 $\lambda>0$에서 매끄럽고 일반적으로 정수가 아니다. 이는 soft spectral
degrees of freedom이지 Riemann manifold의 차원이 아니다. 이미 구성한 $G$에 대한
$QGQ^{\mathsf T}$ orthogonal similarity에서는 spectrum이 보존된다. 하지만 neuronwise
mask로 $D_r$를 다시 계산하는 raw pipeline 전체는 orthogonal chart-invariant가 아니다.

## 5. infinite-dimensional trace와 regularized inner product

positive self-adjoint trace-class $G$에서는

$$
\operatorname{Tr}S_\lambda
=\sum_n\frac{\mu_n}{\mu_n+\lambda}
\le\frac1\lambda\sum_n\mu_n<\infty.
$$

compact만으로는 충분하지 않다. $\mu_n=1/n$이면 compact이지만 위 trace는 harmonic
tail 때문에 발산하고, $G=I$에서도 $S=(1+\lambda)^{-1}I$라 trace가 무한하다.

finite observed space에서

$$
A=10^{-3}I+(1-10^{-3})S
$$

이면 $10^{-3}I\preceq A\preceq I$이고 condition number가 $10^3$ 이하인 SPD
inner product다. kernel 방향을 analyst prior로 채운 것이므로 biological Riemann metric의
검증이 아니다. infinite history metric에는 계약 §5의 별도 smoothnessㆍcoercivity가
필요하다.

## 6. 변화량의 범위와 무차원성

두 PSD contraction의 rank가 각각 $r_\star$ 이하이므로

$$
\|S_t-S_{t-1}\|_F^2
\le\operatorname{tr}S_t^2+\operatorname{tr}S_{t-1}^2
\le2r_\star,
$$

즉 $0\le\kappa_t\le\sqrt2$다. $\kappa$는 step-to-step selector change이지
시간 rate가 아니다. $\nu$만 $\Delta t/\tau_0$로 나눈 rate다.

| core 인자 | 차원 벡터 $(M,L,T,\Theta)$ | 정규화 |
|---|---|---|
| $s/\tau_h$, $ds/\tau_h$ | $(0,0,0,0)$ | history time / $\tau_h$ |
| Gaussian $\ell/\sigma$ | $(0,0,0,0)$ | volume count / volume count |
| photobleach $bt$ | $(0,0,0,0)$ | $b$는 $T^{-1}$, $t$는 $T$ |
| $G/c_G$, $\lambda$ | $(0,0,0,0)$ | standardized fluorescence covariance / train scale |
| $q,\kappa,\Delta t/\tau_0,\nu$ | $(0,0,0,0)$ | 정의상 무차원 |
| $\kappa/\sigma_\kappa$, $\nu/\sigma_\nu$ | $(0,0,0,0)$ | 동일 종류 RMS로 나눔 |
| $\rho_k$ in $\log\rho_k$ | $(0,0,0,0)$ | eigenvalue / trace |

따라서 $\mathcal M$의 exponential과 entropy의 logarithm 인자는 무차원이다. 기존
checker의 focused regression `tests/test_dimensionless.py`도 `19 passed`였다. 이 검사는
차원 정합만 말하며 식의 생물학적 타당성을 말하지 않는다.

## 7. measurementㆍL0 식별 경계

원저자 centered Gaussian interpolation은 미래 sample을 읽을 수 있다. BA-SRM7의
one-sided normalized convolution은 calibration prefix 이후 scored anchor에서 frozen
prefix parameter와 현재ㆍ과거 neural sample만 읽는다. prefix 내부 anchor는 online
prediction으로 해석하지 않고 coefficient calibration에만 쓴다.

photobleachㆍred/green regression의 raw prefix는 cutㆍmanual exclusion 뒤, majority-valid
map 전 first-60%로 고정된다. 그 fit에서 valid map을 만든 뒤의 retained first-60%는
eligibilityㆍreliabilityㆍspectral scale용 processed prefix다. 이 순서는 valid map이
자기 자신을 정의하는 순환을 피한다. nonlinear fit exception은 identity fallback으로
고정돼 숨은 initial-value search가 없다.

L0-B truth는 dropout mask에서 고정한 $D_r$를 clean/noisy 양쪽에 공유하되, clean과
estimate가 각자 first-60% scale을 fit하도록 고정됐다. NMAE 분모는 $|A_s|r_\star$다.
zero truth는 abstain, stationary isotropic truth는 correlation gate 제외, reversal은

$$
d_{\rm eff}^{\check y}(t)=d_{\rm eff}^{y}(T-t+W)
$$

로 rolling alignment를 고정했다. L0-C의 $\rho$는 RMS-squared power ratio이고 truth는
original mask의 같은 $D_r$와 clean calibration scale을 쓴다. 이 장치가 통과해도
latent neural dimension recovery가 아니라 observed operator recovery다.

pairwise-complete covariance route는 기각이 맞다. 대각 1, off-diagonal
$(0.9,0.9,-0.9)$인 symmetric pairwise matrix의 최소 eigenvalue는 $-0.8$이라 PSD가
아니다. resolvent core의 입력으로 쓰면 안 된다.

## 8. 수치 spot check

seed `20260823`, $N=12,W=60$에서 독립 계산한 결과는 다음과 같다.

| 항목 | 결과 |
|---|---:|
| $\min\operatorname{eig}(G)$ | 0.2888557574 |
| $d_{\rm eff}(0.1,0.3,1,3,10)$ | 10.6603, 8.8097, 5.64177, 2.86684, 1.06908 |
| orthogonal trace residual | $8.88\times10^{-16}$ |
| $\min\operatorname{eig}(A)$ | 0.2652542358 |
| $\operatorname{cond}(A)$ | 2.5247218 |
| non-PSD pairwise witness minimum eigenvalue | -0.8 |
| unbounded Volterra norm-ratio lower bound at $n=8$ | $8.8861\times10^6$ |

스크립트 `artifacts/math_spotcheck.py` SHA-256은
`541e03c35ad27fdb90ae2656a449efb5adb2ea7ffaff989249277b3941b3f993`, 결과
`artifacts/math-spotcheck.json`은
`4290b0b9cbef67f18e79e3005f246015fa11a37b556088386fa49c8c058a7d1f`다.

## 9. P0/P1/P2와 결론

- P0: 없음.
- P1: 초안의 weighted-kernel 조건, unit normalization, calibration-causal 범위,
  pipeline chart 범위, L0 truth/dropout/NMAE, reversal alignment, fixed-$d$ domain,
  constant-mask control과 adverse ridge 선택을 revision 1/2에서 해결했다.
- P2: raw green $G$와 covariance $G_t$는 문맥으로 구분한다. 구현에서는
  `green_signal`과 `covariance`로 이름을 분리한다.

수학 판정: `IMPLEMENTABLE_CONDITIONAL_FORMALIZATION / EMPIRICAL_RESULT_UNOPENED`.

## 10. 재현 명령

```powershell
.codex\hooks\python.cmd python `_workspace\ce\brain-adaptive-effective-dimension-validation-v2-20260823\artifacts\math_spotcheck.py`
.codex\hooks\python.cmd pytest `tests\test_dimensionless.py` -q
```
