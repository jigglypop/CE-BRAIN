# BA-SRM6 최종 보고서 — 연속 유효차원의 정식화와 첫 실데이터 입력 감사

Status: COMPLETE

Date: 2026-08-23

Final verdict: **FORMALIZATION_COMPLETE / INPUT_CONTRACT_STOP / REAL_ENDPOINT_UNOPENED**

## 무엇이 확정되었나

“뇌의 연결 상태는 매우 높거나 무한한 차원에 있고, 한 순간에는 어떤 더 작은
차원으로 선택될 수 있다”는 아이디어에서 먼저 분리해야 할 것은 차원의 종류다.
매끄러운 리만 다양체의 차원과 projector의 rank는 정수다. 반면 관측된 neural
population이 특정 해상도에서 실제로 쓰는 자유도의 수는 연속값일 수 있다.

BA-SRM6은 후자를 다음처럼 정식화했다. 길이 $W$의 인과적 calcium window에서
중심화한 관측 공분산을 $G_t$라 하고, train에서 정한 scale $c_G$로
$\widetilde G_t=G_t/c_G$를 만든다. 그러면

$$
S_{t,\lambda}=\widetilde G_t(\widetilde G_t+\lambda I)^{-1},
\qquad
d_{\mathrm{eff}}(t;\lambda)=\operatorname{tr}S_{t,\lambda}
=\sum_k\frac{\mu_{t,k}}{\mu_{t,k}+\lambda}.
$$

고유값 하나가 해상도 $\lambda$보다 크면 약 1, 작으면 약 0으로 기여하기 때문에
$d_{\mathrm{eff}}$는 정수 rank를 부드럽게 만든 유효 자유도다. 숫자 4를 선험적으로
고정하지 않고 시간과 scale에 따라 연속적으로 변할 수 있다. 다만 이것을 “3.7차원
리만 다양체”라고 부르면 안 된다. 정확한 이름은 **관측 calcium quotient의
scale-dependent soft spectral dimension**이다.

유한 관측공간에서는 $G\succeq0$, $\lambda>0$일 때
$0\le d_{\mathrm{eff}}\le\operatorname{rank}G$이고 $\lambda$에 대해 연속ㆍ단조
감소한다. 진짜 무한차원 Hilbert 공간으로 올리려면 $G$가 positive self-adjoint
trace class여야 한다. compact하다는 조건만으로는 trace가 발산할 수 있다.

관측 selector로부터

$$
A_{t,\lambda,\epsilon}=\epsilon I+(1-\epsilon)S_{t,\lambda}
$$

를 만들면 양정 정부호 inner product가 되지만, 이것은 뇌가 실제로 쓰는 metric을
발견한 것이 아니라 관측 quotient에 분석자가 넣은 정규화다. 더구나 covariance는
window 안의 시간 순서를 지우므로 이 식만으로 directed synapse, recurrent route,
해마의 hash/index 기능 또는 의식을 알아낼 수 없다.

## 뇌 실데이터 전에 어떻게 검증하도록 설계했나

검증 사다리는 세 층으로 동결했다.

첫째, L0-A는 행렬 수준의 성질을 검증한다. $S$의 PSDㆍcontraction,
$d_{\mathrm{eff}}$의 범위와 $\lambda$ 단조성, 직교 재좌표화 불변성, regularized
inner product의 양정 정부호성, zero/nonfinite/negative-spectrum 입력의 fail-closed,
모든 지수와 정규화의 무차원성을 float64 상대오차 $10^{-10}$에서 시험한다.

둘째, L0-B는 정답을 아는 합성 시계열을 쓴다. 12개 관측 채널, window 96, 32개
고정 seed에서 soft spectrum을 연속적으로 바꾸고 calcium convolutionㆍnoiseㆍdropoutㆍ
회전 basisㆍhard-rank jumpㆍtime reversal을 가한다. 복원 목표는 숨은 뉴런의 “진짜
차원”이 아니라 측정 과정을 지난 관측 covariance의 같은 resolvent trace다. median
Spearman 0.90 이상, 5th percentile 0.75 이상, normalized MAE median 0.15 이하를
통과선으로 정했다.

셋째, L0-C는 실제 train calcium의 phase-randomized background에 정답을 아는
orthogonal latent signal을 주입한다. 주입 trace/background trace ratio
$\{0,0.5,1\}$에서 연속 soft dimension 2→8의 회복성과 no-injection false alarm을
검사한다. ratio 1의 median Spearman은 0.75 이상이어야 하고 ratio 0보다 높아야 하며,
false-alarm fraction은 0.01–0.10이어야 한다. 이 단계까지는 분석 장치 검증일 뿐
생물학적 증거가 아니다.

이 세 단계 뒤에만 실제 future locomotion을 연다. 동일 rowㆍ동일 ridge budget에서
AR baseline, fixed $d\in\{2,4,8,16,32,48\}$, fixed 4, participation ratio, raw
spectrum, red channel, phase randomization, behavior shift, time reversal, GFP를 모두
대조하도록 설계했다. 두 held-out recording에서 모두 soft model이 최선 대조군보다
$R^2$가 높고 RMSE가 낮아야만 제한적인 developmental predictive evidence가 된다.

## 실제 데이터에서 어디까지 갔나

Hallinen et al.의 public *C. elegans* corpus 세 archive를 새로 받아 bytes와 SHA-256을
확인했고, 11 GCaMP와 11 GFP 기록의 MAT schemaㆍrecording splitㆍclockㆍ미래 horizon을
검사했다. 이 부분은 모두 통과했다.

그러나 endpoint를 열기 전 마지막 입력 규칙에서 멈췄다. 계약은 각 기록의 first-60%
calibration prefix에서 neuron별 `Ratio2` finite fraction이 0.75 이상이어야 한다고
고정했다. train 기록 `BrainScanner20200130_105254`의 최고값은 0.654645,
validation 기록 `BrainScanner20200310_141211`의 최고값은 0.630992였다. 따라서 두
기록 모두 eligible primary neuron이 0개였다.

이 사실을 본 뒤 문턱을 0.6으로 낮추면 데이터에 맞춘 사후 수정이다. red `R2`는
완전하지만 nuisance channel이므로 primary calcium으로 바꿀 수도 없다. 그래서
BA-SRM6은 모델을 적합하지 않았고, validation/held-out score도 열지 않았다.
`R^2`, RMSE, $\Delta R^2$가 보고되지 않은 이유는 성능이 나빠서가 아니라 **과학적
endpoint가 미개봉 상태**이기 때문이다.

## 현재 위치와 다음 판본

현재 위치는 “개념만 있는 단계”보다 한 단계 앞이다. 연속 유효차원 operator,
무한차원에서 필요한 trace-class 조건, 관측 metric의 한계, 합성ㆍ준모의ㆍ실데이터
검증 순서와 반증 기준까지는 닫혔다. 반면 실제 calcium에서 predictive value가
있는지는 아직 한 번도 시험되지 않았다.

다음 BA-SRM7은 원저자 공개 코드의 exact revision을 먼저 고정하고 그 코드가
`Ratio2` 결측을 어떻게 다루는지 확인한다. 그 근거로 missingness rule을 endpoint
개봉 전에 하나만 등록한다. BA-SRM6의 실패한 0.75 rule은 sensitivity control로
남긴다. 새 input gate와 L0-A→L0-B→L0-C가 순서대로 통과할 때에만 real-data fit과
held-out score로 진행한다.

이 결과는 의식, 해마 hash, 시냅스 구조, causal routing 또는 AGI를 지지하지 않는다.
그 주장들은 각각 의식 report/perturbation, hippocampal reinstatement, connectome과
intervention이 있는 별도 데이터 계약을 요구한다.
