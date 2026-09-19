# 사람 해마 ripple과 회상 내용: Norman2019 입력 확인

2026-09-20. [Rey 공동 시행 지원](hippocampal_population_support_findings.md)의 다음 단계다.
기존 원장에서 Norman/3259369의 등록 파일은 없고 후보·미다운로드 기록만 있음을
확인한 뒤 공식 공개 자료의 작은 파일을 먼저 확보했다. 새 복원 효과를 적합한 결과는 아니다.

## 출처와 받은 범위

출처는 [Zenodo 3259369](https://zenodo.org/records/3259369), 판본
`FreeRecallSWRv1.0.0`이며 [Norman et al. 2019](https://www.science.org/doi/10.1126/science.aax1030)의
자료다. Record 게시일은2019-08-01, 표시 수정일은2020-01-24다. 공식 record의 license
값은 공란이어서 자료 전체의 라이선스를 임의로 부여하지 않는다. 새 외부 배포는 하지 않았다.

전체 ZIP은3,458,065,961바이트이며 record의 MD5는
`6da005f0262e9c10b4de224a2cb6657b`다. 전체 ZIP을 받거나 이 MD5를 재계산하지 않았다.
서버의 Last-Modified는 `Thu, 13 Aug 2026 03:59:51 GMT`였으며 record의 표시 수정일과
구분한다. ETag는 제공되지 않았다.

ZIP 끝부분65,536바이트와 중앙목록76,886바이트에서637개 항목을 확인했다.
필요한 저자 코드와 작은 MAT 등71개 항목만 선택해 범위 요청으로 받고, 해제 길이·
CRC32·로컬 SHA-256을 모두 확인했다. 수신 전에206, 정확한 Content-Range/Length와
전체 길이를 대조했다. 항목 무결성을 전체 원격 ZIP의 해시 검증으로 대체하지 않는다.

- Metadata 단계의 실제 네트워크 본문:576,700바이트(8MiB 상한 이내).
- 그중 항목 수신 본문:432,002바이트; 해제된71항목:1,945,394바이트.
- 직접 제공되는 README는2,276바이트, ZIP 내부 README는2,243바이트로 별도 보존했다.
- 초기 API/직접 파일 요청 두 번은403으로 본문을 받기 전에 종료했고 각각0바이트다.
  이 실패와 browser User-Agent를 명시한 후속 성공을 별도 기록했다.

[보유 위치](../data/external/hippocampal_reinstatement/norman2019_metadata_v1)에는 원항목,
목록, 범위 영수증과 수집 소스를 둔다. 영수증에서 Cookie/Authorization 계열 헤더
값을 가린 판본을 보존했고 원본 Temp 로그는 덮어쓰지 않았다.

## 실제 자료가 제공하는 관측

개별 사진을 다시 제시하지 않는 자유회상이지만 얼굴/장소 범주 지시는 있다. 따라서
‘개별 항목 단서 없는 범주 지시 회상’으로 기술한다. 외부 부분 단서에서 사건의 누락
요소를 채우는 과제와 동일하지 않으며, 사용자 목표의 검색·현재 표현 선택에 연결할
별도 관측이다.

| 자료 | 확인한 지원 | 남은 구분 |
|---|---|---|
| `stimuli_list_run_{1,2}.mat` | Face/Place exemplar 라벨, 제시 순서와 반복 | run·회상 annotation과 정확한 대응 |
| `*_RecallEvents.mat` | 범주/run별 발화 주석, 대응 라벨, onset/offset 초 | Prompt·반복·범주 밖 항목을 따로 처리 |
| `Recall_and_memory_search_periods.mat` | EF/EP와 recall/search mask,500Hz·0–150초 run 상대 시계 | 실제 annotation 시각과 mask의 대응 |
| `ripple_psth_data.mat` | viewing1,792행·recall391행의 처리 raster와 subject/run/내용 metadata | 중복 기록과 독립 행동 시행을 구별 |
| MVPA 저자 코드와 MAT | 부호화 HFB와 ripple 주변 항목 표현,212개 채널의 기록 묶음 대응 | 개별 사건 시계와 항목 집계 규칙은 추가 확인 필요 |

[고정 입력 진단](../verify/Q-NPF-04/hippocampal_reinstatement/norman_behavior_support.py)은
등록된 항목 manifest와 실제51개 입력의 SHA·크기를 먼저 확인했다.16개 기록 묶음은
15명에 대응하며 SUB13/SUB13b를 두 독립 참가자로 세지 않는다.32개 run은 각각
14항목×4반복=56번의 제시를 가지며 합계1,792행이다. Viewing PSTH의
`(recordset,run,label,repnum)`은 원 제시 목록의 순서까지 정확히 일치했다.

행동 주석470행은 Prompt79행과 그 외391행이다. Recall PSTH391행은 Prompt를
제외한 전체 `(recordset,run,label)` **다중집합**과 정확히 일치했다. 같은 라벨이
반복된 PSTH 행 각각에 절대 발화 시각을 배정한 검증은 아니며, 별도 `recalled_items`
508개를391행의 사건 index로 사용하지 않는다.

- 391행 중383행은 현재 run의 제시 목록과 exact label이 맞고8행은 맞지 않는다.
  이것은 저자가 붙인 오류 표지가 아니다.8행 중6행은 같은 참가자 기록 묶음의 다른
  run에 등장하며, 나머지2행도 구분해 보존한다. 자동으로 오회상이라고 판정하지 않는다.
- `(recordset,run,label)`의255개 고유 키를 넘는 중복 초과량은136이다. 범주별
  원 block까지 키에 넣으면 초과량111이다. 이는 시간순 반복 표지가 아니며
  faces→places 파싱 순서를 실제 회상 순서로 사용하지 않는다.
- Prompt 외35행은 label의 Face/Place 접두어가 원 회상 block과 다르다.
  Prompt 자체의 접두어/block 불일치3행은 별도다. 이 표지들은 서로 배타적인
  집단이 아니므로 합산해 전체 시행 수를 만들지 않는다. `B` 접미사도 그대로 보존한다.

회상/search mask64개는 각각75,001표본이며500Hz·0–150초 축이다. 실제 주석에서
Prompt를 제외한 **[발화 시작−3초, 발화 종료]**를 합집합하고,500Hz로 반올림·양끝
포함·0–150초 절단한 값이 원 mask와 전부 일치했다(XOR0). Search는 이 mask의
정확한 여집합이다.391개 시작 시각은 모두 mask에 들어가지만7개 종료 시각은
150초를 넘어서 뒤가 잘린다. 이 경계 밖의 신경 관측을 확보했다고 가정하지 않는다.

따라서 이 mask는 미래 발화를 사용한 **후향적 구분**이다. 다음 회상 내용을 예측하는
현재 상태/이력 입력에 넣으면 미래 정보가 섞인다. 또한 이 구분을 ‘뇌가 실제로 회상한
시간’의 직접 관측으로 해석하지 않는다. 전향 예측에는 원 사건 시각과 별도로 검증한
관측 범위를 사용해야 한다.

공식 README는 음성 원본을 제공하지 않는다고 명시한다. 발화 시각/주석의 재분석은
가능하더라도 원음의 envelope나 발화 준비를 새로 측정할 수 있다고 가정하지 않는다.
PSTH의 처리 raster도 연속 원 LFP와 같지 않다.

## 다음 큰 파일을 고른 근거와 현재 상태

선택한 단일 항목은 `multivariate_pattern_analysis_and_recall_decoder/data/`
`multivariate_pattern_all_visual_channels.mat`다. 압축402,445,264바이트,
해제402,438,764바이트, CRC32 `4c66047e`이며 deflate된 하나의 ZIP 항목이다.
항목 안 특정 MATLAB 변수만 원격 범위로 건너뛰어 읽을 수 있다고 가정하지 않는다.

저자 코드는 이 파일에서 `M0`, `M0singletrial`, `M2`, `I`, `Iall`, SWR table,
`electrode_param`, `DATAbyChannel`을 읽는다. M0/M0singletrial은 부호화 HFB이고
M2는 time×channel×item의 ripple 주변 표현이다. 실제 채널→환자 대응, M2의
평균/개별 사건 단위, DATAbyChannel의 사건 시각을 확인하는 데 필요한 한 파일이다.
원 해마 신호150MB나 RTA2.3GB 파일은 이번에 요청하지 않았다.

별도450MiB 본문 상한과16MiB 범위 조각으로 수신을 완료했다. 같은 실행 handle
`64566`을 끝까지 관찰했고 exit0을 확인했다. 네트워크 본문은402,445,776바이트로
압축 항목402,445,264바이트와 local header512바이트의 합이다. 전체24개 조각의
범위·길이와 SHA를 보존했다. 해제 길이402,438,764바이트와 CRC32 `4c66047e`가
일치하며 MAT SHA는 `7c776aafe3a44310e25946a36d7528cef15b7540b956bad69bec2c0e6e89ec70`다.

[정본 보유 위치](../data/external/hippocampal_reinstatement/norman2019_mvpa_v1)에
MAT·상태·영수증·수집/보존 소스·manifest7파일402,471,286바이트를
`norman2019-mvpa-v1`로 등록했다. 보존 전후 크기·SHA·CRC를 재확인했다.
압축24조각402,445,264바이트는 원 수신 경로에 유지하고 `norman2019-mvpa-chunks-v1`에
따로 등록했다. 과거 `norman2019-mvpa-pending-v1`의 `location_only` 기록은 유지하며
별도 완료 기록을 추가했다. 전체 ZIP의 MD5를 검증했다는 뜻은 아니다.
해당 수신25건은 모두206이며 실패0건이다. 이 수신의 응답에는 ETag뿐 아니라
Last-Modified도 없었다. 앞선 metadata 수신에서 얻은 Last-Modified와 이번 응답이
일치했다고 주장하지 않는다. 범위·길이·CRC와 로컬 SHA 검증의 범위를 유지한다.

## 완료한 MAT 구조 검사와 남은 사건 단위

[제한된 구조 결과](../data/local/hippocampal-reinstatement/norman-mvpa-schema-v1/mvpa_schema_whos.json)는
MATLAB v5 형식이며 다음 축을 확인했다. HDF5/v7.3으로 읽는 첫 시도는 실패했고
별도 상태 파일로 보존했다.

| 변수 | 배열 크기 | 확인 범위 |
|---|---|---|
| M0 | 236×212×28 | 시간×채널×항목 |
| M0singletrial | 236×212×112 | 부호화 제시112칸, Iall에서 항목당4회 |
| M2 | 106×212×28 | 별도 개별 ripple/event 축이 없는 항목 표현 |
| I | 28 | Face14·Place14 exemplar 라벨 |
| included_subjects/channels/regions | 각각212 | 채널별 기록 라벨·채널명·영역의 병렬 대응 |

16개 기록 라벨은 SUB13/SUB13b를 합쳐15명이다.212채널을 한 사람의 동시 신경망으로
취급하지 않는다. M2에는 개별 사건 축이 없지만, 어떤 ripple들을 어떤 평균/집계
규칙으로28칸에 넣었는지는 아직 확인하지 않았다. 크기만으로 평균 규칙을 단정하지 않는다.

[작은 metadata 결과](../data/local/hippocampal-reinstatement/norman-mvpa-schema-v1/mvpa_metadata_bounded.json)에서
M2 코드에 쓰이는 bin_centers는−525..525, 간격10이며106칸이다. 부호화 bin_centers_stim은
−225..2125, 간격10이며236칸이다. 코드의 상대시간 축을 개별 사건의 절대 시계로
대체하지 않는다. 이 출력은 첫 strict JSON의 nonfinite 직렬화 실패를 보존한 뒤,
성공 판본에서 nonfinite를 문자열로 기록했다. 분석 입력 배열 자체를 변경하지 않았다.

[DATAbyChannel prefix 검사](../data/local/hippocampal-reinstatement/norman-mvpa-schema-v1/mvpa_databychannel_prefix.json)는
첫 압축 MATLAB element의 해제 prefix262,144바이트만 읽었다. rest/stim/recallFace/
recallPlace/searchFace/searchPlace와 preferred/nonpreferred 계열 등 상위 조건 필드를
확인했다. 그 상위 필드에는 subject/run/event/time 키가 없지만 **중첩 구조를 검사하지
않았으므로 내부의 개별 사건·시간 지원 부재를 확정하지 않는다**.

후속 [전체 구조·항목 대응 검사](hippocampal_norman_event_support_findings.md)에서
DATAbyChannel의21개 필드는 모두 숫자형 조건별 시간·채널 배열이고 F는 채널 이름임을
확인했다. 이 안에는 개별 사건 시계가 없다. [후속 RTA 판독](hippocampal_norman_observation_boundary_findings.md)에서
별도 RTA0/1/2도 channel/item 문자열만 담고 있고 시각·사건별 피질 값은 없음을
확인했다. 원 사진 이름이 정확히 맞고 M2가 유한한 것은204개
기록 묶음×항목이며,56개 B 접미사 후보의 대응은 해결되지 않았다. 항목별 표현의
식별성을 다음 기억 선택이나 이력의 인과 효과로 해석하지 않는다.

저자 코드의 recall 결측값 대치는 target 자료의 평균을 사용한다. 이를 새 보류 평가나
온라인 판독에 그대로 사용하지 않는다. 환자가 다른 채널을 한 동시 집단으로 묶는지,
평균 표현을 독립 개별 사건처럼 세는지도 원파일에서 확인해야 한다.

## 관측식과 다음 판정

[선택과 재활성화의 관측식](hippocampal_retrieval_observation_findings.md)은 다음 두
질문을 분리한다. 다음에 보고될 내용은 미래 정답을 입력에 넣지 않은 발생률 모형으로,
결국 보고된 내용의 신경 재활성화는 그 내용을 조건으로 하는 후향적 특징 모형으로
검사한다. 무발화/관측 구간이 없으면 전자의 전체 경로 우도를 구성하지 않는다.

이번 조건부 수식은 발생 시각과 선택 내용의 정보율을 분해하며, 실제 전기효능이나
뇌 전체 리만 계량을 확립하지 않는다. 신경 원파일의 지원을 확인한 뒤 같은 범주 안
사진 구별, 범주별 기저 활성, 시각과 관측 결손을 반영한 비교 범위를 정한다.

## 보존

Metadata82파일2,351,872바이트를 `norman2019-metadata-v1`에 등록했다.
초기 HTTP 실패6파일10,393바이트는 `norman2019-http-attempts-v1`, 범용 schema
출력과 직렬화 실패 시도22파일2,347,601바이트는 `norman2019-schema-attempts-v1`에
구분했다. 큰 재귀 JSON 출력은 다음 분석의 정본 입력으로 사용하지 않는다.
원항목71개는 보존 전후 SHA·크기와 ZIP CRC를 다시 대조했다.
[데이터 원장](data_registry.md)에 각 파일의 실제 경로·용량·해시와 수신 이유를 남겼다.

집중 진단의 초기/중간6파일596,539바이트는 `norman-behavior-support-attempts-v1`,
영구 입력 경로와 명확한 표지 뜻을 적용한 소스·결과·manifest3파일331,394바이트는
`norman-behavior-support-v3`에 등록했다. 초기/중간의 `intrusion`/`repeat_recall`
이름은 원자료의 오류/시간순 표지로 해석하지 않는다. 정본은 각각
`current_run_unmatched`/`duplicate_in_parser_order`로 뜻을 명시한다.

[정본 결과](../data/local/hippocampal-reinstatement/norman-behavior-support-v3/norman_behavior_ripple_join.json)
SHA는 `a02e3b122d5cc6380a7bedc45e0e1958d204781dd7bcd0b88f65e0ca6e11188a`다.
보존 실행기로 정본 소스를 한 번 실행했고 기존 분모·viewing 순서·recall 다중집합·
mask XOR0가 유지됨을 독립 대조했다. 재적합이나 신경 효과의 검정은 하지 않았다.

MVPA 구조 검사 성공 출력·두 실패 상태·각 소스와 보존 manifest12파일892,831바이트는
`norman-mvpa-schema-v1`에 등록했다. 원 Temp 결과는 유지했다. Whos 결과 SHA는
`da0a708fe5226104e2eceb7c0d453208c3c349277b41ba1085a16e671ee4b35c`,
metadata 결과는 `f7f46d89aebcfb2eb481d34251fd2f6db2b9b407b0f4111ff6408a5c43fe39ed`다.
