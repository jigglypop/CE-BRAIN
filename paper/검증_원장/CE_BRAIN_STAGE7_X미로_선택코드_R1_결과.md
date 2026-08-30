# CE-BRAIN Stage 7 X-미로 선택코드 R1 결과

Status: `APPARATUS_CONTRACT_MISMATCH_EXPLORATORY`

기준일: 2026-08-31

## 1. 판정

두 development session 모두에서 행동 기준선보다 시간 신경모델의 test log loss가 조금 낮았지만, 사전 효과크기와 bootstrap 문턱을 통과하지 못했다. 게다가 계약에 적은 전체 transition 수를 그대로 분석할 것으로 예상했으나 head-direction 결측이 있는 feature 창을 제외하면서 실제 event가 줄었다. 이 제외 규칙과 예상 split의 불일치는 결과를 본 뒤 발견됐으므로 **확인적 실패가 아니라 탐색적 미확립**으로 강등한다.

정본 판정은 `APPARATUS_CONTRACT_MISMATCH_EXPLORATORY`다.

## 2. 결과

| session | 영역 | 계약 event | 실제 event (train/val/test) | B log loss / BA | S log loss / BA | T log loss / BA | T 대 B 개선 (95% CI) |
|---|---|---:|---:|---:|---:|---:|---:|
| BaggySweatpants | MEC | 102 | 87 (52/17/18) | 0.4671 / 0.7778 | 0.6978 / 0.7222 | 0.4540 / 0.7778 | 2.80% [-35.02%, 22.26%] |
| Franklin | hippocampus | 101 | 92 (55/18/19) | 0.3777 / 0.8944 | 0.4148 / 0.8389 | 0.3633 / 0.8944 | 3.81% [-17.21%, 12.22%] |

`B`는 위치·머리방향·속도·sample arm·직전 선택 기준선, `S`는 정적 신경 count 추가, `T`는 네 시간 bin 신경 count 추가다.

Baggy에서 T는 S보다 34.94%, Franklin에서는 12.40% 낮은 log loss였지만 두 bootstrap 하한은 각각 -15.94%, -8.52%로 0을 넘지 못했다. T의 balanced accuracy는 permutation 95 percentile을 넘고 circular-shift T보다 log loss가 낮았지만, 이것만으로 주 문턱 실패를 뒤집지 않는다.

## 3. 쉬운 해석

쥐가 어느 west 팔로 갈지는 현재 위치와 움직임, 방금 있던 east 팔만으로 이미 상당히 예측됐다. 신경세포의 시간 패턴을 더하면 숫자가 약간 좋아졌지만, test 시행이 18~19개뿐이라 우연한 흔들림과 분리되지 않았다. 따라서 “다른 기억 코드가 발견됐다”고 말할 수 없다.

동시에 “그런 코드가 없다”고도 말할 수 없다. 분석 전에 약 100개라고 계산한 이동 중 머리방향 결측 때문에 9~15개를 제외했고, 이 처리 규칙을 계약에 충분히 고정하지 않았다. 엄격한 과학 판정은 새 자료 또는 의미가 명시된 trial log에서 다시 해야 한다.

## 4. 원시 의미 라벨 회수 감사

- DANDI `001701@0.260120.0303`은 218 assets, 6,231,885,174 bytes다.
- 공식 asset 목록은 모두 `*_behavior+ecephys.nwb`이며 별도 Arduino/trial 파일은 없다.
- 공식 GitHub 고정 판본의 recursive tree에도 동물별 원시 task log는 없다.
- NWB exporter는 X Maze trial export 분기가 없다.

따라서 공개 자산만으로 sample/rule/correct/reward 라벨을 복구하는 경로는 현재 확인되지 않았다.

## 5. 다음 증명 의무

1. 저자 원시 Arduino log 또는 trial table을 확보하거나, trial semantics가 이미 포함된 다른 자료를 고른다.
2. 새 계약에서 head-direction 결측 처리와 event 수 문턱을 score 전에 명시한다.
3. 같은 선택문제를 행동 기준선·정적 신경·시간 신경 모델로 다시 경쟁한다.
4. 그 전까지 로드맵 Phase 8 retrieval, Phase 9 capacity, Phase 10 correction으로 승격하지 않는다.

실행 코드: `examples/brain/ce_brain_stage7_xmaze_choice_code.py`

검증: `tests/test_ce_brain_stage7_xmaze_choice_code.py`
