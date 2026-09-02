# 자료 충분성 판정과 승인 요청 (Q-NPF-03, 2026-09-02)

목적: 표적 (1)(2)의 계량 수준 endpoint(출력-상대 Fisher 계량의 학습 전후 변화)를 판정할 생물 자료가 있는가.

## 1. 요건

1. 같은 세포 또는 같은 접촉의 학습/개입 전후 종단 등록
2. phase당 충분한 trial 수. 앞선 합성 보정에서 약 1000 trial이 필요했고 60 trial은 검정력 정지였다
3. 계량을 정의하는 출력과 다른, 사전 지정 가능한 행동 endpoint
4. 동기 clock, trial/block 경계, 동물 단위 holdout

## 2. 저장소 보유 자료 (다운로드 없이 재고조사, 36개 디렉터리, 약 93GB)

정본 표: `verify/Q-NPF-03/local_data_inventory.md`. 요약은 아래.

| 자료 | 요건 1 | 요건 2 | 요건 3 | 판정 |
|---|---|---|---|---|
| Ottenheimer 2023 (PL, 8 mice, 354 triplet) | 충족 | 60 trial/phase, 세션 전체 145-225, 3세션 합산 500-675 | 충족(lick) | 부족: 요건 2 (필요량의 약 1/17) |
| Hattori 2023 OFC (Zenodo 10969434) | 공개 npz에 세션 간 세포 등록 키 없음 | 220 trial/세션 x 40-85세션 = 마리당 8800-18700 | 충족(choice, reward) | 부족: 요건 1. 로컬에 imaging npz 1개만, imaging 마우스와 개입 마우스가 서로 다름(FAIL_DISJOINT_COHORTS) |
| Stx3 2026 (CA1, 16 mice) | 충족(day0-day5 ROI 정합) | arm당 7-22 | 충족(VR 보상) | 차단: STX3_TRIAL_COUNT_BLOCKED, 문턱 완화 금지 |
| 그 외 33개 | 종단 등록 없음 또는 trial 구조 없음 | - | - | 부족 또는 차단 (표 참조) |

판정: 적격 자료 없음. 가장 가까운 것은 Hattori 2023(trial 충분, 등록 키 부재)과 Ottenheimer 2023(등록 충족, trial 부족).

## 3. 외부 공개자료 (메타데이터만, 다운로드 없음)

| 후보 | 요건 1 | 요건 2 | 요건 3 | 접근/용량 | 판정 |
|---|---|---|---|---|---|
| Allen Visual Behavior 2P | 세포 종단 충족(cell_specimen_id, FOV당 3-11세션). 단 학습은 imaging 전 3021 훈련세션에서 끝남. familiar/novel은 학습 전후가 아님 | UNVERIFIED(NWB trial table 필요) | 충족(lick, reward, running) | AllenSDK 직접, 탐색 sample 약 500MB(NWB 2개) | 요건 1 불충족 가능성 높음. 단 Novel 1 대 Novel >1 세션이 같은 세포의 새 자극 친숙화 전후로 쓰일 수 있는지는 미확인(주차) |
| Allen VB Neuropixels | 세션 간 unit 동일성 미문서화 | UNVERIFIED | 충족 | 약 300MB | 요건 1 불충족 |
| IBL Brain-Wide Map 2025 | 세션 간 동일세포 미문서화, 학습이 주 조작 아님 | UNVERIFIED | 충족(choice, RT) | CC-BY, AWS, 5-20MB 메타 | 요건 1 불충족 |
| DANDI 일반 | 네 조건 만족 데이터셋 미발견 | - | - | - | 미발견 |

## 4. 결론과 사용자 승인 요청

결론: 저장소 안팎에서 요건 넷을 모두 충족한다고 확인된 자료는 없다. 계량 수준 endpoint는 현재 자료로 판정 불가이며, 이는 가설의 음성이 아니라 자료 한계다.

승인 요청(택일 또는 복수). 새 payload는 사용자가 자료·직접 변수·최대 용량을 명시해 승인할 때만 받는다.

| 번호 | 요청 | 용량 | 판정할 것 |
|---|---|---|---|
| A | Allen VB 2P 마우스 1마리의 Novel 1 세션과 Novel >1 세션 NWB 2개 + cell_specimen 표 | 약 500MB | trial 수, 같은 세포 추적, 새 자극 친숙화가 학습 전후로 사전 지정 가능한지 |
| B | Hattori 2023 원 논문 저장소에서 세포 등록 키가 있는 판본 존재 여부 문의(메타데이터만) | 0 | 요건 1 해소 가능성 |
| C | 새 자료 대신 endpoint 격하(평균반응 운동학) 승인 | 0 | 재귀회로 forward-model에서 미시 기전 판별력 확인 후에만 카드 |

A는 100MB 탐색 규칙을 넘으므로 명시 승인이 필요하다. 승인 전에는 어떤 다운로드도 하지 않는다.
