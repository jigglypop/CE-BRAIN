# BA-OBS-ID3 route decision — 실제 인간 뇌의 제한된 능동 응답

Status: COMPLETE

## 선택 기준

이번 run의 첫 목적은 새 식을 관측값에 맞춰 만드는 것이 아니다. 실제 개입 입력과
독립 trial 반복이 있으면서, 결과를 보기 전에 input/output 좌표와 반증 통계를 고정할 수
있는 가장 작은 인간 뇌 자료를 선택하는 것이다. 전체 Hilbert metric 복원 대신
"aligned finite response가 self-adjoint compression처럼 보인다"는 P1 하나만 시험한다.

| route | disposition | reason |
|---|---|---|
| OpenNeuro `ds003708` single-subject CCEP derivative | SELECTED | 실제 인간 intracranial electrical intervention, 반복 trial, 공개 BIDS metadata, 약 2.9 GB의 감당 가능한 신호 객체가 한 판본에 함께 있다. |
| 동일 24개 bipolar pair를 stimulation·receiver 좌표로 정렬 | SELECTED | $A_{r\leftarrow s}$와 $A_{s\leftarrow r}$를 같은 node set에서 비교할 수 있는 최소 apparatus다. |
| A-CAR contact-magnitude 평균 + bipolar difference | SELECTED MATCHED CONTROL | reference에 의존하는 결론과 두 readout 모두에서 남는 결론을 분리한다. |
| raw reciprocal/split-half ratio $R$ + heteroscedastic restricted-null calibration | SELECTED AFTER P0 REVISION | 방향별 precision 차이가 raw $R$를 키우는 false refutation을 막으면서 동결된 effect tolerance를 유지한다. |
| prestimulus, distance, late-window controls | SELECTED CONTROL | evocation 부재, 근접 artifact/volume conduction, 시간창 특이성을 구분한다. Primary verdict는 바꾸지 않는다. |
| OpenNeuro `ds004457` multi-subject CCEP | HELD-OUT REPLICATION | 다섯 피험자로 일반화에 더 적합하지만 약 11.5 GB이며, 이번 작은 apparatus를 본 뒤 별도 계약·독립 split으로만 연다. |
| OpenNeuro `ds002094` TMS-EEG | DEFERRED | 비침습 population validation에는 유용하나 약 39.4 GB이고 scalp forward/reference 문제가 현재 질문과 다르다. |
| OpenNeuro `ds007095` RNS longitudinal stimulation | DEFERRED | 장기 dynamics 질문에는 적합하지만 지금의 reciprocal pair matrix와 apparatus가 다르다. |
| 로컬 C. elegans whole-brain calcium | REJECTED FOR THIS CLAIM | 실제 whole-brain 자료지만 수동 관측이며 human electrical intervention·aligned reciprocal input을 제공하지 않는다. |
| 로컬 AISynPhys 경로 재사용 | KILLED BY PREDECESSOR | 원 raw가 없고 이전 판본은 current-clamp와 voltage-clamp 단위 혼합으로 해석 불가능했다. |
| finite CCEP matrix로 무한차원 metric·dimension 복원 | PROHIBITED BY BA-OBS-NOGO1/ID2 | 24-node finite observation은 unobserved tail을 제거하지 못하며 countably complete query도 아니다. |
| 결과를 보고 window/site/threshold/reference retune | PROHIBITED | discovery와 confirmation을 섞고 실패한 식을 같은 자료에 과적합한다. |

## 동결 경로와 kill 순서

1. Source identity와 metadata SHA-256이 하나라도 다르면 `SOURCE_IDENTITY_STOP`이다.
2. Real sample을 열기 전에 symmetric, directed-asymmetric, null-evocation, truncated-range,
   wrong-hash fixture를 같은 decoder/statistic code path로 통과시킨다.
3. Hash split의 pair 방향은 frozen 24-site list의 index 순서이며 lexical sort를 금지한다.
   Calibration 151 endpoint는 계산하지 않는다. Development 42 pairs에서 두 readout 모두 repeatability, early/pseudo
   evocation, byte integrity, endpoint completeness를 통과해야 한다.
4. Development가 실패하면 confirmation 52 pairs의 통계는 계산하거나 직렬화하지
   않는다. 이 경우 결과는 이론 반증이 아니라 `APPARATUS_OR_EVOCATION_STOP`이다.
5. Development가 통과한 경우에만 confirmation을 한 번 연다. 두 reference에서 모두
   raw $R>1.25$이고 방향·half 이분산성을 보존한 restricted-null tail
   $p_R\le0.025$일 때만 P1을 reference-robust하게 기각한다. 기각하지 못해도 metric
   확인이나 symmetry 증거가 아니다.
6. 두 readout의 판정이 갈리거나 interval이 경계를 가로지르면
   `REFERENCE_SENSITIVE_OR_INCONCLUSIVE`로 닫는다.
7. Real signal 전에 256-seed heteroscedastic null에서 scenario별 false refutation
   $\le7/256$, log-gap $\log(1.6)$ power fixture에서 scenario별 detection $\ge205/256$를
   요구한다. 실패하면 실제 P1 verdict를 열지 않는다.
8. 어느 결과에서도 window, pair set, seed, resample count, 1.25 또는 0.025 threshold를 이
   run에서 바꾸지 않는다. 후속 multi-subject 검증은 `ds004457` 새 계약으로 분리한다.

## 선택한 경로의 논리 위치

BA-OBS-ID2의 exact theorem은 countably complete quadratic oracle에서

$$
\{Q_G(f)\}_{f\in\mathscr D}\Longrightarrow M=G^{-1}
$$

를 준다. ds003708은 그 oracle이 아니다. 이번 경로는 오직 finite observed matrix의
필요조건 후보

$$
P1:\quad A_{r\leftarrow s}=A_{s\leftarrow r}
$$

를 시험한다. P1이 실패하면 이 CCEP readout을 self-adjoint mobility block으로 직접
읽는 단순 대응이 실패한다. P1이 버티면 더 강한 명제가 생기는 것이 아니라 다음
falsifier를 실행할 자격만 남는다.

## Claim ceiling

SINGLE_SUBJECT_HUMAN_CCEP / FINITE_RESTRICTED_OBSERVED_RESPONSE_RECIPROCITY_FALSIFIER /
REAL_INTERVENTIONAL_DATA / NO_AMBIENT_OR_INFINITE_DIMENSIONAL_METRIC_RECOVERY /
NO_POLARIZATION_TOMOGRAPHY / NO_POPULATION_GENERALIZATION /
NO_CONSCIOUSNESS_SELF_HIPPOCAMPUS_OR_AGI_VALIDATION
