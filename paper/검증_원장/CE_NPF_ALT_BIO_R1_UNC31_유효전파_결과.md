# CE-NPF 대체 생물자료 R1 `unc-31` 유효전파 결과

## 판정

- 판정: `R1_EFFECTIVE_PROPAGATION_NOT_SUPPORTED`
- 품질 게이트: 통과
- 증거 지위: 고정식에 대한 생물학적 음성 결과. 물리 시냅스·학습 가소성·행동 매개 결과가 아니다.

## 실행 영수증

- 계약: `ALT_BIO_R1_UNC31_v1`
- script: `run_randi_2023_unc31_effective_propagation.py`
- interpreter: Python 3.11.9, NumPy 2.4.6
- seed: `20260901`
- recording permutation: 20,000회
- bootstrap: 10,000회

| 품질 항목 | WT | `unc-31` |
|---|---:|---:|
| 유효 recordings | 101 | 13 |
| holdout recordings | 16 | 6 |
| 유효 자극 | 1,891 | 238 |

## 1차 endpoint

| 항목 | 값 |
|---|---:|
| WT `median(L_m)` | 0.4828073 |
| `unc-31` `median(L_m)` | 0.5901924 |
| `Delta_L = WT - unc31` | -0.1073851 |
| one-sided permutation p | 0.9929004 |
| bootstrap 95% CI | [-0.1674343, 0.0350688] |
| development `Delta_L` | -0.0804067 |
| holdout `Delta_L` | -0.0865695 |

사전 방향은 `Delta_L > 0`이었으나 전체, development, holdout 모두 반대 방향이다. CI도 0을 포함한다.

## 고정 보조 endpoint

- 반응 폭 `B`: WT 0.228916, `unc-31` 0.239437, 차이 -0.010521.
- 정규화 participation ratio `P`: WT 0.117332, `unc-31` 0.112536, 차이 +0.004796.
- source-matched sensitivity: 26 source labels, 중앙 차이 -0.082322, sign-flip p 0.961102.

보조값도 1차 판정을 구제하지 않는다.

## 원래 질문에 대한 답

- 답한 것: `unc-31` 결손이 source-autoresponse로 정규화한 전뇌 noise-whitened 변위 길이를 감소시킨다는 구체식은 이 자료에서 지지되지 않았다.
- 반증된 것: `Delta_L > 0`을 요구한 `ALT_BIO_R1_UNC31_v1` 후보식.
- 반증되지 않은 것: 특정 neuron pair의 extrasynaptic 반응, 비정규화 절대 반응, paper의 kernel 기반 효과, 학습에 따른 연결 변화, 리만기하 일반론.
- 이유: `L_e`는 source response로 나눈 전체 downstream RMS다. `unc-31`이 source autoresponse와 downstream response를 다르게 바꾸면 비율의 방향은 paper의 “기능연결 수”와 같을 필요가 없다.

## 다음 허용 행동

- 같은 R1 식의 창·threshold·정규화를 바꿔 재시도하는 것은 금지한다.
- 다음 독립 질문은 공급자 kernel/response-detection 정의를 그대로 복제하는 별도 계보이거나, Track2p의 발달 동일세포 질문이어야 한다.
- 이 음성 결과로 원 전체 목표를 실패 처리하지 않는다. 다만 “neuromodulator 결손이면 접힌 공간 길이가 단순히 줄어든다”는 단조식은 폐기한다.

