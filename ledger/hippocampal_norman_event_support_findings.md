# Norman2019: 사건 시계와 항목 표현의 실제 지원

2026-09-20. [입력 확보](hippocampal_norman_inputs_findings.md)에서 미확인이던 중첩
배열과 사진 이름 대응을 확인했다. 전체 목표의 전기 이력→검색·복원 검증을 위해,
현재 파일에서 사건을 연결할 수 있는 범위와 처리된 항목 표현을 구분한다.

## DATAbyChannel 전체 구조

MAT SHA `7c776aafe3a44310e25946a36d7528cef15b7540b956bad69bec2c0e6e89ec70`을
고정한 [streaming 검사](../data/local/hippocampal-reinstatement/norman-event-structure-v1/databychannel_stream_structure.json)는
첫 압축 MATLAB element345,413,871바이트를 전부 순차 읽었다. 해제360,600,328바이트,
zlib EOF와 미파싱 payload0을 확인했다. 앞선 짧은 ASCII prefix 조사와 다른 완료 범위다.

| 배열 | 실제 형식·크기 | 축 |
|---|---|---|
| rest/stim/recall/search/preferred 계열17개 | double49×253×212 | 주파수×상대시간×채널 |
| viewing_preferred/nonpreferred 및 CAT 계열4개 | double212×467 | 채널×상대시간 |

21개 필드 모두 숫자 배열로, 내부에 cell·struct 또는 별도 event/item/run 축이 없다.
이 struct에서는 개별 ripple이나 행동 사건의 절대 시계를 연결할 수 없다. 상대시간은
`t_out`253개(−756..756, 저자 plot의 ms), `t_out_stim`467개(−0.648..2.148초),
주파수는 `f_out`49개(31.25..218.75Hz)와 크기가 대응한다. 정확한 집계 규칙은 별도다.

[F cell 확인](../data/local/hippocampal-reinstatement/norman-event-structure-v1/F_cells_structure.json)에서
212개 cell은 모두 `channel-record_label` 문자열이었다. included_channels/subjects와
212행 전부 정확히 대응하며 사건 시각 표가 아니다.16기록 묶음·15명 구분을 유지한다.

## 초기 MATLAB table 경계와 후속 판독

[추가 검사](../data/local/hippocampal-reinstatement/norman-event-structure-v1/workspace-followup-v1/workspace_rta_structure.json)에서
ItemResponse/ItemResponseNU는 각각 double212×28이고, RTA0/1/2는 `MCOS table`의
opaque 참조다. `__function_workspace__`는9,806,224바이트이며 내부 table의 typed
열을 SciPy로 재구성하지 못했다. 제한된 문자열 검색에서 시계 열 이름이 없었다는
사실만으로 table 내부에도 시계가 없다고 결론내리지 않는다.

저자 주석이 설명한 allR/allS/allF/allP는 실제 MAT의 root22변수에는 없다. 주석과
실파일을 구별한다. DATAbyChannel/F에서 사건축이 없다는 결론은 확정했고, 이 검사
당시 opaque table 내부는 미확인으로 남겼다. 이후 [제한 MCOS 판독](hippocampal_norman_observation_boundary_findings.md)이
RTA0/1/2를 읽었으며 모두 channel/item 문자열뿐임을 확인했다. RTA2 고유3,176쌍은
M2 유한 지원과 정확히 같지만, 표에 시각이나 사건별 피질 수치가 없어 사건 번호와
활성값을 임의로 복원하지 않는다.

## 항목 이름과 관측 분모

[항목 지원 진단](../data/local/hippocampal-reinstatement/norman-item-support-v1/norman_mvpa_item_support.json)은
위 MAT, 기존 행동 v3 결과, 원 제시 목록32개를 SHA·용량으로 고정했다.
M0/M0singletrial은 모두 유한하며 I의28항목에 Iall의각4반복이 정확히 대응한다.

모든 기록 묶음의 run은 Face7+Place7이며 두 run의 제시 집합은 겹치지 않는다.
그러나 I와 두 run의 원 사진 이름 집합이 모두 일치하는 것은13/16기록 묶음이다.
SUB11/SUB15의 run1에는14개 B 접미사 이름이 있고 SUB13b는 두 run28개 모두
B 이름이어서 I의 무접미 라벨과 다르다. B를 같은 사진으로 정규화하지 않는다.

| 원 제시 후보 상태 | 기록 묶음×항목 수 |
|---|---:|
| 전체 후보 | 448 |
| 원 이름이 정확히 대응 | 392 |
| B 접미사로 대응 미해결 | 56 |
| 정확 대응 중 M2 전체 유한 | 204 |
| 정확 대응 중 M2 전체 NaN | 188 |

M2의 유한 여부는 기록 묶음×항목 단위로106개 시점·모든 채널이 함께 결정됐다.
일부 시점이나 일부 채널만 유한한 경우는0이었다. 원 I만 기준으로 한 지원 항목238개와
원 제시 이름까지 일치하는204개를 혼용하지 않는다. 미관측은 분류 실패0이 아니며,
M2를 가진 항목만으로 각 후보7개를 줄이지 않는다.

13개 이름 완전 일치 기록 묶음에서는 M2 지원 이름이 실제 non-Prompt 회상 이름의
부분집합이다.5개는 일치하고8개에서는 회상한1–6개 이름의 M2가 빠졌다. 이 누락이
생긴 처리 규칙은 미확인이다.699개 같은 범주 관측 가능 pair도 독립 시행 수가 아니다.

## 후속 검증 범위

M2에는 실제 회상 run·사건·절대시각 축이 없어 반복 회상391건을 행에 배정하지 않는다.
현재 가능한 항목 식별 질문의 후보 run은 **부호화 때 해당 사진을 제시한 run**이다.
이를 회상 당시의 run이라고 부르거나 다음에 선택될 기억을 예측한 결과로 해석하지 않는다.
[선택과 재활성화의 관측식](hippocampal_retrieval_observation_findings.md)의 사건 이력
질문에는 별도 원 ripple 시각과 실제 관측 구간이 필요하다.

상기 구조·opaque 확인의 성공과 첫 실패를 포함한10파일91,006바이트는
`norman-event-structure-v1`, 항목 지원 소스·결과·manifest3파일277,751바이트는
`norman-item-support-v1`로 [데이터 원장](data_registry.md)에 보존했다.
항목 지원 결과 SHA는 `933fc9001ea8bdeb28d3e3ff10b7a99d80af4de542006d31c72efb3adb9d1eeb`다.
