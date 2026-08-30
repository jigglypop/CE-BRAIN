# CE-BRAIN Stage 9 DA R5 학습게이트 개발 계약

Status: `PREREGISTERED_PRE_DA_VALUE_SCORE`

R4의 lick 포트 장치 중단을 보존하고, event meaning의 모든 lick onset code `{1,3,5}`를 행동으로 합친다. 그 밖의 질문·분할·문턱은 R4와 같다.

## 자료

- development: 60sD F7/F11/F8, 600sD F8/F10/F7/M8, 7 animals
- day01~day08, 57 assets. `60sD-F8` day02a/b는 session_start_time 순으로 한 day02로 합친다.
- calibration 2 animals, confirmation 4 animals은 미개봉.

## trial·day 값

CS+는 code 15·flag 0, reward는 code 10·flag 0이다. cue 뒤 첫 reward가 0.5~3.0초인 경우만 짝짓는다. anticipatory lick rate는 cue~reward 사이 code `{1,3,5}` onset 수/구간초이며 day median을 쓴다.

cue dopamine은 cue 전 `[-1,0)` dF/F median을 뺀 `[0,1)` dF/F mean이고 day median을 쓴다. 하루 적격 trial 4개 이상, timestamp 엄격 단조가 필요하다.

day t로 day t+1 행동을 예측한다. `P`는 오늘 행동, `B`는 log10(ITI)+day+오늘 행동, `C`는 B+오늘 cue dopamine, `S`는 dopamine day를 animal 안에서 +3일 circular shift한 대조다. 연속 feature는 outer-train에서만 표준화하고 ridge alpha=1, leave-one-animal-out을 쓴다.

## 판정

`DEVELOPMENT_DOPAMINE_UPDATE_SIGNAL_SUPPORTED`에는 모두 필요하다.

1. 7 animals, animal당 transition 5개 이상.
2. C가 B보다 RMSE 5% 이상 개선, animal-bootstrap 1,999회 95% 하한 >0.
3. C가 P보다 5% 이상 개선, 하한 >0.
4. C가 S보다 3% 이상 개선, 하한 >0.
5. 7 outer fold 중 cue-dopamine 표준화 계수가 양수인 fold 6개 이상.

coverage 실패는 `STAGE9_DA_COVERAGE_STOP`, 나머지는 `DOPAMINE_UPDATE_SIGNAL_NOT_ESTABLISHED`다. 통과해도 관찰적 추가 예측정보일 뿐 dopamine 인과성을 뜻하지 않는다.
