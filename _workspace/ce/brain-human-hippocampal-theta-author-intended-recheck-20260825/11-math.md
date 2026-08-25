# 수학 레인 — 시간축 반례, QC 정의역, 기술적 endpoint

Status: COMPLETE

## 시간축 반례

저자 코드의 1000-point grid는

$$
\operatorname{linspace}(0,1000/500,1000)_j
=\frac{2j}{999}=\frac{j}{499.5}.
$$

따라서 0.5 s shift 뒤의 시간은 $t_j=j/499.5-0.5$이다. BrainVision header의
sample period $2002.002002\ \mu\mathrm{s}=1/499.5\ \mathrm{s}$와도 일치한다.
선행 구현은

$$
t^{old}_j=\frac{j}{999}\frac{1000}{499.5}-0.5
$$

를 사용했다. 그 step은 약 $2.004006$ ms이고 올바른 $2.002002$ ms와 다르며,
$j=998$에서 $t^{old}_{998}-t_{998}\approx1.999998$ ms이다. 원 raw grid에서
선행 기저가 제거하는 유효 주파수는 약 $f(499.5/499.0005)$이므로 nominal
60/120/180 Hz가 약 60.060/120.120/180.180 Hz로 이동한다. 마지막 retained
sample의 위상 편차는 각각 약 43.2, 86.4, 129.6 degree이다. 이는 완전한
수학 반례이므로 선행 count를 author-time count로 해석할 수 없다.

## DFT 두 표현의 동등성

교정 grid의 999 samples에서

$$
999\frac{60}{499.5}=120,\qquad
999\frac{120}{499.5}=240,\qquad
999\frac{180}{499.5}=360
$$

은 모두 정수이다. 따라서 constant와 세 주파수의 sine/cosine 열은 full-period
discrete grid에서 서로 직교한다. 실수 design matrix

$$
X=[\mathbf 1,\sin(2\pi f_kt),\cos(2\pi f_kt)]_{k=1}^3
$$

에 대한 least-squares projection에서 constant를 되돌린 결과와, 평균을 뺀 뒤
$e^{i2\pi f_kt}$의 complex amplitude를 적합해 실수부를 빼고 평균을 되돌리는
FieldTrip `dftreplace='zero'` 표현은 exact arithmetic에서 같은 직교 projection이다.
구현 A/B의 finite-precision 파형과 mask 비교는 이 조건부 동등성의 수치 검증이다.

p17의 direct-form `filtfilt`와 SOS `sosfiltfilt`는 같은 10차 Butterworth transfer
function을 두 수치 표현으로 적용한다. padding·initial-condition 구현이 정확히 같은
MATLAB binary라는 정리는 없으므로, 동일 scaling/padding 아래 모든 selected
QC·endpoint·bipolar trace의 모든 block×999 samples를 DFT+LPF 직후 비교하는
파형 허용오차와 bitwise mask gate를 경험적 falsifier로 둔다. 통과해도 exact
FieldTrip-version parity를 뜻하지 않는다.

## 정수 mask 검산

$t_j=j/499.5-0.5$와 각 closed/open inequality를 대입하면 다음이 나온다.

- first999: $j=0,\ldots,998$.
- nearest latency `[-.4,.8]`: $j=50,\ldots,649$.
- amplitude: $j=50,\ldots,224$ 또는 $275,\ldots,649$.
- kurtosis: $j=275,\ldots,649$.
- early closed window: $j=258,\ldots,274$.
- late closed window: $j=275,\ldots,374$.
- prestim closed window: $j=100,\ldots,199$.
- nearest baseline `[-.05,-.01]`: $j=225,\ldots,245$.

Baseline correction은 trial마다 시간에 무관한 상수를 빼므로 같은 window 안의
P2P를 바꾸지 않는다. 즉 baseline endpoint의 nearest semantics는 waveform level
재현에는 필요하지만 trialwise와 mean-waveform P2P 자체에는 영향을 주지 않는다.

## QC 논리와 최소 정의역

QC channel $c$, trial $i$의 reason indicator를 $a_{ic},k_{ic},z_{ic},u_{ic}$라
한다. 각 indicator는 amplitude $\ge500$, Pearson kurtosis $\ge5$, any-sample
$|z|>5$, nonfinite를 뜻한다. clinical keep mask는

$$
q_i=1-\bigvee_c(a_{ic}\vee k_{ic}\vee z_{ic}\vee u_{ic})
$$

이고 bipolar는 단일 difference trace에 같은 식을 쓴다. 각 reason은 원래
channel×trial mask와 channel을 OR한 trial-union mask를 모두 기록한다. 선행
HPC4 reason count와의 비교에는 channel×trial count를 사용한다. reason count는 서로
겹칠 수 있으므로 합이 excluded-trial 수와 같을 필요가 없다. 선행 실제 p17 두
실패에서는 final excluded set이 amplitude set과 같았지만, 교정 DFT 뒤에는 다시
계산해야 한다.

저자 코드에 없는 20-trial gate는 estimator의 수학 정의역이 아니다. cell mean과
mean waveform은 $n_{clean}\ge1$이면 정의된다. 따라서 clinical primary의 모든
고정 pre/post cell에서 1 이상을 요구하는 것은 outcome threshold가 아니라 분모
0을 배제하는 최소 정의역이다. bipolar는 sensitivity이므로 고정 pre/post cell 중
하나라도 0이면 late/early/prestim/LOO/paired의 partial selection을 허용하지 않고
bipolar bundle 전체를 미정의로 남기며 clinical primary를 삭제하지 않는다.

## 두 P2P estimand

trialwise estimand는

$$
\bar P_W=\frac1n\sum_{i=1}^n
\left(\max_{j\in W}x_{ij}-\min_{j\in W}x_{ij}\right)
$$

이고 predecessor-compatible sensitivity는

$$
P^{mean}_W=\max_{j\in W}\bar x_j-\min_{j\in W}\bar x_j.
$$

max의 convexity와 min의 concavity로 $P^{mean}_W\le\bar P_W$이다. 두 값은 같은
estimand가 아니며 하나를 다른 하나의 exact replication이라 부를 수 없다.
primary는 공개 `compute_p2p.m`의 trialwise 구조를 따르는 $\bar P_W$이고,
$P^{mean}_W$는 선행 분석과의 민감도 비교다.

## participant contrast와 불확실성

각 participant의 post-pre 변화 $\Delta_s$를 먼저 만든 뒤

$$
D=\frac14\sum_{s\in TS}\Delta_s-
\frac15\sum_{s\in PB}\Delta_s
$$

를 계산한다. 이 순서는 trial 수가 많은 participant가 arm 평균을 지배하지 않게
한다. p17과 p19는 두 arm에 동시에 있으므로 bootstrap draw마다 일곱 고유
participant에 한 weight만 배정하고 두 arm에서 같은 weight를 재사용해야 한다.
LOO는 한 고유 participant를 삭제하고 남은 각 arm의 분모를 다시 정규화한다.
p17/p19 paired sensitivity는

$$
D_{pair}=\frac12\sum_{s\in\{p17,p19\}}
(\Delta_{s,TS}-\Delta_{s,PB})
$$

이다. 유효 paired sample이 2뿐이므로 기술적 민감도 외 지위는 없다.

Exponential weights를 arm 안에서 정규화한 bootstrap은 Dirichlet(1,...,1)
Bayesian-bootstrap summary와 같다. 65,536 draws의 quantile과 $P(D>0)$은 이 일곱
participant에 조건부인 기술적 불확실성이며, p-value 또는 population causal
interval이 아니다. early, prestim, bipolar, LOO, paired는 모두 primary와 raw
trial 또는 participant를 공유하므로 독립 증거로 합산하지 않는다.

## 수학 판정

시간축 반례는 `PASS`: HPC2/HPC4의 author-parity 해석을 무효화한다. 교정 DFT 두
표현의 동등성은 stated grid에서 조건부 정리이며, LPF와 전체 QC parity는 raw
mask gate가 아직 열리지 않은 `[미완성]`이다. available-clean endpoint는 분모가
존재할 때 잘 정의되지만, 그 결과는 동일 자료 사후탐색 경험식이라는 지위를 넘지
않는다.
