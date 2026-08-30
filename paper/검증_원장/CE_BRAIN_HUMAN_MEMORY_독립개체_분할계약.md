# CE-BRAIN Human Memory 독립개체 분할 계약

Status: `OUTCOME_BLIND / SUBJECT_SPLIT_LOCKED`

기준일: 2026-08-31

## 목적

P19HMH 한 사람의 관계복원 미통과를 보고 분석창이나 문턱을 고치지 않는다. DANDI 000004 전체 59 subjects를 결과와 무관하게 분할하고, 동일 R1 분석기를 다음 unopened development subject에 적용한다.

## inventory

- 판본: `000004@0.220126.1852`
- assets: 87
- subjects: 59
- total bytes: 6,197,474,020

subject 역할은 `SHA256("ce-brain-human-memory-v1:" + subject)`의 앞 32bit를 `[0,1)`로 바꿔 고정한다.

- `<0.60`: development
- `0.60–<0.80`: calibration
- `≥0.80`: confirmation
- 이미 결과를 본 P19HMH는 hash와 무관하게 `development_opened`로 강등 고정

결과 역할 수는 unopened development 35, calibration 14, confirmation 9, opened development 1이다.

## 다음 asset 선택

unopened development subjects 중 subject별 최소 asset 크기가 가장 작은 P16HMH를 다음 대상으로 고정한다. 같은 subject에 변환 object가 여러 개면 P19 장치 감사에서 작은 object가 학습 절반만 가진 사례가 있었으므로 **가장 큰 object를 먼저** 연다.

- subject: `P16HMH`
- asset: `cac4440b-ac3f-4ab2-a5de-abaafd426801`
- path: `sub-P16HMH/sub-P16HMH_ses-20071001_obj-1jfnx96_ecephys+image.nwb`
- bytes: 73,367,344
- SHA-256: `29ff7b0cede49b731de90b3741ff456d1cf4220944ccb88f364b5924d39bae2c`

먼저 P19와 같은 100 learning + 100 recognition, exact-old 50, response 31–36, unit 10개 이상 장치 문을 검사한다. 통과하면 `CE_BRAIN_HUMAN_MEMORY_R1_관계복원_계약.md`의 코드·문턱을 바꾸지 않고 적용한다.

P16도 통과해야 confirmation 개방을 검토할 수 있다. 미통과하면 calibration/confirmation은 계속 닫는다.
