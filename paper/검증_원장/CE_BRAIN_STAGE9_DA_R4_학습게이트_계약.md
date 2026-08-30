# CE-BRAIN Stage 9 DA R4 학습게이트 개발 계약

Status: `PREREGISTERED_PRE_DA_VALUE_SCORE`

## 질문과 자료 분할

DANDI `001632@draft`의 dLight1.3b cohort에서 하루의 dopamine cue response가 다음날 행동 학습을 추가로 예측하는지 묻는다.

- development: 60sD F7/F11/F8, 600sD F8/F10/F7/M8 — 7 animals
- calibration: 60sD F9, 600sD F6 — 2 animals
- confirmation: 60sD M7/M8, 600sD M9/F9 — 4 animals, 미개봉 유지

R4는 development만 사용한다. 7 animals 모두 day01~day08이 있고 공식 SHA-256이 일치해야 한다. inventory 사전 감사에서 `60sD-F8`의 day02만 `day02a`, `day02b` 두 자산으로 나뉜 것이 확인됐다. 두 조각은 NWB `session_start_time` 순으로 이어 하나의 day02로 집계한다. 따라서 입력은 7 animals·8 days·57 assets다.

## 고정 신호

event code 15·flag 0을 CS+ onset, code 10·flag 0을 sucrose delivery, code 1을 lick onset으로 쓴다. 각 cue 뒤 첫 reward와 짝짓고 0.5~3.0초 밖의 pair는 제외한다.

trial별 행동은 cue부터 reward까지 lick onset 수를 구간 길이로 나눈 anticipatory lick rate다. 하루 값은 trial median이다.

photometry는 `processing/photometry/photometry_dff`를 쓴다. trial별 cue dopamine은 cue 전 `[-1,0)`초 median을 뺀 cue 뒤 `[0,1)`초 mean이며, 하루 값은 trial median이다. 하루 적격 trial이 4개 미만이거나 photometry timestamp가 단조롭지 않으면 장치 중단한다.

day t의 feature로 day t+1 행동을 예측해 animal당 최대 7행을 만든다.

## 경쟁 모델

모든 연속 feature는 outer-train animal에서만 표준화하고 ridge `alpha=1`을 고정한다.

- `P`: 다음날 행동 = 오늘 행동인 persistence.
- `B`: intercept + log10(ITI) + day + 오늘 행동.
- `C`: B + 오늘 cue dopamine.
- `S`: C와 같지만 각 animal의 dopamine day를 고정 +3일 circular shift한 시간불일치 대조.

평가는 leave-one-animal-out prediction RMSE다. 각 동물의 행을 한 묶음으로 bootstrap 1,999회, seed `20260909`로 재표집한다.

## 사전 판정

다음을 모두 만족할 때만 `DEVELOPMENT_DOPAMINE_UPDATE_SIGNAL_SUPPORTED`다.

1. 7 animals와 각 animal 5개 이상의 day transition.
2. C가 B보다 RMSE를 5% 이상 줄이고 animal-bootstrap 95% 하한 >0.
3. C가 P보다 5% 이상 줄이고 하한 >0.
4. C가 S보다 3% 이상 줄이고 하한 >0.
5. outer fold 7개 중 6개 이상에서 표준화 cue-dopamine coefficient가 양수.

coverage 실패는 `STAGE9_DA_COVERAGE_STOP`, 그 밖의 실패는 `DOPAMINE_UPDATE_SIGNAL_NOT_ESTABLISHED`다.

## 주장 상한

통과는 recorded dopamine이 reward interval·day·current behavior를 넘는 next-day predictive information을 가진다는 development 관찰 결과다. dopamine causality, 모든 neuromodulator, hippocampal memory trajectory, chemical concentration 자체를 증명하지 않는다. 확인 승격에는 calibration을 먼저 통과하고 confirmation을 별도 계약으로 열어야 한다.
