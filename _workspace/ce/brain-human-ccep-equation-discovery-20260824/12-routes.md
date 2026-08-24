# BA-OBS-DISC1 route decision — 작은 발견에서 최종 실제 뇌 검증까지

Status: COMPLETE

## Route table

| route | disposition | reason |
|---|---|---|
| 선행 BA-OBS-ID3 calibration 151 endpoint-blind pairs | SELECTED | 실제 인간 CCEP이며 endpoint를 계산하지 않은 pool이 남아 있다. Raw multiplexed bytes가 과거 traversal되었다는 경계는 유지한다. |
| distance-stratified salted 24/48/39/40 | SELECTED | 사용자가 요청한 약 10% 발견→약 20% 빠른 검증→중간→최종 구조이며 stage distance distribution을 signal 없이 맞춘다. |
| B0 + 14 geometry/electrical candidates | SELECTED | scalar reciprocity 한 식에 고정하지 않고 cable, fixed/free dimension exponent, anomalous distance, delay, anisotropy, direction, biexponential을 빠르게 경쟁시킨다. |
| bipolar RMS energy | SELECTED PRIMARY | common/reference component에 덜 민감한 spatial-gradient readout이며 이전 reference-sensitive 결과의 직접 교정이다. |
| contact-mean RMS energy | SELECTED MATCHED CONTROL | common/reference sensitivity를 숨기지 않고 별도 label로 분리한다. |
| source-cluster bootstrap | SELECTED | 같은 stimulation trials이 여러 receiver pair에 공유되므로 pair-iid inference를 금지한다. |
| held-out geometry joint permutation | SELECTED | temporal fit이 아니라 MNI descriptor의 추가 predictive value를 죽이는 adverse control이다. |
| D1/D2 통과 뒤 numerical-only cumulative refit | SELECTED | 다음 unopened stage의 예측력을 높이되 식 구조·window·threshold는 고정한다. |
| free node/pair gains, symbolic regression | KILLED BEFORE DATA | D0에서 lookup/포화 위험이 크다. |
| failed stage를 보고 같은 run에서 식 변환 | PROHIBITED | 실패 stage가 training으로 오염되므로 새 판본과 독립 pool 없이는 허용하지 않는다. |
| 기존 42 development/52 confirmation pairs 재사용 | REJECTED FOR CONFIRMATION | 그 endpoint는 이미 관측되어 새 식의 독립 검증이 아니다. |
| `ds004457` multi-subject CCEP | HELD-OUT EXTERNAL REPLICATION | 이 run이 D3까지 살아남을 때만 별도 source lock/subject split으로 population 방향을 시험한다. |
| ambient/infinite-dimensional metric recovery | PROHIBITED | finite readout no-go와 measurement confounding이 남는다. |
| consciousness/self/hippocampal hash/AGI | OUT OF SCOPE | 이 자료의 endpoint와 직접 연결되지 않는다. |

## Sequential kill order

1. Contract/source identity/split manifest가 하나라도 다르면 endpoint 전에 stop.
2. Synthetic generating/null/common-reference/barrier/dimensionless fixtures가 실패하면 실제 D0를
   열지 않는다.
3. D0 apparatus gate 실패면 식을 적합하지 않는다.
4. D0 6-fold cross-half comparison에서 geometric survivor가 없으면
   `D0_NO_GEOMETRIC_EQUATION_SURVIVED`; D1–D3은 unopened.
5. D0 winner가 있으면 구조를 봉인하고 D1 48 pairs를 예측한다. Bipolar source-cluster CI 또는
   geometry-permutation gate가 실패하면 즉시 kill; D2/D3 unopened.
6. D1 pass 뒤 숫자만 누적 적합해 D2 39 pairs를 예측한다. 같은 gate 실패면 D3 unopened.
7. D2 pass 뒤 숫자만 누적 적합해 D3 40 pairs를 one-shot 평가한다.
8. Mean/bipolar concordance에 따라 reference-concordant 또는 reference-sensitive label을 붙인다.

## What success and failure mean

- D0 failure: 이 작은 실제 표본에서 시험한 14 geometry candidates 어느 것도 B0보다 안정된
  cross-half edge prediction을 보이지 않았다는 뜻이다.
- D1/D2/D3 failure: 앞 stage에서 발견한 식이 다음 실제 pair에 일반화되지 않았다는 뜻이다.
- Final pass: 특정 observed CCEP energy kernel의 MNI-conditioned held-out prediction pass다.
- 어느 결과도 전류 법칙 전체, $L_g$, Riemannian geodesic, 연속/무한 차원 또는 의식을
  직접 확인하거나 부정하지 않는다.

## Claim ceiling

SINGLE_SUBJECT_HUMAN_CCEP / ENDPOINT_BLIND_DISCOVERY / SEQUENTIAL_HELD_OUT_EDGE_PREDICTION /
OBSERVED_ELECTRICAL_RESPONSE_KERNEL / SOURCE_CLUSTER_UNCERTAINTY /
NO_AMBIENT_OR_INFINITE_DIMENSIONAL_METRIC_RECOVERY / NO_POPULATION_GENERALIZATION /
NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_OR_AGI_VALIDATION
