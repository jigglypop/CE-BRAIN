# Norman2019 공통 사건표: 시각과 원행 대응

2026-09-20. [ripple 시계 검사](hippocampal_norman_ripple_clock_findings.md)에서 확인한
원 사건값과 기존 행동 주석을 분석 가능한 공통 block 구조로 보존했다. 개별 ripple에
기억 항목이나 피질 반응을 배정한 결과는 아니다.

[고정 소스](../verify/Q-NPF-04/hippocampal_reinstatement/norman_event_observations.py)는
원 수집 요약과 행동 v3 결과를 SHA로 고정하고, ripple MAT64개의 개별 크기·SHA를
검사한다. 제한 MCOS 표의 열 이름·행 수·유한값·시각 순서·시작/peak/종료 관계와
저장 clock 안의 peak 여부도 확인한다. 출력 폴더가 이미 있으면 덮어쓰지 않는다.

| 보존한 관측 | 수 |
|---|---:|
| 기록 묶음·범주·run block | 64 |
| 기록 묶음 / 사람 | 16 / 15 |
| ripple 사건 | 3,577 |
| 행동0–150초 안의 ripple peak | 3,345 |
| 발화 주석 전체 | 470 |
| Prompt / non-Prompt | 79 / 391 |

각 block은 원 기록 라벨, 사람, Face/Place, run, 해당 조건의 상대 초 시계를 가진다.
Block 간 시계를 하나의 연속 기록처럼 잇지 않는다. Ripple의 `str/peak/fin`과 중앙값
대비 dB amplitude, 원 MAT 행 번호를 그대로 보존한다. 행동은 원 주석 행 번호,
onset/offset, 원 항목 이름과 Prompt·범주·제시 목록 대응 표지를 보존하고 시각순으로
정렬한다. 같은 시각의 행도 버리지 않으며 원행 번호로 구별한다.

0–150초 밖 ripple232개와 범위를 넘는 발화 구간도 삭제·절단하지 않고 별도 표지로
남겼다. 원 MATLAB의−5초 여유 구간보다 앞선 이력을 알 수 있다고 가정하지 않는다.
저장된 숫자 clock 범위는 연속적이고 artifact 없는 원파형 획득의 증명이 아니다.

## 실제 실행과 독립 대조

보존 Python으로 한 번 실행했고, [독립 대조](../data/local/hippocampal-reinstatement/norman-event-observations-v1/independent_check.json)에서
입력66개 크기·SHA, 원 MAT64개 전체3,577행의4열 값, 행동470행의 원행 번호·
onset/offset·라벨이 정확히 보존됐음을 확인했다. 이를 확인하기 위해 모형을 다시
적합하거나 기존 판독 결과를 재평가하지 않았다.

[사건표](../data/local/hippocampal-reinstatement/norman-event-observations-v1/result/norman_event_observations.json)
SHA는 `f9c7ace8ab41e360781900a7bdb96588daf0b70f6fe09c41d496a65cdf867e3c`,
source SHA는 `84ef0dcf5de094c34166822c05a4ee23df9ccde7112c60702fbd4a2992417c7f`다.
소스·결과·manifest·독립 대조 소스/결과5파일1,354,895바이트를 원장에 등록했다.

## 해석과 다음 연결

이 사건표는 후향 분석의 입력이다. Ripple 검출이 미래 표본을 사용한다는 조건은
그대로이며, 공개 recall/search mask도 온라인 예측 특징으로 넣지 않았다.
Raw 행 번호는 출처를 찾는 ID이고 기억 내용의 색인이나 인과적 원인 ID가 아니다.
다음 발화 내용, ripple의 원인, 사건별 피질 내용은 이 표에서 추정하지 않았다.

[기존 MVPA의 경계](hippocampal_norman_observation_boundary_findings.md)를 해소하려면
추가 피질 수치와 이 사건표를 실제 생성 규칙으로 연결해야 한다.
[별도 피질 RTA 검사](hippocampal_norman_cortical_rta_findings.md)를 완료했지만 해당 파일도
이 연결의 원 사건 key를 제공하지 않았다. 전기 이력·관계 변화·계량·기억 검색의
전체 식을 평가할 준비가 모두 끝났다는 주장은 하지 않는다.
