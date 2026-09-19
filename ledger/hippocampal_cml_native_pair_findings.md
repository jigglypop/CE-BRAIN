# CML: 같은 단어의 부호화·회상에서 실제 전기 표본 읽기

2026-09-20. [내용 지원 조사](hippocampal_cml_content_support_findings.md)에서 신호를
보기 전에 고른 첫 SPARROW 쌍의 실제 EDF 두 구간을 받았다. Native sample 계약을
가정한 부호화·회상 입력 확인이며, 행동 시계의 독립 동기화나 기억 복원 효과를
검증한 실험은 아니다.

## 실제 보유한 신호

OpenNeuro ds004809:2.2.0, sub-R1004D/ses-0의 동일 versionId와 ETag를 사용했다.
기존 header와 record250은 재수신하지 않았다. 원문 전체2.07GB 중 두 범위만 받았고
두 응답 모두206·정확한 Content-Range/Length·ETag를 확인했다.

| 구분 | 부호화 WORD | 회상 REC_WORD |
|---|---:|---:|
| 원 사건 행0-based | 31 | 44 |
| 기준 native sample | 1,783,142 | 1,854,576 |
| 확보 EDF record | 1111..1116 | 1156..1161 |
| 수신 바이트 범위, 양끝 포함 | 426,781,886..429,086,569 | 444,067,016..446,371,699 |
| 수신 바이트 | 2,304,684 | 2,304,684 |
| 추출 표본, 우측 제외 | `[1778342,1786342)` | `[1849776,1857776)` |
| 추출 신경 신호 | 120채널×8,000표본 | 120채널×8,000표본 |

합계 수신4,609,368B로8MiB 상한 이내였다. Collector는7.6초 내 exit0으로 종료했으며
실행 중인 다운로드 handle은 없다. [실행 영수증](../data/external/hippocampal_reinstatement/cml_catfr1_native_pair_v1/execution_receipt.json)은
preserved wrapper·실제 Python 경로·PYTHONPATH와 사전 확인한 Python3.11.15,
NumPy2.4.6, Matplotlib3.10.6을 기록한다. 버전값은 collector stdout이 아닌 같은
환경의 실행 직전 조회다. 원 결과와 manifest는 덮어쓰지 않았다.

12개 record의 TAL이 각 기록 번호와 정확히 일치했다. 각 구간의 모든120채널은
1600Hz·uV이며 정확히5초다. 유한값 실패0, 수신 record의 digital rail0, 추출 구간의
physical rail0이었다. 이는 이 두 구간의 숫자 품질이며 artifact 부재·전체 세션 품질·
고주파 리플의 검출 가능성을 입증하지 않는다. 필터·정규화·모형 적합은 수행하지 않았다.

## 원 바이트에서의 독립 재구성

[독립 검사](../data/local/hippocampal-reinstatement/cml-native-pair-independent-check-v1/independent_check.json)는
영구 판독기를 import하지 않고 고정폭 EDF header와 원 int16 표본을 직접 읽었다.
Collector의7파일과 선언 입력7개의 크기·SHA를 확인하고 원 events.tsv의31/44행이
SPARROW·Birds·list1·serial position6 및 선언 sample과 같은지 대조했다.

같은 shaft의 LOTD2–3,3–4,4–5,5–6과 LFG1–2 차신호 총80,000개를 별도로
재구성해 [보존 NPZ](../data/external/hippocampal_reinstatement/cml_catfr1_native_pair_v1/native_pair_signals.npz)와
bit-exact 일치했다. 최대 절대차0이며 두6-record 내부의 추출 경계는 각각
`[742,8742)`, `[176,8176)`이다. 시간벡터는−3..1.999375초, 간격1/1600초이고
오른쪽2초를 포함하지 않는다. 12개 TAL도 Decimal 기준으로 정확히 대조했다.

[파형 그림](../data/external/hippocampal_reinstatement/cml_catfr1_native_pair_v1/native_pair_signals.png)은
5행×2열로 두 구간을 같은 채널별 y범위에서 표시한다. Root가 직접 열어 채널명·단위·
시각축·조건부 시계 설명과 잘림 여부를 확인했다. 차신호는 local reference를 위한
선형 차이며, LOTD2–3과5–6은 atlas상 CA1/DG 경계를 걸치므로 단일 subfield 신호로
명명하지 않는다. 이들은 저장 bipolar EDF를 받은 결과가 아니라 같은 monopolar
원표본의 차로 계산한 값이다.

| 기록 | 판본 | 파일 수 | 바이트 |
|---|---|---:|---:|
| 두 원구간·수집/판독·그림·실행 보충 | `cml-native-pair-readback-v1` | 9 | 5,484,854 |
| 별도 코드·전량 비교·manifest | `cml-native-pair-independent-check-v1` | 4 | 19,201 |

Readback 결과 SHA는 `14023c5b41530fa41e3237aa56dc0ae81e74cab21166af07ed8b4921a97d8f1c`,
독립 결과 SHA는 `8ea250425c209ff2ac316f57f8c078ac7774ba0bf4a854b72225936f194903bc`다.

## 후속 판별과 남은 조건

[같은 범주 안의 후속 판독](hippocampal_cml_withincategory_findings.md)은 후보 신호를
추가 확보하고 고정 관측식을 한 번 실행했다.12항목·9목록에서 신경 특징의 추가
log-gain은−0.017627 nats로 제시 순서 기준을 개선하지 못했다. 아래의 단일 쌍 입력
확인과 구분하며, 해마 이력의 추가 효과는 아직 검사하지 않았다.

이제 같은 단어의 부호화와 회상 표본을 동일 채널 좌표에서 읽을 수 있다. 그러나
단일 쌍의 파형 유사성은 내용 판독이나 해마 검색의 증거가 아니다. 이후 분석은 같은
목록·범주의 다른 세 단어를 대조하고, 반복 회상·침입·단어 없는 발화를 구분해야 한다.
또한 피질 특징을 부호화에서 고정한 뒤 회상에 옮겨야 하며 회상 결과를 보고 시간창·
전극·보정식을 고르면 독립 평가가 되지 않는다.

해마 과거 활동의 추가 예측력을 평가하려면 이력과 반응 시점을 보존하고 직전 피질
상태·발화 준비·공통 입력에 대한 대조를 정해야 한다. 다음 내용의 온라인 선택을
예측하는 질문에는 미래에 회상될 단어로 조건을 거는 이번 후향적 쌍 선택을 그대로
사용할 수 없다. [검색 관측식의 두 질문](hippocampal_retrieval_observation_findings.md)을
유지한다. 독립 동기화·사람 간 일반화·관계 변화·물리 변화 비용의 계량과 현재 세계
표현 선택까지의 전체 기전은 여전히 미확립이다.
