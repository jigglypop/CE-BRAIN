# Pattern-Jet temporal validation — 실제 시간축 신경 데이터

2026-10-02

## 무엇을 다시 검사했는가

이전의 region rank 실험은 Pattern-Jet 가설을 직접 검사하지 않았다. 그 결과는 본 가설의 검증으로 폐기한다.

이번 질문은 하나다.

> 현재 신경활동 x_t만 알고 있을 때보다, 앞선 상태와의 국소 차이를 여러 시간척도로 보존한 J_K(t)=[x_t,Δ_1(t),...,Δ_K(t)]가 새 개체/세션의 미래 신경상태를 더 잘 예측하는가?

공간 rank는 사용하지 않았다.

## 실제 데이터

DANDI 000981에서 유래한 C. elegans calcium trace의 공개 처리본을 사용했다.

고정 입력:
- source repository: Mighty-Stahl/Extended-Essay-Complete-Processing-Pipeline
- commit: 840b910bc5103badc9bfbceb76408a1456574500
- file: dFF.csv
- Git blob: c85efb78c8aa1b5e2d61445190261bafec19d418
- 완전한 세션: 43
- 각 세션: AVA, AVB × 40 time points
- 간격: 약 0.37594 s
- 원 처리코드: 첫 OP50 onset 뒤 15 s, AVAL/AVAR와 AVBL/AVBR를 각각 bilateral average.

DANDI 000981 자체는 Whole-brain chemosensory responses of both C. elegans sexes 공개 데이터다.
이 연구에서는 위 공개 처리본의 AVA/AVB 부분만 사용한다.

## Pattern-Jet 계산

단계 k의 저역상태를

\[
u_k(t)=a_k u_k(t-1)+(1-a_k)u_{k-1}(t),\qquad a_k=e^{-1/2^k},
\]

u_0=x로 두고,

\[
\boxed{\Delta_k(t)=u_{k-1}(t)-u_k(t)}
\]

를 국소 delta로 쓴다.

따라서

\[
\boxed{J_K(t)=[x_t,\Delta_1(t),\ldots,\Delta_K(t)]}
\]

이다. 이것은 전체 loss의 backprop delta가 아니다.

모든 모델은 같은 선형 readout을 사용한다. 전체 세션 하나를 test로 빼고 나머지 42개에서만 readout을 적합한다. 첫 10 sample은 필터 burn-in으로 버린다. 정규화는 training 세션에서만 계산한다. ridge 1e-9는 수치 안정화 전용이다.

비교군:
- current: x_t만 사용
- lag: 같은 feature 수의 raw lag [x_t,x_{t-1},...,x_{t-K}]
- cascade: 위 Pattern-Jet
- parallel: 동일 시간척도의 병렬 leaky-delta bank
- finite: 순수 유한차분 x, Δx, Δ²x, ...

## 핵심 결과: K=2

미래 예측 horizon은 1, 2, 4 sample, 즉 약 0.376 s, 0.752 s, 1.504 s다.

| horizon | current RMSE | raw-lag RMSE | Pattern-Jet K=2 RMSE | raw-lag 대비 감소 | Jet이 이긴 세션 |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.126601 | 0.099521 | **0.091408** | **8.15%** | **38/43** |
| 2 | 0.136093 | 0.111534 | **0.100916** | **9.52%** | **39/43** |
| 4 | 0.174603 | 0.142650 | **0.129633** | **9.12%** | **37/43** |

raw-lag 대비 exact two-sided sign test:
- horizon 1: p ≈ 2.50×10^-7
- horizon 2: p ≈ 3.11×10^-8
- horizon 4: p ≈ 1.64×10^-6

현재값만 쓰는 모델에 비해서는 K=2의 평균 RMSE가 각각 약 27.8%, 25.8%, 25.7% 낮다.

따라서 이 실제 시간축 데이터에서는 현재 신경값만으로 미래를 읽는 것보다, 국소 이력을 별도 상태로 보존하는 것이 명확히 유리하다. 같은 feature 수의 단순 최근 raw lag보다도 K=2 multi-timescale delta가 더 낮은 held-out 오차를 낸다.

## 그러나 정확한 cascade topology는 아직 식별되지 않았다

같은 K=2에서 cascade와 각 시간척도를 입력 x에서 직접 계산하는 parallel delta bank는 거의 같다.

고정 1e-4 ridge 대조:
- horizon 1: cascade 0.09142035, parallel 0.09143184
- horizon 2: cascade 0.10093038, parallel 0.10094459
- horizon 4: cascade 0.12964911, parallel 0.12967167

차이는 약 10^-4 상대 수준이다.

따라서 이번 자료가 지지하는 범위는

\[
\boxed{\text{현재값} + \text{다중 시간척도 국소 이력 상태}}
\]

이지, Δ_k가 반드시 직전 내부단계만을 직렬로 받아야 한다는 topology까지는 아니다.

즉 고차원 history state는 살아남았지만 exact serial cascade topology는 미식별이다.

## K를 무한히 늘리면 더 좋아지는가

아니다. 이 짧은 40-point 데이터에서는 K=8이 같은 차원의 raw-lag보다 더 좋아지지 않는다.

horizon 4, ridge 1e-4 대조:
- K=1: lag 0.159299, Jet 0.145537
- K=2: lag 0.142557, Jet 0.129649
- K=4: lag 0.131482, Jet 0.127660
- K=8: lag **0.126444**, Jet 0.128285

따라서 이번 결과는 무한차원 자체의 실증이 아니다. 오히려 이 관측시간 범위에서는 유효 이력 차원이 제한돼 있음을 보여준다.

무한고차원은 연속 이력 함수공간의 이론적 극한으로 유지하되, 생물 데이터에서는 필요한 유효 K를 검증으로 선택해야 한다.

## 저장력에 대한 정확한 의미

이번 결과가 직접 보여주는 것은 저장용량(bit capacity)이 아니다.

보여주는 것은

\[
x_t \mapsto x_{t+h}
\]

보다

\[
(x_t,\Delta_1,\Delta_2)\mapsto x_{t+h}
\]

가 새 세션에서 더 정확하다는 것이다.

즉 현재 activity에 소실된 과거 정보가 추가 상태에 남아 있고, 그 정보가 실제 미래 신경상태를 예측하는 데 유효하다.

이것은 Pattern-Jet의 “같은 현재값 뒤에 서로 다른 과거가 숨은 고차원 상태로 남는다”는 핵심에 대한 직접적인 시간축 지지다. 다만 실제 synapse 하나의 저장 capacity나 장기기억 용량을 측정한 것은 아니다.

## 현재 판정

- 유지: 고정 뉴런 + 국소 다중시간척도 history state.
- 실데이터 지지: current-only보다 history state가 held-out 미래 신경상태를 더 잘 예측.
- 실데이터 지지: K=2가 같은 차원의 최근 raw-lag보다 이 데이터에서 더 좋음.
- 미식별: serial cascade와 parallel multi-timescale bank 중 어느 것이 실제 생물 구현인가.
- 미검증: synapse-by-synapse Δ_e,k 전파.
- 미검증: K→∞가 생물학적으로 실제 무한차원이라는 주장.
- 미검증: 이 상태공간의 실제 생물 계량이 CE의 특정 G라는 주장.

다음 직접 검증은 causal synaptic-pair / bouton longitudinal data에서 같은 프로토콜을 실행해야 한다.
