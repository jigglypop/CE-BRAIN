# CE-BRAIN Stage 9 DA R3 D-cohort 장치 계약

Status: `PRE_CHEMICAL_ENDPOINT_SCHEMA`

## 대상

논문에서 nucleus accumbens core의 dLight1.3b dopamine을 측정한 핵심 비교에 맞춰 DANDI `001632@draft`의 `60sD`와 `600sD`만 사용한다. subject 수는 각각 6, 7이다.

기존 inventory와 `SHA256("CE-BRAIN-STAGE9|" + subject)` 순서를 그대로 사용한다.

- 60sD development: F7, F11, F8 / calibration: F9 / confirmation: M7, M8
- 600sD development: F8, F10, F7, M8 / calibration: F6 / confirmation: M9, F9

confirmation은 열지 않는다.

## 첫 스키마 게이트

development hash-order 첫 subject인 `60sD-F7`, `600sD-F8`의 day01만 공식 SHA-256으로 검증한다. 두 파일 모두에서 다음이 존재해야 한다.

1. `acquisition/eventLog` 행동 event.
2. `specifications` 밖의 photometry/dopamine/fluorescence instance와 시계열 shape.
3. subject·session/day 식별자.
4. 같은 subject day02 이상 asset의 inventory 존재.

통과하면 두 development cohort 전체의 값-비개방 schema map으로 이동한다. 실패하면 `STAGE9_DA_DCOHORT_SCHEMA_STOP`이다. dopamine 배열 값과 학습 곡선은 분석 계약 전까지 점수화하지 않는다.

## 주장 상한

이 자료는 관찰적 dLight와 행동 학습의 동시 변화다. held-out animal 예측을 통과해도 dopamine의 인과적 gate를 확립하지 않으며, pharmacological/optogenetic intervention이 별도로 필요하다.
