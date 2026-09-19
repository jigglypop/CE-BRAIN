# Norman2019: 숨은 표의 지원과 판독 실패의 관측 조건

2026-09-20. 남아 있던 RTA0/1/2의 opaque table을 판독하고, 기존 부호화→회상
판독 실패의 고정 입력 조건을 진단했다. 새 다운로드·모형 적합·시간창 선택은 하지 않았다.
전기 이력과 기억 복원을 잇는 데 필요한 사건별 관측이 실제로 있는지를 확인한 단계다.

## RTA 표를 판독한 결과

기존 MAT의 SHA는 `7c776aafe3a44310e25946a36d7528cef15b7540b956bad69bec2c0e6e89ec70`다.
RTA0/1/2의 object ID1/2/3과 단일 FileWrapper 안의 세 table block을 확인했다.
각 표의 열 이름·행 수·배열 형식과 원 F/I/Iall 이름 집합의 대응도 검사했다.

| 표 | 행 수 | 고유 channel-item 쌍 | 열의 실제 내용 |
|---|---:|---:|---|
| RTA0 | 23,744 | 23,744 | 채널212개×제시 라벨112개의 완전 조합 |
| RTA1 | 25,542 | 5,609 | 채널·항목 문자열과 그 반복 |
| RTA2 | 20,426 | 3,176 | 채널·항목 문자열과 그 반복 |

세 표 모두 `channel`, `item` 두 열뿐이며, 각각 [행 수,1]의 scalar-string cell이다.
시간·run·ripple index·숫자형 피질 feature 열은 없다. 채널 이름의 접미사에서16개
기록 묶음을 파생할 수 있지만 별도 record 열이 있는 것은 아니다. SUB13/SUB13b의
동일인 관계를 적용하면15명이다. RTA1/2의 생물학적 조건 이름은 table metadata에
명시되지 않아, 반복행을 특정 시각의 원 ripple로 임의 해석하지 않는다.

[전체 판독 결과](../data/local/hippocampal-reinstatement/norman-mvpa-rta-tables-v1/rta_tables_decoded.json)와
[전체 문자열 배열](../data/local/hippocampal-reinstatement/norman-mvpa-rta-tables-v1/rta_tables_decoded.npz)을
보존했다. JSON SHA는 `de8da9c7c3ea7e54b277620ef548ad3077e2ae742266f85da08bb6e722adfa58`,
NPZ SHA는 `d6ab4aead576772c7680600326e4fa71f99f87f0180fbf0324bb80ab873c54ac`다.
구조 탐색·slot 검사·판독 세 단계가 모두 성공했으며 이전의 미확인 판정은 이 검사로 갱신한다.

## M2의 결측 지원과 정확한 대응

[별도 지원 비교](../data/local/hippocampal-reinstatement/norman-rta-support-v1/support_check.json)는
판독 NPZ와 원 MAT를 해시로 고정하고 F/I/M2만 읽었다. RTA2의 고유3,176쌍은
M2에서 유한한 channel-item3,176쌍과 정확히 같다. 양방향 차집합은0이며, 각 지원
쌍에는 모든106시점이 있어 총336,656값이 유한하다.

RTA2의238개 record-item 그룹은 각 기록의 모든 채널을 포함하며, 같은 그룹 안의
라벨 반복 수는 채널마다 같다. 대표 반복 수×기록별 채널 수로20,426행을 정확히
재구성한다. RTA1도424개 그룹에서 같은 성질을 가지며25,542행이 재구성된다.
이238개는 I 이름 기준 지원이고, 원 제시 이름까지 일치하는204관측과 구별한다.
B 접미사56후보의 대응 문제를 이 비교가 해결하지는 않는다.

따라서 M2의 유한/결측 여부와 반복 라벨의 지원은 연결했다. 어떤 원 ripple를 골랐는지,
각 사건의 수치값, 그 평균·정규화 규칙은 아직 알 수 없다. 반복행에 임의의 시간순서를
부여하거나 원 ripple 시각 목록과 행 번호만 맞춰 사건을 복원하지 않는다.

## 기존 판독 실패에 대한 고정 진단

[스케일 진단](../data/local/hippocampal-reinstatement/norman-transfer-scale-audit-v1/norman_transfer_scale_audit.json)은
기존204관측과 고정 부호화105..495ms·회상55..245ms를 유지했다. 원 MAT,
항목 지원, 고정 source·결과·manifest의5개 해시를 검사했으며 새 보정은 하지 않았다.

- M0는 M0singletrial의 해당4반복 평균과 부동소수점 오차 수준에서 같다.
  최대 절대차4.44×10⁻¹⁶, 상대 Frobenius 오차9.11×10⁻¹⁷이다.
  부호화 평균이 다른 자료였다는 설명은 이 검사에서 지지되지 않는다.
- 같은 채널 좌표에서 항목별 평균을 제거한 RMS의 회상/부호화 비율은 기록 묶음별
  0.5947..2.4241, 중앙값1.1393이었다. 채널별 항목 평균 이동의 RMS를 부호화의
  중심화 RMS로 나눈 값은0.1100..0.4662, 중앙값0.2947이다. 관측된 스케일·이동의
  차이이며 정규화, 사건 집계, 생리 또는 실패의 원인을 식별한 결과가 아니다.
- α=0인16개 task·53관측은 부호화 반복 보류 log-loss부터 균등 후보를 선호했다.
  모든16개에서 가장 좋은 양의 α도 균등 log-loss보다 나빴다. 그 차이는
  최소0.00003416, 중앙값0.012757, 최대0.065645 nats다. 이 부분은 회상 전이에
  들어가기 전에 이미 나타난 결과이며, 나머지 task의 전이 실패와 구분한다.

기존 주 평가−0.123684 nats는 그대로 유지한다. 이번 결과를 이용해 새 스케일 보정이나
우수 하위집합을 고른 뒤 같은 회상 자료에서 성공을 주장하지 않았다. 진단 결과 SHA는
`e06293286c8fa4c8dffe0c8dbb4f3a1700f01a80ff0ca8a6c216a49b79380586`다.

## 전체 식을 검증하기 위한 다음 입력

[관측식의 평균 반례](hippocampal_retrieval_observation_findings.md)처럼, 사건 평균만
남기면 이력 효과가 평균 분포에서 완전히 사라질 수 있다. 이 조건부 Gaussian 반례는
독립 수학 검토를 거쳤으며 실제 M2의 Fisher를 계산한 것은 아니다. 시각만 따로
확보해도 버려진 사건별 피질 값과의 대응은 되살아나지 않는다.

남은 입력은 **같은 기록에서의 사건별 피질 수치, 내용 라벨, 해마·행동과의 공통 시계,
생성·정규화 규칙**이다. 기존 MAT의 opaque 표가 이를 제공하는지 묻던 단계는 끝났다.
다음 후보 선택에서는 이 네 요소의 지원을 확인한다. 당시 관련 코드까지만 확인했던
별도 큰 피질 RTA는 [후속 수집·전체 구조 검사](hippocampal_norman_cortical_rta_findings.md)를
완료했다. 조건 집계와 A/B 숫자 벡터는 있지만 원 사건 시각과 표본을 잇는 key는 없었다.
[공통 사건표](hippocampal_norman_event_observations_findings.md)의3,577개 ripple와470개
행동 주석을 이 배열에 행 순서만으로 결합하지 않는다. [CML 대체 입력](hippocampal_cml_input_findings.md)은
실제 EDF 표본에 접근했지만 행동 onset과 native sample의 정렬 출처를 먼저 확인해야 한다.

확보된 ripple는 [후향 검출](hippocampal_norman_ripple_clock_findings.md)이라는 조건도
유지한다. 원 사건의 연결이 확보돼야 전기 이력의 추가 정보, 개별 기억 내용의 복원,
학습에 따른 관계·리만 계량 변화와 현재 표현 선택을 순서대로 대조할 수 있다.
이 전체 연결과 검색의 인과 방향은 아직 미확립이다.
