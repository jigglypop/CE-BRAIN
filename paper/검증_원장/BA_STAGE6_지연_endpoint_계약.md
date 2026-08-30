<!-- 도메인: ce-brain-bio -->

# BA-STAGE6 연구 계약 — 지연 관측량에서의 해부학 대 거리 판별 (R-2)

Status: `STAGE6_LATENCY_NOT_MEASURABLE / SCALE_MISMATCH_C_CLASSIFIED` (계약 동결·결과 기입 2026-08-30)

계보: BA-STAGE4 (`ANATOMY_NOT_IDENTIFIED`, 평균 수준 채널) → BA-STAGE5 (`SHAPE_NOT_IDENTIFIED`, 5-빈 해상도 반례) → **BA-STAGE6 (이 계약)** — Stage 5 §4.1이 승계한 유일 전진 경로 R-2의 이행.

## 1. 가설과 판본 지위

**[예측 후보]** 백질 전도의 물리는 응답 **도달 시각**에 쓰인다(선행: Silverstein 2020 — CCEP N1 지연 ∼ dMRI 경로 길이). 규범 경로길이(Domhof PL)는 응답 지연 예측에서 Euclidean 거리로 환원되지 않는 증분을 갖는가.

판본 지위: 같은 74명·592 source·5,920 trial의 **byte-locked registered reanalysis** — 새 정보는 관측량(지연)뿐이다. 통과해도 개발 지위이며, 개인 해부학·인과 전도 주장은 금지된다.

## 2. 관측량 정의 (결과 확인 전 동결)

DISC2R 동결 규약을 바이트 승계한다: 창 $[-1.0,+0.120]$ s, 기저선 $(-1.0,-0.1)$ s pooled MAD, bipolar(두 contact 차), ten-trial mean, 분석창 $W=[0.010,0.120]$ s (동결 5-빈의 합집합).

$$
w(\tau)=\frac{\overline{V}_{10}(\tau)}{\sigma_{\rm MAD}},\qquad
t_{\rm lat}=\min\Big\{t\in W:\ \sum_{\tau\in W,\,\tau\le t} w(\tau)^2 \ \ge\ \tfrac12\sum_{\tau\in W} w(\tau)^2\Big\},\qquad
x_{\rm lat}=t_{\rm lat}/0.050 .
$$

에너지 절반 도달 시각은 피크 선택 파라미터가 없는 강건 통계다. 원신호 재수령은 range 영수증의 잠긴 URL(versionId)·byte 범위·`If-Match` ETag로 하고, **수령 바이트의 SHA-256이 영수증의 `payload_sha256`과 일치해야만** 유효하다(불일치 = 그 source 전체 fail-closed abstain). 원전압은 비저장, $x_{\rm lat}$ 표만 남긴다.

## 3. 후보·대조·판정 (Stage 3~5 프로토콜의 스칼라 적용)

참가자 5-fold, source 내 centering, RMS 스케일, ridge $\lambda=1$, 4-anchor Huber offset, 참가자 평균 Huber loss($\delta=0.5$), 4,999 bootstrap, 마진 $0.005$/동률대역 $0.002$, Stage 4 연결 잠금의 $f_{\rm PL}$(군중앙 경로길이, mm)과 matched 탈락 그대로.

| 후보 | 특징 (공통: 나이) | 비음수 |
|---|---|---|
| T | — | |
| D | $+d\,r$ | $d\ge0$ (멀수록 늦음) |
| P | $+p\,f_{\rm PL}$ | $p\ge0$ |
| DP | $+d\,r+p\,f_{\rm PL}$ | 둘 다 |

대조: PERM($f_{\rm PL}$의 source 내 16-site 치환 499회, seed `20260832`, DP 재적합), RESID(거리 잔차화 $f_{\rm PL}$, 부호 검사). **측정 가능성 양성대조**: D가 T를 마진으로 이겨야 한다 — 전도 물리상 거리는 지연을 예측해야 하며, 실패 시 관측량 자체가 잡음이다.

- `STAGE6_LATENCY_ANATOMY_SUPPORTED`: D>T 성립, DP가 D를 마진으로 이김, PERM $\ge0.95$, RESID 부호 양.
- `STAGE6_DISTANCE_ONLY`: D>T 성립하나 DP가 D를 못 이김 — 지연에서도 규범 해부학은 거리로 환원. 이 계보(군수준 해부학)는 no-go로 완결.
- `STAGE6_LATENCY_NOT_MEASURABLE`: D가 T를 못 이김 — 이 endpoint 정의로는 지연이 관측 불가. R-2는 관측량 재설계 없이는 재시도 금지.
- `STAGE6_APPARATUS_STOP`: ETag/SHA 불일치 폭주(source 50% 초과), decode·마스크 실패.
- 유효성 규칙(동결): primary는 유한 $x_{\rm lat}$의 전 query. 기술 병기: 잠긴 5-빈 $z$ 최대 $\ge1.0$인 반응성 부분집합. seed·마진·창·규칙의 결과 후 변경은 STOP.

`CLAIM_CEILING`: registered reanalysis 개발 지위. 다음 승격은 개인 dMRI corpus(R-3)뿐.

## 4. 결과 (2026-08-30 실행, 동결 규칙 그대로)

**판정: `STAGE6_LATENCY_NOT_MEASURABLE`** — 양성대조 D>T의 개선 $+0.00192$(95% 하한 $+0.00111$, 54/74 양수)는 **통계적으로 실재하나** 동결 절대 마진 $0.005$ 미달.

- 추출: 592/592 source, 9,472/9,472 target 유한 $x_{\rm lat}$, 기권 0, 전 조각 ETag·`payload_sha256` 바이트 검증 통과 (영수증 `a5aad60555d42047…`, 원전압 비저장, 59분).
- 손실: T $0.13681$ / D $0.13489$ / P $0.13590$ / DP $0.13487$. DP>D $+0.00002$(CI 0 포함), P>D 음수, PERM 분위 $0.944$.
- **원인 분류 C (규약 척도 불일치)**: 지연 손실의 절대 규모(T $0.137$)가 에너지 채점(T $0.282$)의 절반 이하라, 에너지 척도에서 물려받은 절대 마진 $0.005$가 상대 기준으로 3배 가혹해졌다. 에너지 마진의 상대 강도는 $0.005/0.282=1.77\%$, 이번 D>T의 상대 개선은 $0.00192/0.13681=1.40\%$. 이 진단은 판정을 바꾸지 않으며(마진 사후 완화 금지), 경로트리 분기 C-1의 재설계 근거로만 쓴다.
- 결과 SHA-256 `50b11909c86ed2f0…`(runtime 123s). 러너 스크래치패드 `ba_stage6_extract.py`·`ba_stage6_screen.py`.

승계: 경로트리 분기 **C-1 (관측량 재설계 1회)** — BA-STAGE7 계약으로 이행. C-2 규정대로 방향 분기(B-1)는 측정 가능성 확보 전 열지 않는다.
