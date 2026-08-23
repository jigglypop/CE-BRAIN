# BA-SRM7 최종 보고서 — 무한 과거 상태공간과 source-rooted causal 입력의 경계

Status: COMPLETE

Date: 2026-08-23

Final verdict: **FORMALIZATION_COMPLETE / SOURCE_ROOTED_INPUT_STOP / REAL_ENDPOINT_UNOPENED**

## 무엇을 정식화했나

시냅스를 단일 scalar $W_{ij}$가 아니라 과거 자극ㆍ스파이크ㆍ전압ㆍ상태에 반응하는
함수로 보면 자연스러운 상태는 유한 좌표가 아니라 가중 history Hilbert space다.
BA-SRM7은 neuron별 과거를

$$
\mathcal H_i=L^2\!\left(( -\infty,0],e^{2s/\tau_h}\frac{ds}{\tau_h};
\mathbb R^{p_i}\right),\qquad
\mathcal H=\bigoplus_i\mathcal H_i
$$

에 두었다. edge response는 Volterra operator

$$
(K_{ij}h)(s)=\int_{-\infty}^{s}k_{ij}(s,u;\xi)h(u)\,du
$$

로 쓰고, weighted Hilbert--Schmidt 적분이 유한하다는 충분조건 아래 bounded임을
명시했다. 유한 loop는 이 bounded edge의 product로 정의할 수 있다. 이것은 무한차원
함수 상태의 수학적 틀이지, calcium covariance가 실제 synaptic edge나 directed loop를
복원한다는 뜻은 아니다.

한 순간의 관측 차원에는 숫자 4를 넣지 않았다. causal calcium quotient에서 만든
PSD covariance $G_t$를 train-prefix scale로 무차원화하고

$$
S_{t,\lambda}=\widetilde G_t(\widetilde G_t+\lambda I)^{-1},\qquad
d_{\mathrm{eff}}(t;\lambda)=\operatorname{tr}S_{t,\lambda}
$$

를 썼다. $d_{\mathrm{eff}}$는 시간과 해상도에 따라 연속적으로 변하는 soft spectral
degrees of freedom이다. 리만 다양체의 비정수 차원이나 의식의 차원이라고 부르지
않는다. $A=10^{-3}I+(1-10^{-3})S$도 관측 quotient 위의 분석자 inner product이지
뇌의 내재 metric으로 확인된 것이 아니다.

## 원자료 쪽에서 무엇을 고쳤나

BA-SRM6의 `Ratio2` 0.75 finite-fraction 규칙은 공개 predictor의 실제 입력 경로가
아니었다. 공개 코드의 exact revision을 고정해 확인한 predictor는 raw red/green에서
photobleaching correction과 red-to-green motion decorrelation을 거쳐 smoothed neural
signal을 만든다. BA-SRM7은 이 출발점을 채택하되, 미래 예측을 위해 parameter fit은
각 recording의 앞 60%에만 제한하고 symmetric Gaussian 대신 one-sided causal
Gaussian을 썼다. 그러므로 source-rooted이지만 published preprocessing의 동일 재현은
아니다.

모든 neuron component는 기준 scale로 정규화했고 $\exp$, rate와 resolvent에 들어가는
인자를 무차원화했다. reliability-weighted outer-product covariance를 사용해
pairwise-complete missing covariance의 non-PSD 문제도 core 밖으로 밀어냈다.

## 실제 데이터에서 어디까지 갔나

세 archive, 공개 코드, 22개 MAT schema와 clock은 통과했다. 22개 recording 모두에서
primary와 red causal unit이 남았고 $r_\star=59$였다. BA-SRM6의 “unit 0개” 문제는
source-rooted 입력 개정으로 해결됐다.

다음 단계인 behavior-independent common-anchor lock에서 네 기록이 멈췄다.

| recording | train | validation | test |
|---|---:|---:|---:|
| `BrainScanner20200130_105254` | 214 | 42 | 33 |
| `BrainScanner20200309_151024` | 372 | 107 | 48 |
| `BrainScanner20200310_141211` | 23 | 8 | 0 |
| `BrainScanner20200310_142022` | 555 | 53 | 159 |

계약은 모든 split에 최소 100개를 요구했다. 하나라도 큰 clock gap이 있으면 그 지점을
가로지르는 60-sample window 전체를 폐기하는 hard rule이 표본 손실을 크게 증폭했다.
그러나 이 사실을 확인한 뒤 같은 판본에서 window, gap 또는 하한을 바꾸는 것은 사후
튜닝이다. neural lock은 실패로 고정했고 behavior load, model fit, validation/test
score를 열지 않았다. 따라서 이 판본에는 $R^2$나 $\Delta R^2$가 없다.

## 결과의 의미와 다음 식

현재 위치는 수학 정식화와 source-rooted 측정식은 통과했지만 실제 예측 endpoint 바로
앞의 데이터-viability gate에서 멈춘 단계다. 이는 식이 거짓이라는 증거가 아니다.
오히려 고정 index window가 irregular physical clock와 결측에 취약하다는 구체적인
반례를 얻었다.

후속 판본의 자연스러운 후보는 원래의 무한 과거 서사와 맞는 physical-time causal
weight다. 관측 mask $m_k$, prefix-fixed reliability $D$, bounded robust map $\psi$에
대해

$$
x_k=D[m_k\odot\psi(z_k)],\qquad
w_{kn}=q_k\exp[-(t_n-t_k)/\tau],\mathbf 1_{k\le n},
$$

$$
\mu_n=\frac{\sum_{k\le n}w_{kn}x_k}{\sum_{k\le n}w_{kn}},\qquad
G_n=\frac{\sum_{k\le n}w_{kn}(x_k-\mu_n)(x_k-\mu_n)^\mathsf T}
{\sum_{k\le n}w_{kn}}
$$

처럼 정의하면 $G_n\succeq0$를 보존하면서 결측 한 번이 이웃 window 전체를 죽이지
않는다. 충분한 정보 여부는 raw frame 수가 아니라

$$
n_{\mathrm{eff}}=\frac{(\sum_k w_{kn})^2}{\sum_k w_{kn}^2}
$$

로 판단할 수 있다. 이 식과 threshold는 새 계약에서 synthetic irregular-clock,
block-dropout, artifact spike와 behavior-blind real-background injection을 먼저 통과해야
한다. 그 뒤에만 단계적 real behavior screen과 단일 sealed confirmation을 연다.

이 결과는 synaptic edge, hippocampal hash, consciousness 또는 AGI를 지지하지 않는다.
그 주장에는 connectomeㆍinterventionㆍreinstatementㆍreport 같은 별도 관측 계약이
필요하다.
