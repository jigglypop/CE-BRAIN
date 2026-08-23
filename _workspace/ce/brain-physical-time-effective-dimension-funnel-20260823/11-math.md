# BA-SRM8 수학 레인 — 비음수 물리시간 covariance와 선별 규율

Status: COMPLETE

Date: 2026-08-23

## 1. 전제와 지위

이 레인은 `00-contract.md`의 식을 정의ㆍ조건부 정리ㆍ분석자 공리ㆍ예측으로 분리한다.
실제 brain manifold, synaptic edge 또는 consciousness를 정리의 결론에 넣지 않는다.

- physical-time kernel family와 threshold: `[공리: 모델 선택]`;
- weighted covariance의 PSD와 rank bound: `[정리]`;
- resolvent trace의 범위ㆍ연속성ㆍ$\lambda$ 단조성: `[정리]`;
- observed truth recovery와 behavior prediction: 각각 `[산출 후보]`, `[예측]`.

## 2. weighted covariance PSD 정리

고정 anchor $t$에서 $a_j\ge0$이고 $A=\sum_ja_j>0$라 하자. $w_j=a_j/A$이면
$w_j\ge0$, $\sum_jw_j=1$이다. 두 개 이상의 sample이 양의 weight를 갖고

$$
c_w=1-\sum_jw_j^2>0
$$

라 하자. $\bar x=\sum_jw_jx_j$와

$$
G=\frac1{c_w}\sum_jw_j(x_j-\bar x)(x_j-\bar x)^{\mathsf T}
$$

를 정의하면 임의의 $v$에 대해

$$
v^{\mathsf T}Gv
=\frac1{c_w}\sum_jw_j[v^{\mathsf T}(x_j-\bar x)]^2\ge0.
$$

따라서 $G\succeq0$다. mask가 sample vector를 zero로 바꾸거나 bounded radial map이
$x_j$를 다른 vector로 바꾸어도 이 증명은 변하지 않는다. 반면 channel pair마다 서로
다른 denominator를 쓰는 pairwise-complete covariance는 하나의 outer-product 합으로
표현되지 않아 일반적으로 PSD가 아니다.

양의 weight sample 수 $n_+=|\{j:a_j>0\}|$라 하면 중심화 때문에

$$
\operatorname{rank}G\le\min(N,n_+-1)=r_\star.
$$

## 3. effective sample size

정규화 전 weight $a_j$에 대해

$$
n_{\rm eff}=\frac{(\sum_ja_j)^2}{\sum_ja_j^2}
=\frac1{\sum_jw_j^2}.
$$

$n_{\rm eff}>1$은 $c_w>0$과 동치다. $n_{\rm eff}\ge8$은 정리가 아니라 한 sample에
집중된 kernel과 수치적으로 불안정한 covariance를 배제하기 위한 `[공리: 장치 하한]`이다.
짧은 kernel이 이 하한을 구조적으로 통과하지 못하면 candidate를 일찍 제거하는 것이며,
brain 가설의 반례가 아니다. 특히 이 하한은 behavior prediction의 statistical power나
생물학적 충분 정보의 조건이 아니다.

## 4. kernel과 무한 과거

계약의 네 kernel family는 $u<0$에서 사용하지 않고 $u\ge0$에서 비음수다. 따라서
future neural sample은 weight 0이다. EXP와 BIEXP는 적분 가능하고 POWER는 $p>1$일 때

$$
\int_0^\infty(1+u/\theta)^{-p}du=\frac{\theta}{p-1}<\infty
$$

다. COMPACT는 유한 support다. 이들은 infinite history state를 서로 다른 해상도로
읽는 관측 kernel이지, state space 자체의 차원을 정하지 않는다.

물리시간 간격 $u=(t_t-t_j)/\tau_0$와
$\delta=\min(3,(t_j-t_{j-1})/\tau_0)$는 무차원이다. $q^\gamma$도 무차원이다.
따라서 $a$, $w$, $n_{\rm eff}$는 무차원이다. $\delta$ cap 3은 gap 하나를 여러 관측의
질량으로 오인하지 않게 하는 분석자 규칙이며, hard-gap anchor 삭제와 다르다. 이
route는 barrier를 두지 않는다. gap 전 sample은 실제 $u$만큼 감쇠되므로 이는
`soft gap downweighting`이지 관측된 연속성의 증명이 아니다.

## 5. robust map의 bounded influence

$r(x)=\|x\|_2/\sqrt N$와 $c=3$에 대해 radial Huber map은

$$
r(R_{\rm Hub}(x))=\min(r(x),c),
$$

radial tanh map은

$$
r(R_{\tanh}(x))=c\tanh(r(x)/c)<c
$$

를 만족한다. 두 map 모두 $R(0)=0$이고 norm 방향만 축소한다. 따라서 단일 artifact의
outer-product norm은 bounded다. 이것은 artifact를 생물학적 신호와 완전히 분리한다는
정리가 아니며 semi-synthetic falsifier가 필요하다.

## 6. resolvent 유효차원

$G\succeq0$, $c_G>0$와 $\lambda>0$이면 $\widetilde G=G/c_G$의 고유값을 $\mu_k\ge0$라
둘 수 있다.

$c_G$의 calibration set은 original time index
$0\le t<\lfloor0.70T\rfloor$와 valid covariance의 교집합이다. usable covariance만
압축한 뒤 그 목록의 first-70%를 쓰면 original 경계 뒤가 들어갈 수 있으므로 금지한다.
$r_\star=\min(N,n_+-1)$이고 numerical rank를 대신 쓰지 않는다.

$$
S_\lambda=\widetilde G(\widetilde G+\lambda I)^{-1},\qquad
d_{\rm eff}(\lambda)=\sum_k\frac{\mu_k}{\mu_k+\lambda}.
$$

따라서

$$
0\preceq S_\lambda\preceq I,\qquad
0\le d_{\rm eff}\le\operatorname{rank}G\le r_\star,qquad
0\le Q=d_{\rm eff}/r_\star\le1.
$$

또한

$$
\frac{d}{d\lambda}d_{\rm eff}
=-\sum_k\frac{\mu_k}{(\mu_k+\lambda)^2}\le0.
$$

$d_{\rm eff}$는 $G$의 entry와 $\lambda>0$에서 연속이다. 정수가 아닌 값은 soft
spectral occupancy이며 비정수 리만 다양체 차원이 아니다.

## 7. isotropic shrinkage 반례

ambient shrinkage

$$
G^\eta=(1-\eta)G+\eta\frac{\operatorname{tr}G}{N}I
$$

는 PSD를 보존하지만 $\eta>0$, $\operatorname{tr}G>0$이면 full rank가 된다. 원래
$r_\star<N$일 때 $d_{\rm eff}(G^\eta)$가 $r_\star$보다 클 수 있어
$Q=d_{\rm eff}/r_\star\le1$ 정리가 깨진다. 따라서 shrinkage는 primary 48개에서
제외하고, 사용하려면 $N$ 정규화의 별도 diagnostic으로 분리해야 한다.

## 8. 차분 feature와 무차원성

$Q$는 무차원이고 $(t_t-t_{t-1})/\tau_0$도 무차원이므로 $V$는 무차원이다.
$S$와 $\sqrt{r_\star}$도 무차원이므로 $\kappa$는 무차원이다. first-70% RMS
$\sigma_V,\sigma_\kappa>10^{-12}$로 나눈 뒤에만

$$
M=\exp[-(V/\sigma_V)^2-(\kappa/\sigma_\kappa)^2]
$$

를 계산한다. scale이 0 또는 nonfinite면 candidate가 abstain한다. 따라서 exp 인자는
무차원이다.

## 9. candidate 수와 funnel의 논리

kernel specification 8개, quality exponent 2개, robust map 3개이므로 정확히 48개다.
초기 수를 64라고 쓰면서 16개를 결과 뒤 추가하면 selection contract가 성립하지 않는다.
따라서 이 판본의 수열은

$$
48\longrightarrow32\longrightarrow16\longrightarrow8
\longrightarrow4\longrightarrow2\longrightarrow1
$$

이다. 마지막 5%를 LARGE-A와 LARGE-B로 나누므로 2개 중 1개를 고른 block과 그 한 개를
재확인하는 block이 다르다.

F1 recovery에서 clean truth와 noisy estimate는 동일한 observed mask, $D$, clock과
candidate를 사용한다. normalized $Q\in[0,1]$를 비교할 때

$$
\operatorname{NMAE}^Q=|A|^{-1}\sum_{t\in A}|\widehat Q_t-Q_t^{\rm truth}|
$$

는 이미 무차원이며 range denominator가 필요 없다. recovery anchor는 $A=\{t:Q_t^{\rm truth},\widehat Q_t\text{ 모두 finite}\}$다. $|A|<100$ 또는 constant truth의
Spearman은 `ABSTAIN`이다. tie가 있으면 average rank를 사용한다.

F1 promotion source는 self-contained v6뿐이다. v6은 clean/noisy 각각의 masked finite first-60%에서 자기 $(\mu,\sigma)$를 fit하고, shared mask/$D$/clock과 original-index zero-based exclusive $c_G$ boundary를 만족한다. v3/v4/v5는 각각 documented full-$T$, ceil-boundary, constant-truth/provenance 문제로 superseded되어 보존만 한다. F0-v3과 F1-v6의 receipt가 주는 12 `ABSTAIN`, 32 `PROMOTE`, 4 `DROPPED_BUDGET`는 F1 apparatus 결과이지 F2 또는 behavior 결과가 아니다.

F2의 DGP는 implementation choice가 아니라 계약 입력이다. $N=12,T=768,T_{\rm cal}=537,T_D=460$이며 두 경계는 zero-based exclusive다. named SHA-256 substream, irregular increment, 세 개의 long gap, skew-generator redraw, $\operatorname{expm}$ convention, latent spectrum, causal calcium recursion, prefix-pooled noise/artifact scale은 모두 `00-contract.md`와 config-v4에 수치까지 고정한다. fixture-v3는 그 deterministic pseudocode/source closure일 뿐 candidate $Q$, F2 gate, behavior/model 결과가 아니다. 따라서 ROT/MISS/BLOCK/ART/JUMP/ISO/ZERO/REVERSE는 이름만 같은 임의 simulator가 아니라 같은 raw-clock-mask experiment다. 이는 recovery/falsification apparatus의 정의이며 biological latent-state 정리가 아니다.

F2의 null 변화 임계값은 estimate $Q$에서만 정의한다. adjacent common finite anchor에서
$$
V_{\rm est}(t)=\frac{Q_{\rm est}(t)-Q_{\rm est}(t-1)}{(c_t-c_{t-1})/\tau_0},\qquad
\theta_f=Q_{0.95}^{\rm linear}(|V_{\rm est}|;\mathrm{ISO\_NULL},S_{\rm cal})
$$
이며 $S_{\rm cal}=20261001,\ldots,20261016$이다. derivative anchor는 $B=\{t:t\in A,\ t-1\in A\}$이고, $V_{\rm est}$ 및 FAR는 $B$에서만 정의한다. ISO_NULL/JUMP는 $|B|<100$이면 `ABSTAIN`이다. 이 정의는 truth $Q$를 detection threshold에 누설하지 않는다. JUMP의 탐지는 $t_*=384\pm96$ 안에서의 $|V_{\rm est}|$ 최대값과 $\theta_f$ 비교로 한정하며, clean truth는 recovery accuracy에만 쓴다. 이는 경험적 screen 정의이지 biological change-point 정리가 아니다.

SMALL/MID/LARGE는 selection data다. 그 score는 과학적 confirmation이 아니다. FINAL
20%가 confirmatory 의미를 가지려면 formula, preprocessing, coefficient, target,
control, row와 score code가 LARGE-B 뒤 모두 고정되고 champion 하나만 FINAL을 한 번
읽어야 한다.

## 10. common-row 필요성

candidate $f$가 자기에게 어려운 anchor만 abstain하면 선택 score가 인위적으로 오를 수
있다. stage survivor set $\mathcal F_j$에 대해

$$
\mathcal A_j=\bigcap_{f\in\mathcal F_j}\mathcal A_f
$$

를 사용하고 candidate coverage가 base anchor의 95% 이상이어야 한다. row 부족은
`ABSTAIN`이지 성능 0이 아니다.

시간축의 overlap은 nominal row를 독립 표본으로 만들지 않는다. screen은 recording별
row loss를 먼저 하나로 집계한 선택용 point score만 쓰고 p-value를 만들지 않는다.
FINAL의 primary statistic도 두 recording-level paired difference의 최솟값이다.
training autocorrelation에서만 고정한 block length로 각 recording의 conditional temporal
interval을 만들 수 있지만 recording 두 개로 animal population inference를 할 수는 없다.
최대 지위는 developmental held-out evidence다.

## 11. 계산 경로

weighted centered sample matrix $B_t$의 열 수를 effective support $W_f$라 하면 nonzero
eigenvalue는 $B_t^{\mathsf T}B_t$의 고유값으로 얻을 수 있다. candidate당 dense
$N\times N$ decomposition 대신 대략

$$
O(TNW_f^2+TW_f^3)
$$

시간과 $O(NW_f)$ working memory가 가능하다. EXP/BIEXP sufficient statistics는 재귀로
더 줄일 수 있다. POWER의 긴 tail이 reference보다 4배 이상 느리면 계약의 compute
gate에서 제거될 수 있다. runtime 탈락은 생물학적 반례가 아니다.

## 12. 반례ㆍ중지 목록

- negative kernel weight: outer-product 합의 PSD 증명이 깨진다;
- pairwise denominator: 명시적 3-by-3 correlation matrix에서 최소 고유값 $-0.8$인
  predecessor 반례가 있다;
- $n_{\rm eff}=1$: covariance denominator가 0이다;
- $q=0$인 과거뿐인 anchor: weight 합이 0이므로 abstain한다;
- future-centered filter: causal prediction에 사용할 수 없다;
- screen 뒤 kernelㆍ$\lambda$ㆍridgeㆍfeature mutation: final selection leakage다;
- covariance 우세를 edge, loop, consciousness로 해석: 관측 식별성 범위를 넘는다.

수학 판정: **PASS conditional on exact candidate manifest and fail-closed implementation**.
