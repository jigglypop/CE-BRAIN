# 대안 경로 레인 — 교정 재검산 선택

Status: COMPLETE

| ID | 경로 | 장점 | 반례·한계 | 판정 |
|---|---|---|---|---|
| R0 `FROZEN_HPC4_MIN20` | 선행 wrong-grid count와 36-cell MIN20 conjunction 유지 | 거래 receipt는 완전하다. | author/physical time 반례가 있고 endpoint가 없다. PB p17의 실패 cell은 저자 primary가 아닌 local-bipolar sensitivity다. | RETIRED for author-parity; historical apparatus record only |
| R1 `CORRECTED_AVAILABLE_CLEAN` | 교정 grid, 두 독립 수치 표현, clinical available-clean primary, local-bipolar/early/prestim/LOO/paired sensitivity | 자료 손상과 계산 오산을 trial mask 수준에서 가르고 저자 코드에 없는 threshold를 추가하지 않는다. | 동일 공개자료 사후탐색이며 FieldTrip version과 MATLAB fitlme exact parity가 없다. 낮은 count cell의 precision은 약하다. | SELECTED |
| R2 `POSTHOC_MIN10` | 11-trial cell도 임계값을 통과시킨다. | 관측된 11에 맞춘 임의 threshold이며 과학적 근거가 없다. | REJECTED |
| R3 `LITERAL_PUBLIC_SCRIPT` | 공개 코드 자체를 실행한다. | p17/p19 PB 함수 호출에 kurtosis 인자가 빠져 있고 FieldTrip/MATLAB 판본이 잠겨 있지 않다. | BLOCKED; resume only with author environment/version receipt or corrected official release |
| R4 `PUBLISHED_FITLME_PARITY` | 논문과 같은 trial-level mixed model을 겨냥한다. | exact MATLAB engine, FieldTrip commit, 완전한 실행 receipt가 없다. Python 대체 모델은 다른 engine이다. | BLOCKED; report `PUBLISHED_MODEL_ENGINE_UNAVAILABLE` |

선택 경로 R1은 threshold 완화가 아니라 잘못된 measurement clock의 교정과 primary/
sensitivity 정의역 분리다. Stage Q에서 endpoint-free p17 재검산을 먼저 수행하고,
계약에 이미 정한 source/mask gate가 통과할 때만 Stage E가 열린다. corrected count가
20 미만이어도 available-clean endpoint는 계산하며 낮은 trial 수를 정밀도 한계로
전부 공개한다. corrected count나 endpoint를 본 뒤 cohort·contact·window·threshold,
primary estimand 또는 seed를 다시 선택하는 경로는 없다.
