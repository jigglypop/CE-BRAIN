<!-- 도메인: ce-brain-bio -->

# BA-STAGE7 연구 계약 — 문턱 통과 지연 관측량 재설계 (경로트리 C-1, 재설계 1회분)

Status: `STAGE7_DISTANCE_ONLY / LATENCY_MEASURABLE / GROUP_ANATOMY_NO_GO_COMPLETE` (계약 동결·결과 기입 2026-08-30)

계보: BA-STAGE6 (`LATENCY_NOT_MEASURABLE / SCALE_MISMATCH_C`) → **BA-STAGE7 (이 계약)** — 경로트리 C-1이 허용한 관측량 재설계 1회의 이행. 이 판본이 다시 측정 불가면 지연 트랙은 폐쇄한다(트리 규정).

## 1. 재설계 내용 (결과 확인 전 동결)

STAGE6과의 차이는 정확히 두 가지다. 나머지(byte-locked 재수령, 창 $[0.010,0.120]$ s, bipolar·pooled-MAD $w$, 참가자 5-fold, source centering, 비음수 감쇠, Huber offset·loss, 4,999 bootstrap, PERM 499(seed `20260834`)·RESID, Stage 4 연결 잠금 $f_{\rm PL}$, matched 탈락)는 STAGE6 문면 그대로다.

**(a) 관측량**: 에너지 절반 도달 대신 **첫 문턱 통과 시각** (임상 N1 관례 정렬):

$$
x_{\rm thr}=t_{\rm thr}/0.050,\qquad
t_{\rm thr}=\min\{t\in[0.010,0.120]\,\mathrm{s}:\ |w(t)|\ge 3\}.
$$

문턱 $3$은 기저선 MAD 단위의 표준 관례이며 결과 확인 후 변경 금지. 통과가 없는 target은 **모든 후보에서 matched 제외**하고 수를 보고한다(응답 없는 target의 잡음 지연을 제거해 분산 구조를 키우는 것이 재설계의 요점이다).

**(b) 마진**: 절대 $0.005$ 대신 **상대 마진** — 개선이 T 기준선 손실의 $1.77\%$ 이상:

$$
\text{beats}(a,b)\iff \frac{\Delta_{ab}}{\bar L_T}\ \ge\ 0.0177\ \text{ 그리고 } \ \mathrm{lo95}(\Delta_{ab})>0 .
$$

$1.77\%=0.005/0.28213$은 Stage 3부터 동결된 상수 쌍(에너지 마진과 그 시점 E 손실 척도)에서 유도했고, **오늘의 지연 수치에서 유도하지 않았다**. 동률대역도 같은 비로 $0.71\%$($=0.002/0.28213$).

**부가 산출(선언)**: 추출 시 각 방향 target의 홀/짝 교차 반쪽(event 정렬 후 0,2,4,6,8 대 1,3,5,7,9) $x_{\rm thr}$도 함께 계산해 저장한다. 이는 이 판본의 게이트에 쓰지 않으며, 측정 가능성 확보 시 B-1(방향 비대칭)의 재현성 게이트 입력으로만 쓴다.

### 1.1 SMOKE_AMENDMENT (전 corpus 개봉 전, 1-source smoke 근거)

1-source 장치 smoke(첫 정렬 source, 16 target 중 3 통과)에서 anchor 4개 전원 통과 요구가 offset 기구를 구조적으로 죽임이 드러났다. 실데이터 규약의 smoke-수리 조항(실패에 필요한 부분만, 1회)에 따라 **결과 개봉 전에** 다음만 수리한다: source별 offset은 **통과한 anchor $\ge2$개**의 Huber location으로 추정하고, 채점은 **통과한 query $\ge3$개**를 요구한다(미달 source는 전 후보 matched 탈락, 수 보고). 문턱·창·마진·후보는 불변. 이 수정은 전 corpus의 어떤 값도 보기 전에 이루어졌다.

## 2. 판정 (STAGE6 코드 체계 승계)

- `STAGE7_LATENCY_ANATOMY_SUPPORTED`: D>T(상대 마진), DP>D(상대 마진), PERM $\ge0.95$, RESID 부호 양.
- `STAGE7_DISTANCE_ONLY`: D>T 성립, DP>D 실패 — 군수준 해부학의 지연 채널 no-go 완결, **B-1(방향 비대칭)로 회귀** (측정 가능성이 확보되었으므로 트리 C-2 제약 해제).
- `STAGE7_LATENCY_TRACK_CLOSED`: D>T 실패 — 재설계 소진, 지연 트랙 폐쇄. 남은 등록 분기는 B-2(기술 판본)·B-3(외부 corpus)뿐.
- `STAGE7_CONTROL_FAILED` / `APPARATUS_STOP`: 대응 좁은 수리만.
- 문턱·창·마진·seed의 결과 후 변경은 STOP.

`CLAIM_CEILING`: registered reanalysis 개발 지위 유지.

## 3. 결과 (2026-08-30 실행, 동결 규칙 그대로)

**판정: `STAGE7_DISTANCE_ONLY`.**

- 추출: 592/592 source 바이트 검증 통과, 통과 target 1,390/9,472 (14.7%), 영수증 SHA `ff6687fa114e3365…`, 원전압 비저장(58분).
- 유지 코호트(SMOKE_AMENDMENT 적용): source 56, 참가자 30 (탈락: 통과 anchor<2 506, query<3 22, 연결 잠금 8).
- **측정 가능성 성립**: D>T $+0.02116$ = **$+11.18\%$ of $L_T$** (요구 $1.77\%$, 하한 $+0.00404$, 20/30). STAGE6의 C-분류(척도 불일치·관측량 설계) 진단이 확증됨.
- **해부학 판별 음성**: DP>D $-0.00102$ ($-0.54\%$), RESID>D $-0.55\%$, P>T $+1.93\%$(하한 음수), PERM 분위 $0.164$ — 정렬 신호 부재.
- 결과 SHA `7edb01df70c96abf…`(runtime 확인), 러너 스크래치패드 `ba_stage7_extract.py`·`ba_stage7_screen.py`.

### 3.1 계보 결론과 경계

**[산출: 모델 클래스 no-go 완결]** 군수준(정적 규범, Destrieux-150 파셀) 해부학 연결은 이 corpus의 관측 커널에서 **크기(Stage 4)·시간 모양(Stage 5)·도달 시각(Stage 7)** 세 채널 전부 Euclidean 거리로 환원된다. 경계: (i) 판정 정의역은 문턱 통과(응답 실재) 연결, 코호트 30/74명; (ii) 개인 해부학·세밀 해상도는 미반증(재개 조건 유지); (iii) registered reanalysis 개발 지위.

승계: 측정 가능성이 확보되었으므로 경로트리 **B-1(방향 비대칭)** 개방 — BA-STAGE8 계약으로 이행. 홀/짝 반쪽 $x_{\rm thr}$는 이 판본에서 게이트에 쓰지 않았고 선언대로 B-1 입력으로만 넘긴다.
