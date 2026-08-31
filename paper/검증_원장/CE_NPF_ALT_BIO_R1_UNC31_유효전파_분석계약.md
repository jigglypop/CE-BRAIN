# CE-NPF 대체 생물자료 R1 `unc-31` 유효전파 분석계약

## 지위

- 판본: `ALT_BIO_R1_UNC31_v1`
- 선행 게이트: `RANDI_2023_SOURCE_SCHEMA_V2_PASS`
- 상태: endpoint 실행 전 고정
- 목적: dense-core-vesicle 방출 결손이 단일뉴런 자극에 따른 전뇌 유효전파의 noise-normalized 길이를 바꾸는지 동물 단위로 판정한다.

이 계약은 “물리 시냅스 가중치가 학습으로 변해 공간을 접는다”를 직접 검사하지 않는다. 직접 광자극으로 생긴 활동 변위의 유효기하와 `unc-31` 의존성만 검사한다.

## 입력과 분석 단위

- WT identity-usable recordings 112, `unc-31` identity-usable recordings 15.
- recording 하나를 동물 하나의 독립 단위로 둔다.
- GCaMP sample interval은 source gate에서 확인한 0.5 s다.
- source label이 있고 `stim_neurons >= 0`인 자극만 후보로 둔다.

## 자극별 변위

자극 volume을 `s`, receiver neuron을 `i`라 한다. 기준선은 `s-20:s`(10 s), 반응창은 `s+2:s+12`(자극 후 1--6 s)로 고정한다.

\[
b_i=\operatorname{median}F_i[s-20:s],\qquad
\sigma_i=1.4826\,\operatorname{median}|F_i-b_i|,
\]

\[
z_i=\frac{\operatorname{mean}F_i[s+2:s+12]-b_i}
{\sigma_i+10^{-6}\max(1,|b_i|)}.
\]

- 각 창에서 유한값이 80% 이상인 세포만 사용한다.
- source autoresponse가 `z_source >= 2`인 자극만 통과한다.
- 식별된 downstream neuron이 최소 20개여야 한다.
- 극단값 영향은 `z_i`를 `[-20,20]`으로 고정 절단한다.

## 1차 endpoint: 유효 접벡터 길이

식별된 downstream 집합을 `I_e`, 그 수를 `N_e`라 할 때

\[
L_e=\frac{\sqrt{N_e^{-1}\sum_{i\in I_e}z_i^2}}
{\min(z_{source},20)}.
\]

이는 baseline noise로 whitening한 국소 활동변위의 RMS 길이를 source autoresponse로 나눈 값이다. recording 값은 유효 자극들의 중앙값 `L_m`이다. recording당 유효 자극이 3개 미만이면 제외한다.

주효과는

\[
\Delta_L=\operatorname{median}_{m\in WT}L_m-
\operatorname{median}_{m\in unc31}L_m
\]

이며 사전 방향은 `Delta_L > 0`이다.

## 통계와 holdout

- genotype label을 recording 단위로 섞는 one-sided permutation 20,000회, seed `20260901`.
- recording을 집단 안에서 재표집하는 bootstrap 10,000회로 95% CI.
- `sha256(ds_name)` 첫 32-bit 정수를 5로 나눈 나머지가 0이면 holdout, 아니면 development다. 이 분할은 결과값과 무관하다.
- 전체 주효과 외에 development와 holdout에서 `Delta_L` 방향이 모두 양수여야 한다.

품질 게이트는 유효 recording이 WT 80 이상, `unc-31` 10 이상, holdout이 WT 15 이상, `unc-31` 2 이상이다.

## 보조 endpoint

\[
B_e=N_e^{-1}\sum_{i\in I_e}\mathbf 1(|z_i|\ge2)
\]

는 반응 폭이고,

\[
P_e=\frac{(\sum_i z_i^2)^2}{N_e\sum_i z_i^4}
\]

는 정규화 participation ratio다. 이 둘과 source-label별 matched sensitivity는 해석 보조이며 주 판정을 뒤집지 않는다.

## 판정

- `R1_EFFECTIVE_PROPAGATION_SUPPORTED`: 품질 게이트 통과, `Delta_L>0`, permutation `p<0.05`, bootstrap CI 하한 `>0`, development/holdout 방향 모두 양수.
- `R1_EFFECTIVE_PROPAGATION_NOT_SUPPORTED`: 품질은 통과하지만 위 결합조건 실패.
- `R1_BLOCKED_QUALITY`: 품질 게이트 실패. 이 경우 생물학적 음성으로 세지 않는다.

양성이어도 증거 상한은 L2다. `unc-31`은 발생·전신효과를 가진 유전자 결손이고, 자연행동·학습·동일개체 구조 연결·물리 전도속도를 이 자료가 함께 측정하지 않기 때문이다.

