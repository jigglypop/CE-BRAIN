<!-- 도메인: ce-brain-bio -->

# BA-CCEP 계보 경로 트리 — STAGE6 개봉 전 사전 등록

Status: `ROUTE_TREE_EXHAUSTED` (동결 2026-08-30 STAGE6 개봉 전 → 전 분기 판정 완료 2026-08-30)

이 문서는 인간 CCEP 계보의 후속 분기를 **STAGE6 결과를 보기 전에** 등록한다. 반례는 회귀점이며, 각 분기는 서로 다른 구조 seam·독립 falsifier·kill condition을 갖는다. 결과 확인 후 이 트리에 분기를 추가·수정하는 것은 outcome-informed로 금지한다 (새 관측 사실로 정당화되는 새 트리는 새 문서·새 동결로만).

## 확정된 지식 (지금까지의 생존 명제)

- **[검증 산출]** 거리 감쇠 E는 세 판본(DISC2R PASS_FINAL, Stage 3 선정, Stage 4 matched 재현)에서 held-out 예측 우위.
- **[산출]** 군수준 파셀 해부학은 평균 수준 채널(Stage 4)과 5-빈 모양 채널(Stage 5)에서 무정보. PERM 정렬 신호는 3회 연속 존재하나 마진의 수 %.
- **[산출: 설계 속성]** 5-빈 로그 에너지는 시간 모양을 분해하지 못한다 (Stage 5 해상도 반례).

## STAGE6 결과별 분기 (사전 선택 포함)

### 분기 A — `STAGE6_LATENCY_ANATOMY_SUPPORTED`
1. **A-1 (선택)**: 결과를 원장·논문 트랙으로 안정화하고, R-3(개인 dMRI 동반 corpus)로 독립 확증 계약. 군수준 지지의 상한은 개발 지위임을 유지.

### 분기 B — `STAGE6_DISTANCE_ONLY`
군수준 해부학은 수준·모양·지연 3채널 전부에서 거리로 환원 → **군수준(정적 규범) 해부학 모델 클래스의 no-go로 완결**. 다음은 해부학이 아니라 **방향성** seam으로 회귀한다:
1. **B-1 (선택): 지연 비대칭 판별** — DISC2R endpoint-graph-admission이 동결한 **73명 880 왕복(reciprocal) 방향쌍**에서, 같은 전극쌍의 $x_{\rm lat}(i\to j)$ 대 $x_{\rm lat}(j\to i)$ 비대칭을 시험한다. Stage 3에서 `DEFERRED_NOT_IDENTIFIABLE`이던 방향 기하(quasi-metric, BA-CG1의 실데이터 유사체)의 첫 실측. matched 쌍 설계라 거리·해부학이 완전 통제됨.
   - 사전 예측: 참가자 내 쌍별 비대칭 $\Delta_{ij}=x_{\rm lat}(i\to j)-x_{\rm lat}(j\to i)$의 재현성(반쪽 상관) 게이트와, 순열 대비 초과 분산.
   - falsifier: 쌍 라벨 순열(seed `20260833`, 499회)에서 재현성 통계가 95 분위 미만이면 방향 신호 없음 → `DIRECTION_NOT_IDENTIFIED`로 완결.
   - kill: 유한 왕복쌍 부족(<100 유효쌍) 시 `INSUFFICIENT_RECIPROCITY`.
2. B-2: 속도 estimand — 참가자별 $x_{\rm lat}$–거리 기울기(유효 전도 속도)의 나이 의존을 기술 보고(원 논문 축과 대조). 게이트 없는 기술 판본.
3. B-3: 개인 해부학 corpus (외부 소싱, 장기).

### 분기 C — `STAGE6_LATENCY_NOT_MEASURABLE`
1. **C-1 (선택)**: 관측량 재설계 1회 허용 — 에너지 절반 도달 대신 첫 문턱 통과 시각(사전 고정 $|w|\ge3$ 최초 시각, N1 관례)으로 새 계약. 재설계는 1회로 제한하며 재실패 시 지연 트랙 폐쇄.
2. C-2: 분기 B-1은 측정 가능성이 전제이므로 C에서는 열지 않는다.

### 분기 D — `STAGE6_CONTROL_FAILED` / `APPARATUS_STOP`
원인 분류(D→I→P→C→B→T) 후 대응하는 좁은 수리만. 과학 판정 없음.

## 분기 판정 기록 (설계 수정 아님 — 결과 로그)

- 2026-08-30 STAGE6: `LATENCY_NOT_MEASURABLE`(척도 C-분류) → C-1 이행.
- 2026-08-30 STAGE7(C-1): `DISTANCE_ONLY` — 측정 가능성 성립(+11.18%), 군수준 해부학 3채널 no-go 완결. C-2 제약 해제로 B-1 개방.
- 2026-08-30 B-1: **`INSUFFICIENT_RECIPROCITY`** — 양방향 문턱 통과 왕복쌍 33/440 (< 등록 kill 문턱 100). Δ 값 미개봉 상태의 유효성 집계만으로 판정. 방향 채널은 이 corpus에서 표본 부족으로 닫힘(반증 아님).
- 2026-08-30 B-2 (기술 판본, 게이트 없음): 통과 target 기준 참가자별 Theil–Sen 지연–거리 기울기 — ≥10 target 55명, 기울기 양수 40/55, 양수군 유효 전도속도 중앙 $1.83$ m/s (IQR $[1.15,3.55]$ — 피질-피질 유효 전파의 문헌 범위와 정합), 나이–기울기 Spearman $0.008$ (연관 없음, 기술 관찰). 산출 `ba-ccep-b2-descriptive.json`.
- 2026-08-30 B-3: **필수 외부 자료 부재** (sourcer 전수 검증) — "같은 환자 + trial 수준 CCEP + 개인 raw dMRI + 공개 다운로드"를 만족하는 corpus 없음. F-TRACT는 집계 지도만 공개(원문이 raw 배포 불가 명시), DABI는 신청제(내용 UNVERIFIED). **부분 예외**: OpenNeuro `ds007703`(n=2)이 SPES trial + 개인 트랙토그래피 파생물(.trk, 동공간 전극 좌표)을 공개 — n=2라 판별·확증 불가, 사례 수준 기술 pilot의 재개 조건으로만 보존.
- **트리 소진.** 재개 조건: (i) ds007703 사례 pilot(기술 지위 한정), (ii) DABI 신청 승인 + dMRI 포함 확인, (iii) 새 공개 corpus 출현. 이 셋 없이 CCEP 계보의 새 판본을 열지 않는다.

## 계보 최종 요약 (생존 지식)

- **[검증 산출]** Euclidean 거리 감쇠 E: 에너지(3개 판본 held-out)와 도달 시각(+11.18% of $L_T$) 모두에서 유일하게 생존한 경험 법칙.
- **[산출]** 문턱 지연 관측량은 측정 가능하며, 통과 연결의 유효 전도속도 중앙 $1.83$ m/s는 문헌 범위와 정합 (기술).
- **[산출: no-go]** 군수준 파셀 해부학은 크기·모양·시각 3채널 전부 거리로 환원 (정의역: 응답 실재 연결).
- **[산출: 표본 한계]** 방향 비대칭은 이 corpus에서 왕복 표본 부족(33쌍)으로 검정 불가 — 반증 아님.

## 공통 규율

- 각 분기의 실행은 새 `LOCKED_PRE_RESULT` 계약 문서로만 연다.
- 이 corpus에서 얻는 모든 판정은 registered reanalysis 개발 지위를 넘지 않는다.
- 연구 목표 축소·BLOCKED는 이 트리의 등록 분기가 소진된 뒤에만 허용된다.
