# BA-OBS-DISC2 routes lane — 실제 뇌 검증 경로와 퇴역 경로

Status: COMPLETE

## 우선순위 판정

| 순위 | 경로 | 식별 질문 | 장점 | kill/보류 조건 | 상태 |
|---:|---|---|---|---|---|
| 1 | `R1_RAW_RANGE_PATIENT_HOLDOUT` | fsaverage geometry 후보가 새 환자의 bipolar five-bin energy를 S0보다 예측하는가 | 74명 raw intervention, 30명 final, exact source identity | apparatus/D0/D1/D2/D3 계약 gate 중 하나 실패 | `SELECTED` |
| 2 | `R2_NATIVE_TRACT_LATENCY` | native tract length가 N1 latency를 설명하는가 | 전도속도·fiber path에 더 가까움 | 공개 manifest에 subject-native tract가 없고 현재 질문은 energy kernel; 새 source/계약 필요 | `DEFERRED` |
| 3 | `R3_FTRACT_SUMMARY_REPLICATION` | parcel-level 대규모 CCEP atlas에서 attenuation/latency 패턴이 재현되는가 | 수백 환자의 population summary | raw waveform·동일 endpoint 없음; 로그인/요약자료라 primary confirmation 대체 불가 | `EXTERNAL_FOLLOWUP` |
| 4 | `R4_DISC1_D3_REUSE` | 기존 한 환자 D3로 수정식을 다시 볼 것인가 | 빠름 | D2를 보고 수정했으므로 confirmation 오염 | `RETIRED_PROHIBITED` |
| 5 | `R5_SIMULATOR_SEARCH` | parser·optimizer가 generating family를 회수하는가 | 장치·null false selection 진단 | 실제 뇌 증거가 아니며 R1 대체 불가 | `CONTROL_ONLY` |

## R1 선택 이유

DISC1의 약점은 edge 수보다 independent participant가 없다는 점이었다. R1은 source effect를
같은 환자 안에서 다시 뽑는 대신 74명을 단계별로 완전히 갈라 population generalization을
직접 시험한다. raw BrainVision은 269 GB 전체를 받지 않고 선택된 5,920 trial windows만
VersionId-locked HTTP Range로 읽을 수 있다. 한 trial range에 모든 channel이 multiplexed로
들어 있으므로 receiver 16개를 늘려도 network byte는 늘지 않는다.

실행은 D0의 1,920 windows만 먼저 읽는다. D0 winner가 없으면 나머지 4,000 windows를 읽지
않는다. D1은 640, D2는 960, D3는 2,400 windows이며 각 stage barrier가 통과할 때만 다음
source를 연다. raw payload는 저장하지 않고 endpoint와 byte-range receipt만 남긴다.

## 대안 후보의 퇴역 근거

DISC1의 free $q$는 공통 $\log t$와 구조적으로 중복되고, delay/BIEXP는 boundary에 붙었다.
따라서 threshold나 start만 바꿔 되살리지 않는다. source-specific attenuation random slope도
anchor 4개에서 source intercept와 slope를 동시에 안정적으로 분리하기 어려워 이번 후보에서
퇴역한다. 이 세 경로의 재개 조건은 각각 독립 temporal basis, 직접 latency/tract observation,
source당 더 많은 calibration distances가 있는 새 계약이다.

## 잔차에 따른 다음 경로

- `APPARATUS_STOP`: 식을 고치지 않는다. source alignment, decoding, reference, evocation을
  원인별로 분류한 새 apparatus 판본만 허용한다.
- `D0_NO_SURVIVOR`: 현재 cable/heat grammar를 퇴역한다. symbolic formula를 같은 D0에
  사후 추가하지 않고, native tract 또는 electrophysiological latency라는 새 observable로
  넘어간다.
- `D1/D2_FAIL`: winner를 population candidate로 퇴역한다. 뒤 stage는 미개봉으로 보존하고,
  실패 residual을 보려면 새 run에서 one-structure revision만 허용한다.
- `D3_POST_PASS_PRE_PASS`: baseline/reference geometry confound로 분류하고 확인하지 않는다.
- `D3_PASS`: observed response predictor로만 ledger에 올린 뒤 F-TRACT summary replication과
  native tract route를 별도 confirmation으로 연다.

## Route-lane 결론

현재 가장 정보량이 큰 경로는 R1이다. raw patient-held-out 검증을 통과하지 않은 식을
R2/R3의 요약 통계로 먼저 살리지 않는다. R1이 실패해도 D3 미개봉 여부와 residual class가
다음 판본의 자산이다.
