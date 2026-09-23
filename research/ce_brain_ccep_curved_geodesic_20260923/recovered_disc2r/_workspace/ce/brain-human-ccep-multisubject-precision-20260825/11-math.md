# BA-OBS-DISC2 math lane — 무차원성, 식별성, 다피험자 gate

Status: COMPLETE

## 판정 요약

`MATH_ADMISSIBLE_WITH_PROXY_CEILING`.

다섯 후보는 무차원이며 nested null과 determinant-one scale constraint가 명확하다. 74명의
patient-disjoint split은 DISC1의 source-cluster 불안정성을 직접 겨눈다. 다만 fitted
anisotropy는 fsaverage 좌표축에 의존하는 predictive proxy이고, actual Riemannian metric이나
state-space dimension은 식별되지 않는다.

## 1. 전기식에서 후보식까지

operating point 주위에서

$$
\mathcal C_*\dot v=-\mathcal A_*v+\mathcal B_sQ_s\delta(t)
$$

이면 $v(t)=e^{-t\mathcal C_*^{-1}\mathcal A_*}\mathcal C_*^{-1}\mathcal B_sQ_s$다.
$\mathcal A_*$를 local elliptic operator로 근사할 때 heat asymptotic의 log magnitude는

$$
\log |K|=c-\frac q2\log t-\frac{d_G^2}{4Dt}-\Lambda t+o(1)
$$

이고 screened cable의 공간 leading term은 $-a d_G$다. 실제 endpoint는 voltage가 아니라
baseline-normalized, trial-averaged RMS의 log이므로 amplitude·reference·nonlinear readout이
intercept와 잔차에 섞인다. 따라서 `SC/SAC/SH0/SHA0`는 연산자 identity가 아니라 이 두
leading geometry grammar의 제한된 예측 비교다.

## 2. 무차원 감사

| 항 | 정규화 | 결과 |
|---|---|---|
| 시간 | $x=t/(50\,\mathrm{ms})$ | $x>0$, $\log x$ 허용 |
| 좌표차 | $\Delta=(X_d-X_s)/(50\,\mathrm{mm})$ | 무차원 벡터 |
| isotropic 거리 | $r=\sqrt{\Delta^\top\Delta}$ | 무차원 |
| anisotropic 거리 | $d_G=\sqrt{\Delta^\top G\Delta}$, $G=\mathrm{diag}(e^{g_x},e^{g_y},e^{-g_x-g_y})$ | $g_x,g_y$와 exp 인자 무차원, $G\succ0$, $\det G=1$ |
| current 기록 | $\iota=\log(I/(8\,\mathrm{mA}))$ | 양의 current ratio의 log; source offset과 겹쳐 이번 fitted 공통항에서는 제외 |
| age | $\widetilde A=(A-20\,\mathrm{yr})/(20\,\mathrm{yr})$ | 무차원 |
| endpoint | $E=\mathrm{RMS}(\bar D/\sigma)$, $z=\log(E+10^{-6})$ | $E$와 floor 무차원 |
| cable | $a r$ 또는 $a d_G$ | $a$ 무차원 |
| heat | $\kappa r^2/x$ 또는 $\kappa d_G^2/x$ | $\kappa$ 무차원 |

exp/log/Huber core에 dimensionful quantity가 직접 들어가지 않는다. 512 Hz의 가장 짧은
`[10,18) ms` bin에도 네 samples가 있어 모든 고정 bin이 nonempty다.

## 3. 구조적 식별성

### free $q$ no-go

공통 시간항이 $\beta_1\log x$를 가지면 heat factor의 $-q\log x/2$를 추가한 design
columns는 정확히 선형 종속이다.

$$
\beta_1\log x-\frac q2\log x
=\left(\beta_1-\frac q2\right)\log x.
$$

따라서 $(\beta_1,q)$는 유일하지 않고 Jacobian rank가 하나 줄어든다. $q$를 고정하지 않은
latent-dimension fit은 금지한 계약이 맞다.

### metric scale no-go와 det-one 보정

$d_G=\sqrt{\Delta^\top G\Delta}$에서 $G\mapsto cG$와
$a\mapsto a/\sqrt c$는 cable prediction을 바꾸지 않는다. heat도
$G\mapsto cG$, $\kappa\mapsto\kappa/c$에 불변이다. $\det G=1$은 이 global scale orbit을
제거한다. 하지만 diagonal $G$만 쓰므로 회전된 anisotropy나 actual cortical chart는 여전히
식별하지 못한다.

### source gain 분리

평가 receiver로 $u_{is}$를 추정하면 geometry residual을 source lookup이 흡수할 수 있다.
계약은 hash-fixed 4 anchor에서 scalar $u_{is}$만 profile하고 12 disjoint query를 score한다.
각 source는 네 distance strata에 anchor 하나씩 있으므로 intercept가 특정 거리대 하나에만
고정되는 문제도 줄인다. candidate마다 동일한 anchor 수와 nuisance 차원을 써 비교가 공정하다.

자유 source offset을 둔 상태에서 global intercept나 source-constant current term을 동시에
추정할 수는 없다. source-constant $c$에 대해

$$
\widehat u_{is}(\mu+c)=\widehat u_{is}(\mu)-c,
\qquad
(\mu+c)+\widehat u_{is}(\mu+c)=\mu+\widehat u_{is}(\mu)
$$

이므로 $\beta_0$와 $\gamma_I\iota_{is}$의 Jacobian columns는 영벡터다. 이에 따라 공통항은

$$
T_i^\star(x)=\beta_1\log x+\beta_2x
+\gamma_1\widetilde A_i\log x+\gamma_2\widetilde A_ix
$$

로 줄였다. current 값은 provenance로 보존하지만 이번 run은 current effect를 식별하거나
주장하지 않는다. 이를 추정하려면 source offset에 사전 고정된 shrinkage나 zero-sum 제약을 둔
별도 계층모형과 새 run이 필요하다.

### 좌표와 생물 metric

finite electrode pairs의 energy와 fsaverage 좌표만으로는 native axonal path, tract branch,
conductance, source/receiver gain, volume conduction과 metric curvature를 동시에 분해할 수
없다. 서로 다른 latent operators가 같은 sampled transfer matrix를 만들 수 있으므로 fitted
$G$는 predictive chart proxy 이상으로 승격할 수 없다.

## 4. 분할·표본 단위 검산

age strata 크기는 `19/19/18/18`이고 각 stratum의 stage quota 합은 각각

$$
6+2+3+8=19,\quad 6+2+3+8=19,\quad
6+2+3+7=18,\quad 6+2+3+7=18
$$

이다. 따라서 D0/D1/D2/D3 participant 수는 정확히 `24/8/12/30`이다. D0 각 fold는 네
age strata에서 한 명씩 test로 받아 4명이고 6 folds가 24명을 한 번씩 덮는다.

각 participant의 primary statistic은

$$
\Delta_i=\frac18\sum_s
\left(\mathcal L_{S0,is}-\mathcal L_{W,is}\right)
$$

다. source 내부 12 receivers와 5 bins는 반복 측정이지 독립 표본이 아니다. 따라서 outer
bootstrap이 participant를 resample하고 source를 equal-weight 평균하는 계약이 맞다.
D3은 30 participants와 240 sources를 가지므로 선행 planning의 source ≥80을 넘지만,
population precision은 $N=30$ participant가 제한한다. 정규근사 one-sided
$\alpha=0.025$, power 0.90에서 필요한 standardized participant effect는 약

$$
\frac{1.96+1.282}{\sqrt{30}}\simeq0.592
$$

다. 이는 power 보장이 아니라 final detectable scale의 사전 진단이다.

trial repeatability와 polarity는 같은 개념이 아니다. 모든 source는 시간순 5/5 halves를
가지지만, 두 orientation을 실제로 가진 source만 orientation-specific 5-vs-5 비교가 가능하다.
D0에서 전자는 192 sources 전체, 후자는 사전 고정된 48 sources와 6 participants에만
계산한다. single-orientation 144 sources를 polarity evidence로 세지 않는 수정이 필요하고
계약에 반영됐다.

## 5. 단계 gate 검산

- D1의 `6/8 positive`와 $p\le0.20$은 약한 식을 빨리 죽이는 screen이며 확인 주장에 쓰지
  않는다.
- endpoint-blind null fixture v1에서 `improvement>0` D0 rule은 `4/64` false selection을 냈고,
  네 건 모두 `SH0`, 개선 범위는 $6.14\times10^{-5}$에서 $4.934\times10^{-3}$였다. 따라서
  실제 endpoint 개봉 전 마지막 revision에서 D0 최소 상대개선을 $0.005$로 올렸다. 이 값은
  새 v2 salt fixture에서 독립적으로 재검사하며 실제 CCEP 효과를 보고 고친 값이 아니다.
- D2의 one-sided 80% LCB, `8/12 positive`, $p\le0.10$은 중간 promotion 조건이다.
- D3의 one-sided 97.5% LCB, `20/30 positive`, $p\le0.025$가 유일한 final gate다.
- permutation은 source 안에서 query coordinate tuple 전체를 바꾸므로 response/time/source
  gain을 보존하고 geometry association만 끊는다.
- matched prestimulus가 같은 D3 gate를 통과하면 geometry가 evoked response가 아니라
  baseline/reference 구조를 예측했을 수 있으므로 final claim을 죽이는 것이 맞다.

## 6. 수치 gate와 남은 위험

full-rank Jacobian, condition number $\le10^7$, upper-bound·anisotropy-bound rejection은
수치 degeneracy를 성공으로 세지 않게 한다. Jacobian은 normalized parameter coordinate에서
중심차분하되 매 차분점에서 anchor profile을 다시 계산한 query prediction으로 만든다.
$a/\kappa\le10^{-4}$는 nested S0 collapse로 분류한다. 다만 Huber-profile objective는
piecewise smooth이고 local minima가 가능하므로 training query/time design의 source-centered
rank-4 OLS common start와 그 perturbation, isotropic attenuation 다섯 starts와,
anisotropic attenuation 세 starts와 anisotropy 9 starts를 교차한 27 starts로 basin search를
한다. 이어 최저 basin의 normalized parameter $0,\pm10^{-3}$ perturbation 세 해에서
loss/prediction agreement를 확인해야 한다. Huber
source offset은 반복 최적화 대신 20개 anchor residual의 $r_j\pm0.5$ breakpoints를 전부 훑는
정확한 piecewise-linear score root를 쓴다. endpoint-blind analytic fixture에서 보인 평평한
nuisance valley를 수치 실패로 과대분류하지 않도록 prediction agreement는 log-energy RMS
$5\times10^{-2}$로 고정하고 loss 상대차는 $2\times10^{-4}$로 고정하되 Jacobian gate는
유지한다.

빠른 제거 목적에 맞춰 각 local optimizer는 300 iterations/6,000 function calls에서
fail-closed한다. 이는 수렴하지 않은 해를 열등한 loss로 채택하는 truncation이 아니라 해당
candidate 전체를 numerical stop으로 분류하는 규칙이다.

남은 주요 위험은 다음과 같다.

1. trial-averaged response가 비연결 pair에서 noise floor에 몰리면 log-floor sensitivity가
   생길 수 있다. floor는 고정하고 sensitivity를 diagnostic으로만 보고 구조는 바꾸지 않는다.
2. bipolar가 local reference를 줄여도 differential volume conduction은 남는다. contact-mean
   concordance와 prestimulus control만으로 완전 제거를 주장하지 않는다.
3. age-linear time interaction은 nuisance leakage를 줄이지만 실제 age dynamics가 nonlinear일
   수 있다. stage가 age-stratified이므로 predictive comparison은 가능하나 발달 법칙을
   추정하는 run은 아니다.

## Math-lane 결론

계약의 식과 inference unit은 내부 일관성이 있다. 실행 허용 범위는 patient-held-out
observed bipolar energy prediction이며, metric/dimension/consciousness 해석은 금지한다.
