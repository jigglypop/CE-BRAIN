<!-- 도메인: ce-brain-bio -->

# BA-STAGE5 연구 계약 — CCEP 프로파일 모양 채널에서의 해부학 판별

Status: `STAGE5_SHAPE_NOT_IDENTIFIED / RESOLUTION_COUNTEREXAMPLE` (계약 동결·결과 기입 2026-08-30)

계보: BA-STAGE4 (`STAGE4_ANATOMY_NOT_IDENTIFIED` — 평균 수준 채널에서 해부학 무정보) → **BA-STAGE5 (이 계약)**.

## 1. 가설과 판본 지위

**[산출: 설계 속성]** Stage 3/4의 동결 특징 행렬에서 공간 항은 5개 시간 빈에 동일 복제되어(`np.repeat(delta, 5)`) 프로파일의 평행이동만 가능했다 — 해부학이 프로파일 **모양**($b$-의존)에 쓰여 있다면 구조적으로 보일 수 없었다.

**[예측 후보]** 백질 연결은 전도 시간을 바꾸므로(선행: Silverstein 2020, Parker 2018), 해부학 강도는 로그-에너지 프로파일의 시간 기울기와 상호작용한다. 시험: 빈×해부학 상호작용이 빈×거리 상호작용 대비 held-out 증분을 갖는가.

판본 지위: 같은 잠긴 endpoint 테이블(전부 기개봉)의 **registered reanalysis / OUTCOME_KNOWN** — 통과해도 개발 지위이며, Stage 4의 평균 수준 판정을 뒤집지 않는다(다른 채널의 질문이다).

## 2. 승계·후보 (Stage 3/4 프로토콜 그대로)

승계: 참가자 5-fold, ridge $\lambda=1$, 비음수 감쇠 하한(상호작용 계수는 부호 자유), source centering, RMS 스케일, 4-anchor Huber offset, 참가자 평균 Huber loss, 4,999 bootstrap, 마진 $0.005$/동률대역 $0.002$(단순 우선), Stage 4 연결 잠금(f_SC, SHA `fe20b06b…`)과 matched 탈락 그대로. **모든 후보는 동일 자유도 사다리로 용량을 대칭화한다.**

| 후보 | 공간·상호작용 항 | 자유도(공간) | 단순성 |
|---|---|---:|---|
| T | 없음 | 0 | 1 |
| E | $-a\,r$ | 1 | 2 |
| **Ex** | $-a\,r + e_1\, r\!\cdot\!\log x_b$ | 2 | 3 |
| **EAx** | $-a\,r + e_1\, r\!\cdot\!\log x_b + c_1 f_{\rm SC} + c_2\, f_{\rm SC}\!\cdot\!\log x_b$ | 4 | 4 |

판별 쌍은 **EAx 대 Ex**다(둘 다 모양 채널 보유 — 차이는 해부학뿐). Ex 대 E는 "모양 채널 자체의 가치"를 재는 보조 비교. 대조군: PERM(Stage 4와 동일한 source 내 f_SC 치환 499회, seed `20260831`, EAx로 재적합)과 RESID(거리 잔차화 f_SC의 EAx 변형, 부호 검사).

## 3. 판정 (결과 확인 전 고정)

- `STAGE5_SHAPE_ANATOMY_SUPPORTED`: EAx가 Ex를 마진으로 이기고, PERM 분위 $\ge0.95$, RESID 부호 양.
- `STAGE5_SHAPE_CHANNEL_ONLY`: Ex가 E를 이기지만 EAx는 Ex를 못 이김 — 모양 채널은 유효하나 해부학 무관(거리 공선 확정, §5-(ii) 반례 성립).
- `STAGE5_SHAPE_NOT_IDENTIFIED`: Ex가 E조차 못 이김 — 5-빈 해상도에서 모양 채널 자체가 무정보(§5-(i) 반례 성립).
- `STAGE5_CONTROL_FAILED` / `STAGE5_APPARATUS_STOP`.
- 마진·seed·후보·상호작용 기저($\log x_b$ 하나만, $x_b$ 상호작용 추가 금지)의 결과 후 변경은 STOP.

`CLAIM_CEILING`: registered reanalysis 개발 지위. 어떤 결과든 개인 해부학·인과 전도·리만 계량 주장 금지. 통과 시 승격 경로는 R-2(지연 endpoint 재추출) 또는 R-3(개인 dMRI corpus) 새 계약뿐.

## 4. 결과 (2026-08-30 실행, 동결 규칙 그대로)

**판정: `STAGE5_SHAPE_NOT_IDENTIFIED`** — §1의 반례 후보 (i)이 성립했다: 5-빈 로그-에너지 해상도에서는 **모양 채널 자체가 한계 정보를 갖지 않는다** (Ex>E: $+0.00029$, 95% 하한 $-0.00009$, 41/74; 마진 $0.005$ 미달). 따라서 EAx 대 Ex 판별($+0.00020$, CI가 0 포함)도 자동으로 마진 미달이다.

| 후보 | 평균 loss | 비고 |
|---|---|---|
| T / E | 0.29976 / 0.28213 | E>T $+0.01762$ (하한 $+0.01328$) — 기준 재재현 |
| Ex | 0.28184 | 모양 채널만: 미미 |
| EAx / RESID | 0.28164 | 전 후보 중 최저이나 마진 미달 |

기술 관찰(판정 불사용): **세 번째 연속으로** PERM 전부(499/499)에서 실측이 치환보다 낮았다(`eax_below_perm_fraction=1.0`). Stage 4·5의 해부학 정렬 신호는 일관되게 존재하되 항상 마진의 수 % 수준이다 — "신호는 있으나 이 관측량으로는 분해 불가"라는 해상도 반례 해석과 정합.

증거: 결과 SHA-256 `04cd3dc1440956e7d843e8a11b722600…`(runtime 172s), 러너 `examples/brain/ba_stage5_screen.py`, T/E 특징의 Stage 4 비트 동일성 검사 통과, 탈락 matched (source 584/592).

### 4.1 지위와 승계

- **[산출] 반례 (i) 확정**: 이 endpoint(5-빈 로그 에너지)는 시간 모양 정보를 분해하지 못한다. Stage 4의 "해부학 무정보" 판정은 이제 "이 관측량의 해상도 한계"라는 원인 분류를 얻었다.
- **승계: R-2가 유일한 전진 경로다** — ds004080 원신호를 재스트리밍해 target별 **지연/도달시각 endpoint**를 새 관측량으로 세우는 새 계약(DISC2R 파이프라인 재사용, 원전압 비저장 규율 유지). 예측은 사전 고정: $t_{\rm lat}\sim$ Domhof 경로길이/전도속도, 거리 대비 판별. R-3(개인 dMRI corpus)은 확증 전용으로 유지.
- 같은 테이블 위에서의 추가 상호작용 기저 탐색($x_b$, 고차 등)은 outcome-informed 낚시이므로 금지 (§3 STOP 조항).
