# CE-BRAIN Stage 8 DANDI 001371 업데이트과제 장치 감사

Status: `UPDATE_TASK_RAPID_CORRECTION_APPARATUS_ELIGIBLE`

기준일: 2026-08-31

## 1. 목표 정렬

DANDI 001371의 Y-maze에서는 첫 단서가 목표 팔을 지시하고, 일부 trial의 두 번째 단서가 기존 목표를 유지하거나 반대로 바꾸라고 지시한다. 이는 exact-item 관계거리와 다른 memory-code family이며, `기존 목표의 유지 → 새 정보 뒤 선택 수정`을 직접 관찰할 수 있다.

다만 이 과제의 두 번째 단서는 한 trial 안의 선택을 바꾼다. 장기간 유지되는 `F→F'`, `G→G'`, `W→W'`를 자동으로 뜻하지 않는다. 따라서 첫 claim ceiling은 **within-trial rapid correction**이다.

## 2. 자료와 분할

- DANDI `001371@draft`: valid draft, 66 assets, 7 subjects, 14.537 TB
- 모든 asset은 `behavior+ecephys.nwb`이며 CA1·mPFC 기록과 명시적 trial table을 포함한다.
- trial columns에는 `update_type`, `turn_type`, `choice`, `correct`, `t_update`, `t_choice_made`가 있다.
- `update_type`: 1=delay only, 2=switch, 3=stay

subject ID SHA-256 정렬로 다음을 endpoint-blind하게 고정했다.

- development: S34, S29, S20, S25
- calibration: S17
- confirmation: S33, S28

## 3. development 장치 문턱

한 세션이 다음을 모두 만족해야 한다.

- switch 30 trials 이상
- stay 10 trials 이상
- CA1 20 units 이상
- PFC 20 units 이상

| 세션 | 전체 | delay only | switch | stay | CA1 | PFC | 판정 |
|---|---:|---:|---:|---:|---:|---:|---|
| S34-220623 | 257 | 190 | 51 | 16 | 54 | 50 | 적격 |
| S29-211123 | 104 | 77 | 17 | 10 | 41 | 16 | 중단 |
| S20-210521 | 78 | 62 | 12 | 4 | 78 | 29 | 중단 |
| S25-210916 | 161 | 112 | 34 | 15 | 56 | 30 | 적격 |

이 수치는 원격 HDF5 range read로 trial label과 unit region만 읽어 얻었으며 neural endpoint는 열지 않았다.

## 4. 판정

**[장치 판정]** `UPDATE_TASK_RAPID_CORRECTION_APPARATUS_ELIGIBLE`.

S34와 S25에서 새 representation family를 development 실행할 수 있다. calibration·confirmation은 봉인한다.

**[금지]** rapid prospective-code switch를 지속 학습, 기억 geometry의 영구 변화, 화학적 write gate, 또는 독립 READ/WRITE subspace의 증거로 부르지 않는다.
