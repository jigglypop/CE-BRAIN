# CE-BRAIN Stage 9 ACh DANDI 001176 직접게이트 장치 감사

Status: `ACH_FAST_DYNAMICS_PRESENT / WRITE_GATE_NOT_IDENTIFIABLE`

기준일: 2026-08-31

## 1. 목표

긴 로드맵 Phase 11의 직접 질문을 검사할 수 있는지 먼저 판정한다.

> 동일한 전기 trajectory라도 ACh 상태가 다르면 이후 장기 변화가 달라지는가?

이 질문에는 같은 자료계에서 최소한 전기 population trajectory, ACh, matched condition, 이후 지속 변화 endpoint가 필요하다.

## 2. 판본과 inventory

- DANDI: `001176@0.260610.2204`
- title: `Cortical acetylcholine dynamics are predicted by cholinergic axon activity and behavior state`
- assets: 132
- subjects: 29
- bytes: 924,191,446
- modality: behavior + optical physiology

## 3. 두 schema 대표 파일

### ACh-only

- file: `sub-22713_ses-22713-2-2-Ach-V1_behavior+ophys.nwb`
- SHA-256: `ff1eca2449c8c8ac56c92b1a00e0ecd5d8a1e121a0d6e0b1ae6fe11d77119075`
- ACh sensor ROI 1개, pupil, eye position, treadmill velocity

### simultaneous cholinergic axon + ACh

- file: `sub-26536_ses-26536-2-2_behavior+ophys.nwb`
- SHA-256: `4074ccfc0529e10743723ad62297916bff7fa41089836949fe7ff7956bc7fb3f`
- GCaMP ROI 1개와 ACh sensor ROI 1개를 동시에 기록
- pupil, eye position, treadmill velocity

## 4. 존재하는 것과 빠진 것

| 축 | 지위 |
|---|---|
| ACh dynamics | 있음 |
| cholinergic axon GCaMP | 있음 |
| pupil/treadmill behavior state | 있음 |
| local ephys population trajectory | 없음 |
| stimulation/pharmacology/trial intervention | 없음 |
| matched electrical trajectory with different ACh | 없음 |
| 이후 지속 synaptic/representational/behavior update | 없음 |

따라서 이 자료는 다음 질문에는 적합하다.

> 현재 cholinergic axon activity와 behavior state가 빠른 cortical ACh 변동을 얼마나 예측하는가?

그러나 다음 질문에는 적합하지 않다.

> ACh가 전기적 복원 궤적을 장기 기억 쓰기로 허가하는가?

## 5. 판정

**[장치 판정]** `ACH_FAST_DYNAMICS_PRESENT_WRITE_GATE_NOT_IDENTIFIABLE`.

이것은 ACh chemical gate의 과학적 실패가 아니라 직접 주장에 필요한 축이 없는 장치 한계다. 논문 제목의 빠른 예측관계를 재현하더라도 CE의 장기 write-permission 증거로 승격하지 않는다.

**[다음 최소 증명 의무]** ephys 또는 명시적 neural trajectory, ACh/DA/NE sensor나 조작, 학습 전후의 지속 변화가 같은 개체·과제에 함께 있는 자료를 찾아야 한다.

공식 자료: <https://dandiarchive.org/dandiset/001176/0.260610.2204>

코드: `examples/brain/ce_brain_ach_apparatus.py`

검증: `tests/test_ce_brain_ach_apparatus.py`
