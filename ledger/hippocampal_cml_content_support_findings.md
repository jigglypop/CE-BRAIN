# CML catFR1: native sample 경로와 실제 기억 내용의 지원

2026-09-20. [앞선 입력 조사](hippocampal_cml_input_findings.md)의 시계 문제를
처리 라이브러리까지 추적하고, 같은 목록의 기억 복원으로 평가할 수 있는 항목을
구분했다. 신호를 보고 유리한 항목이나 전극을 고르지 않았다.

## sample 좌표에서 제한 추출을 진행할 근거

[공식 source 추적](../data/local/hippocampal-reinstatement/cml-sample-origin-audit-v1/sample_origin_audit_result.json)은
snapshot 이전 후보 cmlreaders commit `99c22cca99a701e1c0a85183659dacaba6fcf427`
(2024-04-02, source version0.10.7)을 확인했다. 이 버전과 앞서 확보한 converter는
snapshot과 암호학적으로 연결된 실행 환경은 아니다.

Converter는 events를 읽은 뒤 retrieval offset과 countdown list를 보정하고,
보정된 `eegoffset`을 `sample`로 보존했다. Retrieval 보정은 별도
`offset_corrections.csv`에 따라 회상 사건의 eegoffset에0.5초 또는1초에 해당하는
표본 수를 더하고 mstime도 함께 바꾼다. 어떤 보정이 이 세션에 실제 적용됐는지는
공개 표에서 확인할 수 없다. Countdown 보정은 list만 바꾼다.

Whole-record EEG 경로는 첫 nonempty eegfile 사건을 파일 이름 선택에 사용하고
`rel_start=0`, `rel_stop=-1`, epoch `(0,None)`으로 읽는다. 해당 코드에서 event 시각의
crop이나 resampling은 없고, MNE RawArray는 `first_samp=0`이다. 따라서 이 코드가
사용됐다는 조건 아래 EDF sample0은 선택된 **processed EEG source의 첫 표본**이다.
병원 원 획득 전체의 최초 시각까지 복원한 것은 아니다.

[BIDS1.7의 sample 정의](https://bids-specification.readthedocs.io/en/v1.7.0/04-modality-specific-files/05-task-events.html)는
함께 제공되는 신호 파일의 표본 좌표를 가리킨다. 이 계약, 과거의 무crop 출력 경로와
후속 공식 `sample/Fs` 수정을 근거로 제한된 native-sample 추출은 진행할 수 있다.
독립 sync나 당시 correction 행을 확인했다고 주장하지 않으며, 실패한 행동 onset에
맞추어 임의 offset이나 drift를 추정하지 않는다. 앞선 ‘정렬 미확인’ 판정은 독립
생리적 동기화에 대해서 유지하되 모든 조건부 신호 접근을 금지하는 것으로 확대하지 않는다.

## 내용 라벨 전량의 실제 지원

[고정 metadata 분석](../data/local/hippocampal-reinstatement/cml-content-support-v1/cml_content_support.json)은
사건739행과 채널·전극 표를 해시로 고정했다. 모든 sample은 유한 정수이고
1,362,944..7,069,219로 EDF의 `[0,8640000)` 안에 있다. 순서 역전은0이고 동일한
인접 sample20쌍은 TRIAL/COUNTDOWN_START다. 1600Hz에서 조건부 native 시각은
851.84..4418.261875초다. 이것은 기존 BIDS onset과 다른 숫자 축이다.

| 관측 | 결과 | 내용 복원 질문의 제한 |
|---|---|---|
| WORD | 300개 고유 단어, 25목록×12개 | 같은 항목의 부호화 반복은 없음 |
| 목록 내 범주 | 각3범주×4단어 | 범주 판독만으로 항목 복원을 주장할 수 없음 |
| 전체 범주 | 25범주×12단어 | 목록과 범주를 함께 통제해야 함 |
| REC_WORD same-list | 15회, 고유 list-item13개 | 정답 항목 재등장의 직접 후보 |
| REC_WORD 이전 목록 침입 | 6회, 고유 list-item5개 | 현재 목록 정답과 구별 |
| REC_WORD 목록 밖 침입 | 3회 | 보유 부호화 template 없음 |
| REC_WORD_VV | 111회 모두 `<>` | 발화 시각은 있으나 단어 정체성 없음 |

GIRAFFE/list2, CRAB/list16, LION/list21은 각각 두 번 회상됐다. 이를 독립된 새
기억 항목으로 세지 않는다. 정답·침입·단어 없는 발화를 함께 합쳐 ‘회상135개’의 내용
복원 평가로 만들 수 없다. List/time-block 분할은 가능하지만 한 사람·한 세션으로
사람 간 일반화나 학습에 의한 계량 변화를 평가할 수는 없다. 회상 단어가 있는 목록도
25개 중11개뿐이다. 첫 분석의 표적은 제한된 관측 대응이며 효과의 확증은 아니다.

## 전극 지원과 신호를 보기 전에 고정한 쌍

120 monopolar 이름은 전극 표와 집합이 같고 EDF 순서도 일치한다. Bipolar162개의
모든 구성 contact가 전극 표에 존재한다. 해마 후보는 같은 LOTD depth shaft의
LOTD2..6이다. LOTD2는 das CA1/stein Left CA1, LOTD3..5는 das DG/stein Left DG,
LOTD6은 das n/a/stein Left CA1이다. 모두 ind.region은 n/a다. 두 contact 모두
후보인 인접 bipolar는2–3,3–4,4–5,5–6의 네 쌍이다. 서로 다른 subfield를 가로지르는
쌍을 단일 CA1 또는 DG 관측으로 명명하지 않는다. 저장 좌표를 검증된 물리 거리나
리만 계량으로 사용하지 않았다.

신호 접근 전에 시간순 첫 same-list 정확 쌍을 다음과 같이 고정했다.

| 항목 | 부호화 WORD | 회상 REC_WORD |
|---|---:|---:|
| 원 events의0-based 행 | 31 | 44 |
| native sample | 1,783,142 | 1,854,576 |
| 단어 / 범주 / 목록 | SPARROW / Birds / 1 | SPARROW / Birds / 1 |

부호화 serial position은6이고 native 시각 차는44.64625초다. 이 쌍은 효과가 커서
선정한 것이 아니라 첫 대응 항목이라는 기계적 규칙으로 선정했다. 두 사건 각각
`[-3,+2)`초의 신호 접근은 sample 계약을 조건으로 한 입력 검증이며, 단일 쌍의
그림이나 유사도를 기억 복원 성능으로 해석하지 않는다.
[후속 실제 읽기와 독립 대조](hippocampal_cml_native_pair_findings.md)는 이 두 구간의
120채널 값을 확보하고 선택한 차신호80,000개를 원 바이트에서 bit-exact 재구성했다.

## EDF 판독 구현과 확인

[bounded EDF+C 판독기](../verify/Q-NPF-04/hippocampal_reinstatement/cml_edf_records.py)는
고정 헤더, 같은 표본률의 선택 채널, 원 byte TAL, 채널별 물리 단위와 보정을 읽는다.
각 record의 TAL이 `record index × duration`과 맞지 않으면 중단한다. EOF·잘린
record·EDF+D·보유하지 않은 표본·중복 채널과 모호한 비정수 인덱스도 거부한다.
행동 시계나 사건 label을 스스로 변환하지 않고 gap을 채우거나 필터링하지 않는다.
[EDF+ 규격](https://www.edfplus.info/specs/edfplus.html)에 따라 annotation은 모든 원
문자 byte를 사용하며 전압 보정 또는 int16의 low byte 추출을 적용하지 않는다.

[관련 검사](../tests/test_cml_edf_records.py)는 실제 보유 record250의 시각,120채널
단위·극값, 잘못된 record 번호, truncated payload와 반열린 표본 구간을 확인했다.
독립 실행 결과는4 passed이고 [검사 영수증](../data/local/hippocampal-reinstatement/cml-content-support-v1/cml_edf_records_test_receipt.json)에
source/test SHA를 남겼다. 이 검사는 신호 포맷과 읽기 경계를 확인하며 실제 발화의
생리적 정렬이나 리플 검출 정확도를 확인하지 않는다.

내용 결과 SHA는 `7006d6a6121180c21f5f5700014147f7ce76536d6fc4b373f95d8217c88c8b49`,
sample-origin 결과 SHA는 `a68e373968f344895666644787781a22066769a1762167c93db0595bfe12c7d3`다.
첫 metadata 분석의 header 필드 오해 오류도 소스·실패 상태로 별도 보존했다.
